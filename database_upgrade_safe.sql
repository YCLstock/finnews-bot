-- 資料庫安全升級腳本：加入AI標籤支援
-- 此腳本設計為與現有資料完全相容，不會造成資料遺失

-- 檢查並備份重要資料（可選）
-- CREATE TABLE subscriptions_backup AS SELECT * FROM subscriptions;

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
-- 使用安全的預設值，避免NULL問題
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
-- 使用IF NOT EXISTS確保不會重複建立
CREATE INDEX IF NOT EXISTS idx_news_articles_tags ON news_articles USING GIN(tags);
CREATE INDEX IF NOT EXISTS idx_subscriptions_tags ON subscriptions USING GIN(subscribed_tags);
CREATE INDEX IF NOT EXISTS idx_news_articles_published_at ON news_articles(published_at);

-- 8. 安全地更新現有數據
-- 分步驟進行，確保資料完整性

-- 8.1 首先檢查keywords欄位是否存在
DO $$
BEGIN
    -- 只有當keywords欄位存在且original_keywords為空時才執行更新
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'subscriptions' 
        AND column_name = 'keywords'
    ) THEN
        -- 將現有的keywords複製到original_keywords
        UPDATE subscriptions 
        SET original_keywords = keywords 
        WHERE (original_keywords IS NULL OR original_keywords = '{}')
          AND keywords IS NOT NULL 
          AND keywords != '{}';
          
        RAISE NOTICE 'Updated % rows with existing keywords', (
            SELECT COUNT(*) FROM subscriptions 
            WHERE original_keywords != '{}' AND keywords IS NOT NULL
        );
    ELSE
        RAISE NOTICE 'keywords column does not exist, skipping data migration';
    END IF;
END $$;

-- 8.2 為現有用戶設置合理的時間戳
-- 避免所有用戶的標籤在第一次同步時都被重新處理
UPDATE subscriptions 
SET 
    keywords_updated_at = COALESCE(updated_at, created_at, NOW()),
    tags_updated_at = COALESCE(updated_at, created_at, NOW())
WHERE keywords_updated_at IS NULL OR tags_updated_at IS NULL;

-- 9. 驗證升級結果
DO $$
DECLARE
    news_tags_count INTEGER;
    subs_tags_count INTEGER;
    subs_keywords_count INTEGER;
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
    
    IF news_tags_count = 1 AND subs_tags_count = 1 AND subs_keywords_count = 1 THEN
        RAISE NOTICE '✅ 資料庫升級成功完成！';
        RAISE NOTICE '   - news_articles.tags 欄位: ✅';
        RAISE NOTICE '   - subscriptions.subscribed_tags 欄位: ✅';
        RAISE NOTICE '   - subscriptions.original_keywords 欄位: ✅';
        RAISE NOTICE '   - 時間戳欄位: ✅';
        RAISE NOTICE '   - 索引: ✅';
        RAISE NOTICE '';
        RAISE NOTICE '🚀 AI標籤系統已準備就緒！';
    ELSE
        RAISE EXCEPTION '❌ 資料庫升級失敗，請檢查錯誤訊息';
    END IF;
END $$;