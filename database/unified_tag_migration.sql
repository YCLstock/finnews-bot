-- FindyAI 統一標籤管理系統 - 數據遷移 SQL
-- 版本: 1.0
-- 日期: 2025-08-13
-- 說明: 將硬編碼標籤同步到Supabase資料庫，建立統一標籤管理系統

-- =====================================================
-- 第一階段: 基礎標籤數據遷移
-- =====================================================

-- 插入主要標籤 (來自爬蟲系統的硬編碼標籤)
INSERT INTO public.tags (tag_code, tag_name_zh, tag_name_en, priority, is_active) 
VALUES 
    -- 科技公司 (高優先級)
    ('APPLE', '蘋果公司', 'Apple Inc.', 10, true),
    ('TSMC', '台積電', 'Taiwan Semiconductor', 10, true),
    ('TESLA', '特斯拉', 'Tesla Inc.', 10, true),
    
    -- 科技產業
    ('AI_TECH', 'AI科技', 'AI Technology', 15, true),
    ('TECH', '科技產業', 'Technology Sector', 12, true),
    ('ELECTRIC_VEHICLES', '電動車', 'Electric Vehicles', 15, true),
    
    -- 金融市場 (核心優先級)
    ('STOCK_MARKET', '股票市場', 'Stock Market', 5, true),
    ('ECONOMIES', '經濟指標', 'Economic Indicators', 5, true),
    ('FEDERAL_RESERVE', '聯準會', 'Federal Reserve', 6, true),
    ('EARNINGS', '企業財報', 'Corporate Earnings', 8, true),
    
    -- 投資標的
    ('CRYPTO', '加密貨幣', 'Cryptocurrency', 20, true),
    ('BONDS', '債券市場', 'Bond Market', 19, true),
    ('COMMODITIES', '商品期貨', 'Commodities', 17, true),
    
    -- 產業分類
    ('HOUSING', '房地產', 'Real Estate', 18, true),
    ('ENERGY', '能源產業', 'Energy Sector', 16, true),
    ('HEALTHCARE', '醫療保健', 'Healthcare', 20, true),
    ('FINANCE', '金融業', 'Financial Services', 12, true),
    
    -- 政策與貿易
    ('TARIFFS', '關稅貿易', 'Tariffs & Trade', 14, true),
    ('TRADE', '國際貿易', 'International Trade', 14, true),
    
    -- 通用分類 (低優先級)
    ('LATEST', '最新消息', 'Latest News', 30, true)
ON CONFLICT (tag_code) DO UPDATE SET
    tag_name_zh = EXCLUDED.tag_name_zh,
    tag_name_en = EXCLUDED.tag_name_en,
    priority = EXCLUDED.priority,
    updated_at = CURRENT_TIMESTAMP;

-- =====================================================
-- 第二階段: 關鍵字映射數據遷移
-- =====================================================

-- 插入基礎關鍵字映射
WITH tag_mappings AS (
  SELECT id, tag_code FROM public.tags WHERE is_active = true
)
INSERT INTO public.keyword_mappings (tag_id, keyword, language, mapping_type, confidence, match_method, is_active)
SELECT t.id, kw.keyword, kw.language, 'system_migration', kw.confidence, 'exact', true
FROM tag_mappings t
CROSS JOIN (
    -- 蘋果公司相關
    SELECT 'apple' as keyword, 'en' as language, 1.0 as confidence WHERE tag_code = 'APPLE'
    UNION ALL SELECT 'aapl', 'en', 1.0 WHERE tag_code = 'APPLE'
    UNION ALL SELECT '蘋果', 'zh', 1.0 WHERE tag_code = 'APPLE'
    UNION ALL SELECT '庫克', 'zh', 0.8 WHERE tag_code = 'APPLE'
    UNION ALL SELECT 'iphone', 'en', 0.9 WHERE tag_code = 'APPLE'
    UNION ALL SELECT 'mac', 'en', 0.7 WHERE tag_code = 'APPLE'
    
    -- 台積電相關
    UNION ALL SELECT 'tsmc', 'en', 1.0 WHERE tag_code = 'TSMC'
    UNION ALL SELECT 'taiwan semiconductor', 'en', 1.0 WHERE tag_code = 'TSMC'
    UNION ALL SELECT '台積電', 'zh', 1.0 WHERE tag_code = 'TSMC'
    UNION ALL SELECT '晶圓', 'zh', 0.8 WHERE tag_code = 'TSMC'
    
    -- 特斯拉相關
    UNION ALL SELECT 'tesla', 'en', 1.0 WHERE tag_code = 'TESLA'
    UNION ALL SELECT 'tsla', 'en', 1.0 WHERE tag_code = 'TESLA'
    UNION ALL SELECT '特斯拉', 'zh', 1.0 WHERE tag_code = 'TESLA'
    UNION ALL SELECT '馬斯克', 'zh', 0.9 WHERE tag_code = 'TESLA'
    UNION ALL SELECT 'elon musk', 'en', 0.9 WHERE tag_code = 'TESLA'
    
    -- AI科技相關
    UNION ALL SELECT 'ai', 'en', 1.0 WHERE tag_code = 'AI_TECH'
    UNION ALL SELECT 'artificial intelligence', 'en', 1.0 WHERE tag_code = 'AI_TECH'
    UNION ALL SELECT '人工智慧', 'zh', 1.0 WHERE tag_code = 'AI_TECH'
    UNION ALL SELECT 'machine learning', 'en', 0.9 WHERE tag_code = 'AI_TECH'
    UNION ALL SELECT '機器學習', 'zh', 0.9 WHERE tag_code = 'AI_TECH'
    UNION ALL SELECT 'chatgpt', 'en', 0.8 WHERE tag_code = 'AI_TECH'
    UNION ALL SELECT 'openai', 'en', 0.8 WHERE tag_code = 'AI_TECH'
    
    -- 科技產業相關
    UNION ALL SELECT 'technology', 'en', 1.0 WHERE tag_code = 'TECH'
    UNION ALL SELECT 'tech', 'en', 1.0 WHERE tag_code = 'TECH'
    UNION ALL SELECT '科技', 'zh', 1.0 WHERE tag_code = 'TECH'
    UNION ALL SELECT '科技股', 'zh', 1.0 WHERE tag_code = 'TECH'
    UNION ALL SELECT 'semiconductor', 'en', 0.8 WHERE tag_code = 'TECH'
    UNION ALL SELECT '半導體', 'zh', 0.8 WHERE tag_code = 'TECH'
    
    -- 電動車相關
    UNION ALL SELECT 'electric vehicle', 'en', 1.0 WHERE tag_code = 'ELECTRIC_VEHICLES'
    UNION ALL SELECT 'ev', 'en', 1.0 WHERE tag_code = 'ELECTRIC_VEHICLES'
    UNION ALL SELECT '電動車', 'zh', 1.0 WHERE tag_code = 'ELECTRIC_VEHICLES'
    UNION ALL SELECT '新能源車', 'zh', 1.0 WHERE tag_code = 'ELECTRIC_VEHICLES'
    UNION ALL SELECT '充電', 'zh', 0.7 WHERE tag_code = 'ELECTRIC_VEHICLES'
    
    -- 股票市場相關
    UNION ALL SELECT 'stock', 'en', 1.0 WHERE tag_code = 'STOCK_MARKET'
    UNION ALL SELECT 'market', 'en', 0.8 WHERE tag_code = 'STOCK_MARKET'
    UNION ALL SELECT 'dow', 'en', 0.9 WHERE tag_code = 'STOCK_MARKET'
    UNION ALL SELECT 'nasdaq', 'en', 0.9 WHERE tag_code = 'STOCK_MARKET'
    UNION ALL SELECT 's&p', 'en', 0.9 WHERE tag_code = 'STOCK_MARKET'
    UNION ALL SELECT '股市', 'zh', 1.0 WHERE tag_code = 'STOCK_MARKET'
    UNION ALL SELECT '股票', 'zh', 1.0 WHERE tag_code = 'STOCK_MARKET'
    UNION ALL SELECT '道瓊', 'zh', 0.9 WHERE tag_code = 'STOCK_MARKET'
    UNION ALL SELECT '納斯達克', 'zh', 0.9 WHERE tag_code = 'STOCK_MARKET'
    
    -- 經濟指標相關
    UNION ALL SELECT 'economy', 'en', 1.0 WHERE tag_code = 'ECONOMIES'
    UNION ALL SELECT 'gdp', 'en', 1.0 WHERE tag_code = 'ECONOMIES'
    UNION ALL SELECT 'recession', 'en', 0.9 WHERE tag_code = 'ECONOMIES'
    UNION ALL SELECT 'unemployment', 'en', 0.8 WHERE tag_code = 'ECONOMIES'
    UNION ALL SELECT '經濟', 'zh', 1.0 WHERE tag_code = 'ECONOMIES'
    UNION ALL SELECT '失業率', 'zh', 0.8 WHERE tag_code = 'ECONOMIES'
    UNION ALL SELECT '衰退', 'zh', 0.9 WHERE tag_code = 'ECONOMIES'
    UNION ALL SELECT '成長', 'zh', 0.7 WHERE tag_code = 'ECONOMIES'
    
    -- 聯準會相關
    UNION ALL SELECT 'federal reserve', 'en', 1.0 WHERE tag_code = 'FEDERAL_RESERVE'
    UNION ALL SELECT 'fed', 'en', 1.0 WHERE tag_code = 'FEDERAL_RESERVE'
    UNION ALL SELECT 'interest rate', 'en', 0.9 WHERE tag_code = 'FEDERAL_RESERVE'
    UNION ALL SELECT '聯準會', 'zh', 1.0 WHERE tag_code = 'FEDERAL_RESERVE'
    UNION ALL SELECT '央行', 'zh', 1.0 WHERE tag_code = 'FEDERAL_RESERVE'
    UNION ALL SELECT '美聯儲', 'zh', 1.0 WHERE tag_code = 'FEDERAL_RESERVE'
    UNION ALL SELECT '利率', 'zh', 0.9 WHERE tag_code = 'FEDERAL_RESERVE'
    
    -- 企業財報相關
    UNION ALL SELECT 'earnings', 'en', 1.0 WHERE tag_code = 'EARNINGS'
    UNION ALL SELECT 'revenue', 'en', 0.9 WHERE tag_code = 'EARNINGS'
    UNION ALL SELECT 'profit', 'en', 0.9 WHERE tag_code = 'EARNINGS'
    UNION ALL SELECT 'quarterly', 'en', 0.8 WHERE tag_code = 'EARNINGS'
    UNION ALL SELECT '財報', 'zh', 1.0 WHERE tag_code = 'EARNINGS'
    UNION ALL SELECT '營收', 'zh', 0.9 WHERE tag_code = 'EARNINGS'
    UNION ALL SELECT '獲利', 'zh', 0.9 WHERE tag_code = 'EARNINGS'
    UNION ALL SELECT '季報', 'zh', 0.8 WHERE tag_code = 'EARNINGS'
    
    -- 加密貨幣相關
    UNION ALL SELECT 'bitcoin', 'en', 1.0 WHERE tag_code = 'CRYPTO'
    UNION ALL SELECT 'crypto', 'en', 1.0 WHERE tag_code = 'CRYPTO'
    UNION ALL SELECT 'cryptocurrency', 'en', 1.0 WHERE tag_code = 'CRYPTO'
    UNION ALL SELECT 'blockchain', 'en', 0.9 WHERE tag_code = 'CRYPTO'
    UNION ALL SELECT '比特幣', 'zh', 1.0 WHERE tag_code = 'CRYPTO'
    UNION ALL SELECT '加密貨幣', 'zh', 1.0 WHERE tag_code = 'CRYPTO'
    UNION ALL SELECT '區塊鏈', 'zh', 0.9 WHERE tag_code = 'CRYPTO'
    
    -- 其他產業關鍵字
    UNION ALL SELECT 'housing', 'en', 1.0 WHERE tag_code = 'HOUSING'
    UNION ALL SELECT 'real estate', 'en', 1.0 WHERE tag_code = 'HOUSING'
    UNION ALL SELECT 'mortgage', 'en', 0.8 WHERE tag_code = 'HOUSING'
    UNION ALL SELECT '房地產', 'zh', 1.0 WHERE tag_code = 'HOUSING'
    UNION ALL SELECT '房價', 'zh', 0.9 WHERE tag_code = 'HOUSING'
    UNION ALL SELECT '房貸', 'zh', 0.8 WHERE tag_code = 'HOUSING'
    
    UNION ALL SELECT 'energy', 'en', 1.0 WHERE tag_code = 'ENERGY'
    UNION ALL SELECT 'oil', 'en', 0.9 WHERE tag_code = 'ENERGY'
    UNION ALL SELECT 'gas', 'en', 0.8 WHERE tag_code = 'ENERGY'
    UNION ALL SELECT 'renewable', 'en', 0.8 WHERE tag_code = 'ENERGY'
    UNION ALL SELECT '能源', 'zh', 1.0 WHERE tag_code = 'ENERGY'
    UNION ALL SELECT '石油', 'zh', 0.9 WHERE tag_code = 'ENERGY'
    UNION ALL SELECT '天然氣', 'zh', 0.8 WHERE tag_code = 'ENERGY'
    UNION ALL SELECT '再生能源', 'zh', 0.8 WHERE tag_code = 'ENERGY'
    
    UNION ALL SELECT 'healthcare', 'en', 1.0 WHERE tag_code = 'HEALTHCARE'
    UNION ALL SELECT 'pharma', 'en', 0.9 WHERE tag_code = 'HEALTHCARE'
    UNION ALL SELECT 'medical', 'en', 0.8 WHERE tag_code = 'HEALTHCARE'
    UNION ALL SELECT '醫療', 'zh', 1.0 WHERE tag_code = 'HEALTHCARE'
    UNION ALL SELECT '製藥', 'zh', 0.9 WHERE tag_code = 'HEALTHCARE'
    UNION ALL SELECT '生技', 'zh', 0.8 WHERE tag_code = 'HEALTHCARE'
    
    UNION ALL SELECT 'finance', 'en', 1.0 WHERE tag_code = 'FINANCE'
    UNION ALL SELECT 'banking', 'en', 0.9 WHERE tag_code = 'FINANCE'
    UNION ALL SELECT '金融', 'zh', 1.0 WHERE tag_code = 'FINANCE'
    UNION ALL SELECT '銀行', 'zh', 0.9 WHERE tag_code = 'FINANCE'
    UNION ALL SELECT '保險', 'zh', 0.8 WHERE tag_code = 'FINANCE'
    
    UNION ALL SELECT 'tariff', 'en', 1.0 WHERE tag_code = 'TARIFFS'
    UNION ALL SELECT '關稅', 'zh', 1.0 WHERE tag_code = 'TARIFFS'
    UNION ALL SELECT '貿易戰', 'zh', 0.9 WHERE tag_code = 'TARIFFS'
    
    UNION ALL SELECT 'trade', 'en', 1.0 WHERE tag_code = 'TRADE'
    UNION ALL SELECT 'import', 'en', 0.8 WHERE tag_code = 'TRADE'
    UNION ALL SELECT 'export', 'en', 0.8 WHERE tag_code = 'TRADE'
    UNION ALL SELECT '貿易', 'zh', 1.0 WHERE tag_code = 'TRADE'
    UNION ALL SELECT '進口', 'zh', 0.8 WHERE tag_code = 'TRADE'
    UNION ALL SELECT '出口', 'zh', 0.8 WHERE tag_code = 'TRADE'
    
    UNION ALL SELECT 'bonds', 'en', 1.0 WHERE tag_code = 'BONDS'
    UNION ALL SELECT 'treasury', 'en', 0.9 WHERE tag_code = 'BONDS'
    UNION ALL SELECT 'yield', 'en', 0.8 WHERE tag_code = 'BONDS'
    UNION ALL SELECT '債券', 'zh', 1.0 WHERE tag_code = 'BONDS'
    UNION ALL SELECT '公債', 'zh', 0.9 WHERE tag_code = 'BONDS'
    UNION ALL SELECT '殖利率', 'zh', 0.8 WHERE tag_code = 'BONDS'
    
    UNION ALL SELECT 'commodities', 'en', 1.0 WHERE tag_code = 'COMMODITIES'
    UNION ALL SELECT 'gold', 'en', 0.9 WHERE tag_code = 'COMMODITIES'
    UNION ALL SELECT 'silver', 'en', 0.8 WHERE tag_code = 'COMMODITIES'
    UNION ALL SELECT '商品', 'zh', 1.0 WHERE tag_code = 'COMMODITIES'
    UNION ALL SELECT '黃金', 'zh', 0.9 WHERE tag_code = 'COMMODITIES'
    UNION ALL SELECT '白銀', 'zh', 0.8 WHERE tag_code = 'COMMODITIES'
    
    -- 通用關鍵字
    UNION ALL SELECT 'latest', 'en', 0.8 WHERE tag_code = 'LATEST'
    UNION ALL SELECT 'news', 'en', 0.7 WHERE tag_code = 'LATEST'
    UNION ALL SELECT '最新', 'zh', 0.8 WHERE tag_code = 'LATEST'
    UNION ALL SELECT '消息', 'zh', 0.7 WHERE tag_code = 'LATEST'
    UNION ALL SELECT '新聞', 'zh', 0.6 WHERE tag_code = 'LATEST'
) kw ON t.tag_code = (
    CASE 
        WHEN kw.keyword IN ('apple', 'aapl', '蘋果', '庫克', 'iphone', 'mac') THEN 'APPLE'
        WHEN kw.keyword IN ('tsmc', 'taiwan semiconductor', '台積電', '晶圓') THEN 'TSMC'
        WHEN kw.keyword IN ('tesla', 'tsla', '特斯拉', '馬斯克', 'elon musk') THEN 'TESLA'
        WHEN kw.keyword IN ('ai', 'artificial intelligence', '人工智慧', 'machine learning', '機器學習', 'chatgpt', 'openai') THEN 'AI_TECH'
        WHEN kw.keyword IN ('technology', 'tech', '科技', '科技股', 'semiconductor', '半導體') THEN 'TECH'
        WHEN kw.keyword IN ('electric vehicle', 'ev', '電動車', '新能源車', '充電') THEN 'ELECTRIC_VEHICLES'
        WHEN kw.keyword IN ('stock', 'market', 'dow', 'nasdaq', 's&p', '股市', '股票', '道瓊', '納斯達克') THEN 'STOCK_MARKET'
        WHEN kw.keyword IN ('economy', 'gdp', 'recession', 'unemployment', '經濟', '失業率', '衰退', '成長') THEN 'ECONOMIES'
        WHEN kw.keyword IN ('federal reserve', 'fed', 'interest rate', '聯準會', '央行', '美聯儲', '利率') THEN 'FEDERAL_RESERVE'
        WHEN kw.keyword IN ('earnings', 'revenue', 'profit', 'quarterly', '財報', '營收', '獲利', '季報') THEN 'EARNINGS'
        WHEN kw.keyword IN ('bitcoin', 'crypto', 'cryptocurrency', 'blockchain', '比特幣', '加密貨幣', '區塊鏈') THEN 'CRYPTO'
        WHEN kw.keyword IN ('housing', 'real estate', 'mortgage', '房地產', '房價', '房貸') THEN 'HOUSING'
        WHEN kw.keyword IN ('energy', 'oil', 'gas', 'renewable', '能源', '石油', '天然氣', '再生能源') THEN 'ENERGY'
        WHEN kw.keyword IN ('healthcare', 'pharma', 'medical', '醫療', '製藥', '生技') THEN 'HEALTHCARE'
        WHEN kw.keyword IN ('finance', 'banking', '金融', '銀行', '保險') THEN 'FINANCE'
        WHEN kw.keyword IN ('tariff', '關稅', '貿易戰') THEN 'TARIFFS'
        WHEN kw.keyword IN ('trade', 'import', 'export', '貿易', '進口', '出口') THEN 'TRADE'
        WHEN kw.keyword IN ('bonds', 'treasury', 'yield', '債券', '公債', '殖利率') THEN 'BONDS'
        WHEN kw.keyword IN ('commodities', 'gold', 'silver', '商品', '黃金', '白銀') THEN 'COMMODITIES'
        WHEN kw.keyword IN ('latest', 'news', '最新', '消息', '新聞') THEN 'LATEST'
        ELSE NULL
    END
)
WHERE t.tag_code IS NOT NULL
ON CONFLICT (tag_id, keyword) DO UPDATE SET
    confidence = EXCLUDED.confidence,
    updated_at = CURRENT_TIMESTAMP;

-- =====================================================
-- 第三階段: 建立索引以優化查詢性能
-- =====================================================

-- 標籤表索引
CREATE INDEX IF NOT EXISTS idx_tags_code_active ON public.tags (tag_code, is_active);
CREATE INDEX IF NOT EXISTS idx_tags_priority ON public.tags (priority) WHERE is_active = true;

-- 關鍵字映射表索引  
CREATE INDEX IF NOT EXISTS idx_keyword_mappings_keyword ON public.keyword_mappings (keyword) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_keyword_mappings_tag_id ON public.keyword_mappings (tag_id) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_keyword_mappings_language ON public.keyword_mappings (language) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_keyword_mappings_confidence ON public.keyword_mappings (confidence DESC) WHERE is_active = true;

-- 文章標籤表索引
CREATE INDEX IF NOT EXISTS idx_article_tags_article_id ON public.article_tags (article_id);
CREATE INDEX IF NOT EXISTS idx_article_tags_tag_id ON public.article_tags (tag_id);
CREATE INDEX IF NOT EXISTS idx_article_tags_confidence ON public.article_tags (confidence DESC);

-- =====================================================
-- 第四階段: 創建統計視圖
-- =====================================================

-- 標籤使用統計視圖
CREATE OR REPLACE VIEW tag_usage_stats AS
SELECT 
    t.tag_code,
    t.tag_name_zh,
    t.tag_name_en,
    t.priority,
    COUNT(km.id) as keyword_mappings_count,
    COUNT(at.id) as article_tags_count,
    AVG(at.confidence) as avg_confidence
FROM public.tags t
LEFT JOIN public.keyword_mappings km ON t.id = km.tag_id AND km.is_active = true
LEFT JOIN public.article_tags at ON t.id = at.tag_id
WHERE t.is_active = true
GROUP BY t.id, t.tag_code, t.tag_name_zh, t.tag_name_en, t.priority
ORDER BY t.priority, article_tags_count DESC;

-- 關鍵字映射統計視圖
CREATE OR REPLACE VIEW keyword_mapping_stats AS
SELECT 
    km.language,
    km.mapping_type,
    COUNT(*) as total_mappings,
    AVG(km.confidence) as avg_confidence,
    COUNT(DISTINCT km.tag_id) as unique_tags_count
FROM public.keyword_mappings km
WHERE km.is_active = true
GROUP BY km.language, km.mapping_type
ORDER BY total_mappings DESC;

-- =====================================================
-- 第五階段: 權限設置
-- =====================================================

-- 確保 authenticated 用戶可以讀取標籤數據
GRANT SELECT ON public.tags TO authenticated;
GRANT SELECT ON public.keyword_mappings TO authenticated;
GRANT SELECT ON public.article_tags TO authenticated;
GRANT SELECT ON tag_usage_stats TO authenticated;
GRANT SELECT ON keyword_mapping_stats TO authenticated;

-- 確保 service_role 可以管理標籤數據
GRANT ALL ON public.tags TO service_role;
GRANT ALL ON public.keyword_mappings TO service_role;
GRANT ALL ON public.article_tags TO service_role;

-- =====================================================
-- 遷移完成確認
-- =====================================================

-- 查看遷移結果統計
SELECT 
    '標籤總數' as metric,
    COUNT(*) as value
FROM public.tags 
WHERE is_active = true

UNION ALL

SELECT 
    '關鍵字映射總數' as metric,
    COUNT(*) as value
FROM public.keyword_mappings 
WHERE is_active = true

UNION ALL

SELECT 
    '中文關鍵字數量' as metric,
    COUNT(*) as value
FROM public.keyword_mappings 
WHERE language = 'zh' AND is_active = true

UNION ALL

SELECT 
    '英文關鍵字數量' as metric,
    COUNT(*) as value
FROM public.keyword_mappings 
WHERE language = 'en' AND is_active = true;

-- 顯示各標籤的關鍵字映射數量
SELECT 
    t.tag_code,
    t.tag_name_zh,
    COUNT(km.id) as keyword_count
FROM public.tags t
LEFT JOIN public.keyword_mappings km ON t.id = km.tag_id AND km.is_active = true
WHERE t.is_active = true
GROUP BY t.id, t.tag_code, t.tag_name_zh
ORDER BY keyword_count DESC, t.priority;

-- =====================================================
-- 腳本執行說明
-- =====================================================

/*
執行此腳本後，系統將具備以下功能:

1. 🏷️ 統一標籤管理
   - 20個核心財經標籤
   - 中英文對照支援
   - 優先級排序

2. 🔍 智能關鍵字映射  
   - 80+ 關鍵字映射規則
   - 多語言支援 (中文/英文)
   - 信心度評分系統

3. 📊 性能優化
   - 完整索引配置
   - 查詢性能優化
   - 統計視圖支援

4. 🔐 權限控制
   - 適當的資料庫權限設置
   - 安全的資料存取控制

執行完成後，請運行以下Python腳本驗證:
```bash
python scripts/dynamic_tags.py
python scripts/run_pusher_test.py
```

如果遇到問題，請檢查:
1. Supabase連接配置
2. 環境變數設置
3. 資料庫權限設定
*/