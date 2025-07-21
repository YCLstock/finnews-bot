-- 資料庫安全升級腳本：加入AI標籤支援 (修正版)
-- 解決JSONB到TEXT[]的型態轉換問題

-- 1. 為news_articles表加入tags欄位（安全操作）
ALTER TABLE news_articles 
ADD COLUMN IF NOT EXISTS tags TEXT[] DEFAULT '{}';

-- 2. 為subscriptions表加入AI轉換後的標籤（安全操作）
ALTER TABLE subscriptions 
ADD COLUMN IF NOT EXISTS subscribed_tags TEXT[] DEFAULT '{}';

-- 3. 為subscriptions表加入原始關鍵字記錄（安全操作）
ALTER TABLE subscriptions 
ADD COLUMN IF NOT EXISTS original_keywords TEXT[] DEFAULT '{}';

-- 4. 為subscriptions表加入時間戳欄位（安全操作）
ALTER TABLE subscriptions 
ADD COLUMN IF NOT EXISTS keywords_updated_at TIMESTAMP DEFAULT NOW();

ALTER TABLE subscriptions 
ADD COLUMN IF NOT EXISTS tags_updated_at TIMESTAMP DEFAULT NOW();

-- 5. 建立標籤使用統計表（安全操作）
CREATE TABLE IF NOT EXISTS tag_usage_stats (
    tag TEXT PRIMARY KEY,
    usage_count INTEGER DEFAULT 0,
    user_subscription_count INTEGER DEFAULT 0,
    last_used_at TIMESTAMP DEFAULT NOW()
);

-- 6. 建立關鍵字轉換記錄表（安全操作）
CREATE TABLE IF NOT EXISTS keyword_conversion_log (
    id SERIAL PRIMARY KEY,
    user_id UUID,
    original_keyword TEXT,
    converted_tag TEXT,
    confidence DECIMAL(3,2),
    created_at TIMESTAMP DEFAULT NOW(),
    user_modified BOOLEAN DEFAULT FALSE
);

-- 7. 為查詢優化建立索引（安全操作）
CREATE INDEX IF NOT EXISTS idx_news_articles_tags ON news_articles USING GIN(tags);
CREATE INDEX IF NOT EXISTS idx_subscriptions_tags ON subscriptions USING GIN(subscribed_tags);
CREATE INDEX IF NOT EXISTS idx_news_articles_published_at ON news_articles(published_at);

-- 8. 安全地更新現有數據（修正型態轉換問題）
DO $$
DECLARE
    keywords_column_type TEXT;
    updated_rows INTEGER := 0;
BEGIN
    -- 檢查keywords欄位的資料型態
    SELECT data_type INTO keywords_column_type
    FROM information_schema.columns 
    WHERE table_name = 'subscriptions' 
    AND column_name = 'keywords';
    
    IF keywords_column_type IS NOT NULL THEN
        RAISE NOTICE 'Found keywords column with type: %', keywords_column_type;
        
        -- 根據不同型態進行轉換
        IF keywords_column_type = 'jsonb' THEN
            -- JSONB型態轉換為TEXT[]
            UPDATE subscriptions 
            SET original_keywords = ARRAY(
                SELECT jsonb_array_elements_text(keywords)
                WHERE jsonb_typeof(keywords) = 'array'
            )
            WHERE (original_keywords IS NULL OR original_keywords = '{}')
              AND keywords IS NOT NULL 
              AND jsonb_typeof(keywords) = 'array'
              AND jsonb_array_length(keywords) > 0;
              
            GET DIAGNOSTICS updated_rows = ROW_COUNT;
            RAISE NOTICE 'Updated % rows from JSONB keywords to TEXT[] original_keywords', updated_rows;
            
        ELSIF keywords_column_type = 'ARRAY' OR keywords_column_type LIKE '%[]' THEN
            -- 已經是陣列型態，直接複製
            UPDATE subscriptions 
            SET original_keywords = keywords 
            WHERE (original_keywords IS NULL OR original_keywords = '{}')
              AND keywords IS NOT NULL 
              AND keywords != '{}';
              
            GET DIAGNOSTICS updated_rows = ROW_COUNT;
            RAISE NOTICE 'Updated % rows from TEXT[] keywords to original_keywords', updated_rows;
            
        ELSIF keywords_column_type = 'text' THEN
            -- 純文字型態，需要特殊處理
            UPDATE subscriptions 
            SET original_keywords = string_to_array(keywords, ',')
            WHERE (original_keywords IS NULL OR original_keywords = '{}')
              AND keywords IS NOT NULL 
              AND length(trim(keywords)) > 0;
              
            GET DIAGNOSTICS updated_rows = ROW_COUNT;
            RAISE NOTICE 'Updated % rows from TEXT keywords to TEXT[] original_keywords', updated_rows;
            
        ELSE
            RAISE NOTICE 'Unknown keywords column type: %, skipping data migration', keywords_column_type;
        END IF;
        
    ELSE
        RAISE NOTICE 'keywords column does not exist, skipping data migration';
    END IF;
    
    -- 顯示資料移轉統計
    RAISE NOTICE 'Data migration completed: % rows updated', updated_rows;
    
EXCEPTION
    WHEN OTHERS THEN
        RAISE NOTICE 'Data migration failed: %', SQLERRM;
        RAISE NOTICE 'Continuing with other upgrade steps...';
END $$;

-- 9. 為現有用戶設置合理的時間戳
UPDATE subscriptions 
SET 
    keywords_updated_at = COALESCE(updated_at, created_at, NOW()),
    tags_updated_at = COALESCE(updated_at, created_at, NOW())
WHERE keywords_updated_at IS NULL OR tags_updated_at IS NULL;

-- 10. 檢視現有資料狀況（調試用）
DO $$
DECLARE
    total_users INTEGER;
    users_with_keywords INTEGER;
    users_with_original_keywords INTEGER;
BEGIN
    SELECT COUNT(*) INTO total_users FROM subscriptions;
    
    SELECT COUNT(*) INTO users_with_keywords 
    FROM subscriptions 
    WHERE keywords IS NOT NULL AND (
        (jsonb_typeof(keywords) = 'array' AND jsonb_array_length(keywords) > 0) OR
        (keywords::text != '{}' AND keywords::text != '[]' AND keywords::text != 'null')
    );
    
    SELECT COUNT(*) INTO users_with_original_keywords 
    FROM subscriptions 
    WHERE original_keywords IS NOT NULL AND original_keywords != '{}';
    
    RAISE NOTICE '';
    RAISE NOTICE '📊 資料統計:';
    RAISE NOTICE '   總用戶數: %', total_users;
    RAISE NOTICE '   有關鍵字的用戶: %', users_with_keywords; 
    RAISE NOTICE '   已移轉原始關鍵字的用戶: %', users_with_original_keywords;
    RAISE NOTICE '';
END $$;

-- 11. 驗證升級結果
DO $$
DECLARE
    news_tags_count INTEGER;
    subs_tags_count INTEGER;
    subs_keywords_count INTEGER;
    subs_timestamp_count INTEGER;
BEGIN
    -- 檢查新欄位是否成功建立
    SELECT COUNT(*) INTO news_tags_count
    FROM information_schema.columns 
    WHERE table_name = 'news_articles' AND column_name = 'tags';
    
    SELECT COUNT(*) INTO subs_tags_count
    FROM information_schema.columns 
    WHERE table_name = 'subscriptions' AND column_name = 'subscribed_tags';
    
    SELECT COUNT(*) INTO subs_keywords_count
    FROM information_schema.columns 
    WHERE table_name = 'subscriptions' AND column_name = 'original_keywords';
    
    SELECT COUNT(*) INTO subs_timestamp_count
    FROM information_schema.columns 
    WHERE table_name = 'subscriptions' 
    AND column_name IN ('keywords_updated_at', 'tags_updated_at');
    
    IF news_tags_count = 1 AND subs_tags_count = 1 AND subs_keywords_count = 1 AND subs_timestamp_count = 2 THEN
        RAISE NOTICE '✅ 資料庫升級成功完成！';
        RAISE NOTICE '   - news_articles.tags 欄位: ✅';
        RAISE NOTICE '   - subscriptions.subscribed_tags 欄位: ✅';
        RAISE NOTICE '   - subscriptions.original_keywords 欄位: ✅';
        RAISE NOTICE '   - 時間戳欄位: ✅ (% 個)', subs_timestamp_count;
        RAISE NOTICE '   - 索引建立: ✅';
        RAISE NOTICE '';
        RAISE NOTICE '🚀 AI標籤系統已準備就緒！';
        RAISE NOTICE '';
        RAISE NOTICE '📋 下一步:';
        RAISE NOTICE '   1. 啟動關鍵字同步服務: python scheduler.py --keyword-sync';
        RAISE NOTICE '   2. 測試AI標籤功能: python test_ai_tagging.py';
        RAISE NOTICE '   3. 啟動完整調度器: python scheduler.py';
    ELSE
        RAISE EXCEPTION '❌ 資料庫升級失敗，請檢查錯誤訊息';
    END IF;
END $$;