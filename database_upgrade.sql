-- 資料庫升級腳本：加入AI標籤支援

-- 1. 為news_articles表加入tags欄位
ALTER TABLE news_articles 
ADD COLUMN IF NOT EXISTS tags TEXT[] DEFAULT '{}';

-- 2. 為subscriptions表加入AI轉換後的標籤
ALTER TABLE subscriptions 
ADD COLUMN IF NOT EXISTS subscribed_tags TEXT[] DEFAULT '{}';

-- 3. 為subscriptions表加入原始關鍵字記錄（用於後續改進）
ALTER TABLE subscriptions 
ADD COLUMN IF NOT EXISTS original_keywords TEXT[] DEFAULT '{}';

-- 4. 為subscriptions表加入時間戳欄位（關鍵字同步用）
ALTER TABLE subscriptions 
ADD COLUMN IF NOT EXISTS keywords_updated_at TIMESTAMP DEFAULT NOW();

ALTER TABLE subscriptions 
ADD COLUMN IF NOT EXISTS tags_updated_at TIMESTAMP DEFAULT NOW();

-- 5. 建立標籤使用統計表（用於分析和改進）
CREATE TABLE IF NOT EXISTS tag_usage_stats (
    tag TEXT PRIMARY KEY,
    usage_count INTEGER DEFAULT 0,
    user_subscription_count INTEGER DEFAULT 0,
    last_used_at TIMESTAMP DEFAULT NOW()
);

-- 6. 建立關鍵字轉換記錄表（用於AI學習改進）
CREATE TABLE IF NOT EXISTS keyword_conversion_log (
    id SERIAL PRIMARY KEY,
    user_id UUID,
    original_keyword TEXT,
    converted_tag TEXT,
    confidence DECIMAL(3,2),
    created_at TIMESTAMP DEFAULT NOW(),
    user_modified BOOLEAN DEFAULT FALSE
);

-- 7. 為查詢優化建立索引
CREATE INDEX IF NOT EXISTS idx_news_articles_tags ON news_articles USING GIN(tags);
CREATE INDEX IF NOT EXISTS idx_subscriptions_tags ON subscriptions USING GIN(subscribed_tags);
CREATE INDEX IF NOT EXISTS idx_news_articles_published_at ON news_articles(published_at);

-- 8. 更新現有數據（如果有的話）
-- 將現有keywords轉換為tags（後續由AI處理）
UPDATE subscriptions 
SET original_keywords = keywords 
WHERE original_keywords = '{}' AND keywords IS NOT NULL;