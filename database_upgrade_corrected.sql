-- 資料庫安全升級腳本：加入AI標籤支援 (錯誤修正版)
-- 修正變數名稱衝突問題

-- 1. 為news_articles表加入tags欄位
ALTER TABLE public.news_articles 
ADD COLUMN IF NOT EXISTS tags TEXT[] DEFAULT '{}';

-- 2. 為subscriptions表加入AI轉換後的標籤
ALTER TABLE public.subscriptions 
ADD COLUMN IF NOT EXISTS subscribed_tags TEXT[] DEFAULT '{}';

-- 3. 為subscriptions表加入原始關鍵字記錄
ALTER TABLE public.subscriptions 
ADD COLUMN IF NOT EXISTS original_keywords TEXT[] DEFAULT '{}';

-- 4. 為subscriptions表加入時間戳欄位（用於AI標籤同步）
ALTER TABLE public.subscriptions 
ADD COLUMN IF NOT EXISTS keywords_updated_at timestamp with time zone DEFAULT now();

ALTER TABLE public.subscriptions 
ADD COLUMN IF NOT EXISTS tags_updated_at timestamp with time zone DEFAULT now();

-- 5. 加入推送頻率類型欄位（替代push_frequency_hours）
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'subscriptions' AND column_name = 'push_frequency_type'
    ) THEN
        -- 創建enum類型（如果不存在）
        DO $enum$
        BEGIN
            CREATE TYPE push_frequency_type AS ENUM ('daily', 'twice', 'thrice');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $enum$;
        
        -- 加入新欄位
        ALTER TABLE public.subscriptions 
        ADD COLUMN push_frequency_type push_frequency_type DEFAULT 'daily';
        
        -- 根據現有push_frequency_hours轉換
        UPDATE public.subscriptions 
        SET push_frequency_type = CASE 
            WHEN push_frequency_hours <= 8 THEN 'thrice'
            WHEN push_frequency_hours <= 12 THEN 'twice' 
            ELSE 'daily'
        END;
        
        RAISE NOTICE 'Added push_frequency_type column and migrated from push_frequency_hours';
    ELSE
        RAISE NOTICE 'push_frequency_type column already exists';
    END IF;
END $$;

-- 6. 加入推送窗口追蹤欄位
ALTER TABLE public.subscriptions 
ADD COLUMN IF NOT EXISTS last_push_window TEXT;

-- 7. 建立標籤使用統計表
CREATE TABLE IF NOT EXISTS public.tag_usage_stats (
    tag TEXT PRIMARY KEY,
    usage_count INTEGER DEFAULT 0,
    user_subscription_count INTEGER DEFAULT 0,
    last_used_at timestamp with time zone DEFAULT now()
);

-- 8. 建立關鍵字轉換記錄表
CREATE TABLE IF NOT EXISTS public.keyword_conversion_log (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id uuid,
    original_keyword TEXT,
    converted_tag TEXT,
    confidence DECIMAL(3,2),
    created_at timestamp with time zone DEFAULT now(),
    user_modified BOOLEAN DEFAULT FALSE
);

-- 9. 為查詢優化建立索引
CREATE INDEX IF NOT EXISTS idx_news_articles_tags ON public.news_articles USING GIN(tags);
CREATE INDEX IF NOT EXISTS idx_subscriptions_tags ON public.subscriptions USING GIN(subscribed_tags);
CREATE INDEX IF NOT EXISTS idx_news_articles_published_at ON public.news_articles(published_at);
CREATE INDEX IF NOT EXISTS idx_subscriptions_frequency_type ON public.subscriptions(push_frequency_type);

-- 10. 安全地轉換現有JSONB keywords到TEXT[] original_keywords
DO $$
DECLARE
    updated_rows INTEGER := 0;
BEGIN
    -- 檢查keywords欄位是否存在且為JSONB型態
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'subscriptions' 
        AND column_name = 'keywords'
        AND data_type = 'jsonb'
    ) THEN
        RAISE NOTICE 'Converting JSONB keywords to TEXT[] original_keywords...';
        
        -- 轉換JSONB陣列到TEXT陣列
        UPDATE public.subscriptions 
        SET original_keywords = ARRAY(
            SELECT jsonb_array_elements_text(keywords)
        )
        WHERE (original_keywords IS NULL OR original_keywords = '{}')
          AND keywords IS NOT NULL 
          AND jsonb_typeof(keywords) = 'array'
          AND jsonb_array_length(keywords) > 0;
          
        GET DIAGNOSTICS updated_rows = ROW_COUNT;
        RAISE NOTICE 'Successfully converted % rows from JSONB to TEXT[]', updated_rows;
        
    ELSE
        RAISE NOTICE 'keywords column not found or not JSONB type, skipping conversion';
    END IF;
    
EXCEPTION
    WHEN OTHERS THEN
        RAISE NOTICE 'Keywords conversion failed: %, continuing...', SQLERRM;
END $$;

-- 11. 為現有用戶設置合理的時間戳
UPDATE public.subscriptions 
SET 
    keywords_updated_at = COALESCE(now()),
    tags_updated_at = COALESCE(now())
WHERE keywords_updated_at IS NULL OR tags_updated_at IS NULL;

-- 12. 顯示升級統計資訊
DO $$
DECLARE
    total_users INTEGER;
    users_with_keywords INTEGER;
    users_with_original_keywords INTEGER;
    news_articles_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO total_users FROM public.subscriptions;
    SELECT COUNT(*) INTO news_articles_count FROM public.news_articles;
    
    SELECT COUNT(*) INTO users_with_keywords 
    FROM public.subscriptions 
    WHERE keywords IS NOT NULL AND jsonb_array_length(keywords) > 0;
    
    SELECT COUNT(*) INTO users_with_original_keywords 
    FROM public.subscriptions 
    WHERE original_keywords IS NOT NULL AND array_length(original_keywords, 1) > 0;
    
    RAISE NOTICE '';
    RAISE NOTICE '📊 資料庫升級統計:';
    RAISE NOTICE '   訂閱用戶總數: %', total_users;
    RAISE NOTICE '   新聞文章總數: %', news_articles_count;
    RAISE NOTICE '   有關鍵字的用戶: %', users_with_keywords; 
    RAISE NOTICE '   已轉換原始關鍵字的用戶: %', users_with_original_keywords;
    RAISE NOTICE '';
END $$;

-- 13. 最終驗證（修正變數名稱衝突）
DO $$
DECLARE
    required_columns TEXT[] := ARRAY[
        'news_articles.tags',
        'subscriptions.subscribed_tags', 
        'subscriptions.original_keywords',
        'subscriptions.keywords_updated_at',
        'subscriptions.tags_updated_at'
    ];
    col TEXT;
    missing_columns TEXT[] := '{}';
    target_table_name TEXT;  -- 重新命名變數
    target_column_name TEXT; -- 重新命名變數
    found BOOLEAN;
BEGIN
    -- 檢查所有必要欄位
    FOREACH col IN ARRAY required_columns LOOP
        target_table_name := split_part(col, '.', 1);
        target_column_name := split_part(col, '.', 2);
        
        SELECT EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_schema = 'public'
            AND information_schema.columns.table_name = target_table_name  -- 明確指定表格來源
            AND information_schema.columns.column_name = target_column_name -- 明確指定表格來源
        ) INTO found;
        
        IF NOT found THEN
            missing_columns := array_append(missing_columns, col);
        END IF;
    END LOOP;
    
    IF array_length(missing_columns, 1) > 0 THEN
        RAISE EXCEPTION '❌ 升級失敗！缺少欄位: %', array_to_string(missing_columns, ', ');
    ELSE
        RAISE NOTICE '✅ 資料庫升級成功完成！';
        RAISE NOTICE '';
        RAISE NOTICE '🎯 新功能已啟用:';
        RAISE NOTICE '   ✅ AI標籤系統 (使用TEXT[]陣列型態)';
        RAISE NOTICE '   ✅ 關鍵字同步服務';
        RAISE NOTICE '   ✅ 智能推送頻率';
        RAISE NOTICE '   ✅ 批量處理優化';
        RAISE NOTICE '   ✅ GIN索引查詢優化';
        RAISE NOTICE '';
        RAISE NOTICE '🚀 下一步執行指令:';
        RAISE NOTICE '   測試關鍵字同步: python scheduler.py --keyword-sync';
        RAISE NOTICE '   測試AI標籤功能: python test_ai_tagging.py';
        RAISE NOTICE '   啟動完整系統: python scheduler.py';
        RAISE NOTICE '';
        RAISE NOTICE '💡 TEXT[]陣列優勢:';
        RAISE NOTICE '   - 查詢效能更佳 (GIN索引)';
        RAISE NOTICE '   - 陣列操作符支援: @>, &&, ||';
        RAISE NOTICE '   - 記憶體佔用更少';
        RAISE NOTICE '';
        RAISE NOTICE '🎉 FinNews-Bot AI升級完成！';
    END IF;
END $$;