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

-- 插入基礎關鍵字映射 (重構為獨立INSERT語句以避免語法錯誤)

-- 蘋果公司關鍵字映射
INSERT INTO public.keyword_mappings (tag_id, keyword, language, mapping_type, confidence, match_method, is_active)
SELECT t.id, kw.keyword, kw.language, 'system_migration', kw.confidence, 'exact', true
FROM (SELECT id FROM public.tags WHERE tag_code = 'APPLE' AND is_active = true) t
CROSS JOIN (VALUES 
    ('apple', 'en', 1.0),
    ('aapl', 'en', 1.0),
    ('蘋果', 'zh', 1.0),
    ('庫克', 'zh', 0.8),
    ('iphone', 'en', 0.9),
    ('mac', 'en', 0.7)
) AS kw(keyword, language, confidence)
ON CONFLICT (tag_id, keyword) DO UPDATE SET
    confidence = EXCLUDED.confidence,
    updated_at = CURRENT_TIMESTAMP;

-- 台積電關鍵字映射
INSERT INTO public.keyword_mappings (tag_id, keyword, language, mapping_type, confidence, match_method, is_active)
SELECT t.id, kw.keyword, kw.language, 'system_migration', kw.confidence, 'exact', true
FROM (SELECT id FROM public.tags WHERE tag_code = 'TSMC' AND is_active = true) t
CROSS JOIN (VALUES 
    ('tsmc', 'en', 1.0),
    ('taiwan semiconductor', 'en', 1.0),
    ('台積電', 'zh', 1.0),
    ('晶圓', 'zh', 0.8)
) AS kw(keyword, language, confidence)
ON CONFLICT (tag_id, keyword) DO UPDATE SET
    confidence = EXCLUDED.confidence,
    updated_at = CURRENT_TIMESTAMP;

-- 特斯拉關鍵字映射
INSERT INTO public.keyword_mappings (tag_id, keyword, language, mapping_type, confidence, match_method, is_active)
SELECT t.id, kw.keyword, kw.language, 'system_migration', kw.confidence, 'exact', true
FROM (SELECT id FROM public.tags WHERE tag_code = 'TESLA' AND is_active = true) t
CROSS JOIN (VALUES 
    ('tesla', 'en', 1.0),
    ('tsla', 'en', 1.0),
    ('特斯拉', 'zh', 1.0),
    ('馬斯克', 'zh', 0.9),
    ('elon musk', 'en', 0.9)
) AS kw(keyword, language, confidence)
ON CONFLICT (tag_id, keyword) DO UPDATE SET
    confidence = EXCLUDED.confidence,
    updated_at = CURRENT_TIMESTAMP;

-- AI科技關鍵字映射
INSERT INTO public.keyword_mappings (tag_id, keyword, language, mapping_type, confidence, match_method, is_active)
SELECT t.id, kw.keyword, kw.language, 'system_migration', kw.confidence, 'exact', true
FROM (SELECT id FROM public.tags WHERE tag_code = 'AI_TECH' AND is_active = true) t
CROSS JOIN (VALUES 
    ('ai', 'en', 1.0),
    ('artificial intelligence', 'en', 1.0),
    ('人工智慧', 'zh', 1.0),
    ('machine learning', 'en', 0.9),
    ('機器學習', 'zh', 0.9),
    ('chatgpt', 'en', 0.8),
    ('openai', 'en', 0.8)
) AS kw(keyword, language, confidence)
ON CONFLICT (tag_id, keyword) DO UPDATE SET
    confidence = EXCLUDED.confidence,
    updated_at = CURRENT_TIMESTAMP;

-- 科技產業關鍵字映射
INSERT INTO public.keyword_mappings (tag_id, keyword, language, mapping_type, confidence, match_method, is_active)
SELECT t.id, kw.keyword, kw.language, 'system_migration', kw.confidence, 'exact', true
FROM (SELECT id FROM public.tags WHERE tag_code = 'TECH' AND is_active = true) t
CROSS JOIN (VALUES 
    ('technology', 'en', 1.0),
    ('tech', 'en', 1.0),
    ('科技', 'zh', 1.0),
    ('科技股', 'zh', 1.0),
    ('semiconductor', 'en', 0.8),
    ('半導體', 'zh', 0.8)
) AS kw(keyword, language, confidence)
ON CONFLICT (tag_id, keyword) DO UPDATE SET
    confidence = EXCLUDED.confidence,
    updated_at = CURRENT_TIMESTAMP;

-- 電動車關鍵字映射
INSERT INTO public.keyword_mappings (tag_id, keyword, language, mapping_type, confidence, match_method, is_active)
SELECT t.id, kw.keyword, kw.language, 'system_migration', kw.confidence, 'exact', true
FROM (SELECT id FROM public.tags WHERE tag_code = 'ELECTRIC_VEHICLES' AND is_active = true) t
CROSS JOIN (VALUES 
    ('electric vehicle', 'en', 1.0),
    ('ev', 'en', 1.0),
    ('電動車', 'zh', 1.0),
    ('新能源車', 'zh', 1.0),
    ('充電', 'zh', 0.7)
) AS kw(keyword, language, confidence)
ON CONFLICT (tag_id, keyword) DO UPDATE SET
    confidence = EXCLUDED.confidence,
    updated_at = CURRENT_TIMESTAMP;

-- 股票市場關鍵字映射
INSERT INTO public.keyword_mappings (tag_id, keyword, language, mapping_type, confidence, match_method, is_active)
SELECT t.id, kw.keyword, kw.language, 'system_migration', kw.confidence, 'exact', true
FROM (SELECT id FROM public.tags WHERE tag_code = 'STOCK_MARKET' AND is_active = true) t
CROSS JOIN (VALUES 
    ('stock', 'en', 1.0),
    ('market', 'en', 0.8),
    ('dow', 'en', 0.9),
    ('nasdaq', 'en', 0.9),
    ('s&p', 'en', 0.9),
    ('股市', 'zh', 1.0),
    ('股票', 'zh', 1.0),
    ('道瓊', 'zh', 0.9),
    ('納斯達克', 'zh', 0.9)
) AS kw(keyword, language, confidence)
ON CONFLICT (tag_id, keyword) DO UPDATE SET
    confidence = EXCLUDED.confidence,
    updated_at = CURRENT_TIMESTAMP;

-- 經濟指標關鍵字映射
INSERT INTO public.keyword_mappings (tag_id, keyword, language, mapping_type, confidence, match_method, is_active)
SELECT t.id, kw.keyword, kw.language, 'system_migration', kw.confidence, 'exact', true
FROM (SELECT id FROM public.tags WHERE tag_code = 'ECONOMIES' AND is_active = true) t
CROSS JOIN (VALUES 
    ('economy', 'en', 1.0),
    ('gdp', 'en', 1.0),
    ('recession', 'en', 0.9),
    ('unemployment', 'en', 0.8),
    ('經濟', 'zh', 1.0),
    ('失業率', 'zh', 0.8),
    ('衰退', 'zh', 0.9),
    ('成長', 'zh', 0.7)
) AS kw(keyword, language, confidence)
ON CONFLICT (tag_id, keyword) DO UPDATE SET
    confidence = EXCLUDED.confidence,
    updated_at = CURRENT_TIMESTAMP;

-- 聯準會關鍵字映射
INSERT INTO public.keyword_mappings (tag_id, keyword, language, mapping_type, confidence, match_method, is_active)
SELECT t.id, kw.keyword, kw.language, 'system_migration', kw.confidence, 'exact', true
FROM (SELECT id FROM public.tags WHERE tag_code = 'FEDERAL_RESERVE' AND is_active = true) t
CROSS JOIN (VALUES 
    ('federal reserve', 'en', 1.0),
    ('fed', 'en', 1.0),
    ('interest rate', 'en', 0.9),
    ('聯準會', 'zh', 1.0),
    ('央行', 'zh', 1.0),
    ('美聯儲', 'zh', 1.0),
    ('利率', 'zh', 0.9)
) AS kw(keyword, language, confidence)
ON CONFLICT (tag_id, keyword) DO UPDATE SET
    confidence = EXCLUDED.confidence,
    updated_at = CURRENT_TIMESTAMP;

-- 企業財報關鍵字映射
INSERT INTO public.keyword_mappings (tag_id, keyword, language, mapping_type, confidence, match_method, is_active)
SELECT t.id, kw.keyword, kw.language, 'system_migration', kw.confidence, 'exact', true
FROM (SELECT id FROM public.tags WHERE tag_code = 'EARNINGS' AND is_active = true) t
CROSS JOIN (VALUES 
    ('earnings', 'en', 1.0),
    ('revenue', 'en', 0.9),
    ('profit', 'en', 0.9),
    ('quarterly', 'en', 0.8),
    ('財報', 'zh', 1.0),
    ('營收', 'zh', 0.9),
    ('獲利', 'zh', 0.9),
    ('季報', 'zh', 0.8)
) AS kw(keyword, language, confidence)
ON CONFLICT (tag_id, keyword) DO UPDATE SET
    confidence = EXCLUDED.confidence,
    updated_at = CURRENT_TIMESTAMP;

-- 加密貨幣關鍵字映射
INSERT INTO public.keyword_mappings (tag_id, keyword, language, mapping_type, confidence, match_method, is_active)
SELECT t.id, kw.keyword, kw.language, 'system_migration', kw.confidence, 'exact', true
FROM (SELECT id FROM public.tags WHERE tag_code = 'CRYPTO' AND is_active = true) t
CROSS JOIN (VALUES 
    ('bitcoin', 'en', 1.0),
    ('crypto', 'en', 1.0),
    ('cryptocurrency', 'en', 1.0),
    ('blockchain', 'en', 0.9),
    ('比特幣', 'zh', 1.0),
    ('加密貨幣', 'zh', 1.0),
    ('區塊鏈', 'zh', 0.9)
) AS kw(keyword, language, confidence)
ON CONFLICT (tag_id, keyword) DO UPDATE SET
    confidence = EXCLUDED.confidence,
    updated_at = CURRENT_TIMESTAMP;

-- 房地產關鍵字映射
INSERT INTO public.keyword_mappings (tag_id, keyword, language, mapping_type, confidence, match_method, is_active)
SELECT t.id, kw.keyword, kw.language, 'system_migration', kw.confidence, 'exact', true
FROM (SELECT id FROM public.tags WHERE tag_code = 'HOUSING' AND is_active = true) t
CROSS JOIN (VALUES 
    ('housing', 'en', 1.0),
    ('real estate', 'en', 1.0),
    ('mortgage', 'en', 0.8),
    ('房地產', 'zh', 1.0),
    ('房價', 'zh', 0.9),
    ('房貸', 'zh', 0.8)
) AS kw(keyword, language, confidence)
ON CONFLICT (tag_id, keyword) DO UPDATE SET
    confidence = EXCLUDED.confidence,
    updated_at = CURRENT_TIMESTAMP;

-- 能源產業關鍵字映射
INSERT INTO public.keyword_mappings (tag_id, keyword, language, mapping_type, confidence, match_method, is_active)
SELECT t.id, kw.keyword, kw.language, 'system_migration', kw.confidence, 'exact', true
FROM (SELECT id FROM public.tags WHERE tag_code = 'ENERGY' AND is_active = true) t
CROSS JOIN (VALUES 
    ('energy', 'en', 1.0),
    ('oil', 'en', 0.9),
    ('gas', 'en', 0.8),
    ('renewable', 'en', 0.8),
    ('能源', 'zh', 1.0),
    ('石油', 'zh', 0.9),
    ('天然氣', 'zh', 0.8),
    ('再生能源', 'zh', 0.8)
) AS kw(keyword, language, confidence)
ON CONFLICT (tag_id, keyword) DO UPDATE SET
    confidence = EXCLUDED.confidence,
    updated_at = CURRENT_TIMESTAMP;

-- 醫療保健關鍵字映射
INSERT INTO public.keyword_mappings (tag_id, keyword, language, mapping_type, confidence, match_method, is_active)
SELECT t.id, kw.keyword, kw.language, 'system_migration', kw.confidence, 'exact', true
FROM (SELECT id FROM public.tags WHERE tag_code = 'HEALTHCARE' AND is_active = true) t
CROSS JOIN (VALUES 
    ('healthcare', 'en', 1.0),
    ('pharma', 'en', 0.9),
    ('medical', 'en', 0.8),
    ('醫療', 'zh', 1.0),
    ('製藥', 'zh', 0.9),
    ('生技', 'zh', 0.8)
) AS kw(keyword, language, confidence)
ON CONFLICT (tag_id, keyword) DO UPDATE SET
    confidence = EXCLUDED.confidence,
    updated_at = CURRENT_TIMESTAMP;

-- 金融業關鍵字映射
INSERT INTO public.keyword_mappings (tag_id, keyword, language, mapping_type, confidence, match_method, is_active)
SELECT t.id, kw.keyword, kw.language, 'system_migration', kw.confidence, 'exact', true
FROM (SELECT id FROM public.tags WHERE tag_code = 'FINANCE' AND is_active = true) t
CROSS JOIN (VALUES 
    ('finance', 'en', 1.0),
    ('banking', 'en', 0.9),
    ('金融', 'zh', 1.0),
    ('銀行', 'zh', 0.9),
    ('保險', 'zh', 0.8)
) AS kw(keyword, language, confidence)
ON CONFLICT (tag_id, keyword) DO UPDATE SET
    confidence = EXCLUDED.confidence,
    updated_at = CURRENT_TIMESTAMP;

-- 關稅貿易關鍵字映射
INSERT INTO public.keyword_mappings (tag_id, keyword, language, mapping_type, confidence, match_method, is_active)
SELECT t.id, kw.keyword, kw.language, 'system_migration', kw.confidence, 'exact', true
FROM (SELECT id FROM public.tags WHERE tag_code = 'TARIFFS' AND is_active = true) t
CROSS JOIN (VALUES 
    ('tariff', 'en', 1.0),
    ('關稅', 'zh', 1.0),
    ('貿易戰', 'zh', 0.9)
) AS kw(keyword, language, confidence)
ON CONFLICT (tag_id, keyword) DO UPDATE SET
    confidence = EXCLUDED.confidence,
    updated_at = CURRENT_TIMESTAMP;

-- 國際貿易關鍵字映射
INSERT INTO public.keyword_mappings (tag_id, keyword, language, mapping_type, confidence, match_method, is_active)
SELECT t.id, kw.keyword, kw.language, 'system_migration', kw.confidence, 'exact', true
FROM (SELECT id FROM public.tags WHERE tag_code = 'TRADE' AND is_active = true) t
CROSS JOIN (VALUES 
    ('trade', 'en', 1.0),
    ('import', 'en', 0.8),
    ('export', 'en', 0.8),
    ('貿易', 'zh', 1.0),
    ('進口', 'zh', 0.8),
    ('出口', 'zh', 0.8)
) AS kw(keyword, language, confidence)
ON CONFLICT (tag_id, keyword) DO UPDATE SET
    confidence = EXCLUDED.confidence,
    updated_at = CURRENT_TIMESTAMP;

-- 債券市場關鍵字映射
INSERT INTO public.keyword_mappings (tag_id, keyword, language, mapping_type, confidence, match_method, is_active)
SELECT t.id, kw.keyword, kw.language, 'system_migration', kw.confidence, 'exact', true
FROM (SELECT id FROM public.tags WHERE tag_code = 'BONDS' AND is_active = true) t
CROSS JOIN (VALUES 
    ('bonds', 'en', 1.0),
    ('treasury', 'en', 0.9),
    ('yield', 'en', 0.8),
    ('債券', 'zh', 1.0),
    ('公債', 'zh', 0.9),
    ('殖利率', 'zh', 0.8)
) AS kw(keyword, language, confidence)
ON CONFLICT (tag_id, keyword) DO UPDATE SET
    confidence = EXCLUDED.confidence,
    updated_at = CURRENT_TIMESTAMP;

-- 商品期貨關鍵字映射
INSERT INTO public.keyword_mappings (tag_id, keyword, language, mapping_type, confidence, match_method, is_active)
SELECT t.id, kw.keyword, kw.language, 'system_migration', kw.confidence, 'exact', true
FROM (SELECT id FROM public.tags WHERE tag_code = 'COMMODITIES' AND is_active = true) t
CROSS JOIN (VALUES 
    ('commodities', 'en', 1.0),
    ('gold', 'en', 0.9),
    ('silver', 'en', 0.8),
    ('商品', 'zh', 1.0),
    ('黃金', 'zh', 0.9),
    ('白銀', 'zh', 0.8)
) AS kw(keyword, language, confidence)
ON CONFLICT (tag_id, keyword) DO UPDATE SET
    confidence = EXCLUDED.confidence,
    updated_at = CURRENT_TIMESTAMP;

-- 最新消息關鍵字映射
INSERT INTO public.keyword_mappings (tag_id, keyword, language, mapping_type, confidence, match_method, is_active)
SELECT t.id, kw.keyword, kw.language, 'system_migration', kw.confidence, 'exact', true
FROM (SELECT id FROM public.tags WHERE tag_code = 'LATEST' AND is_active = true) t
CROSS JOIN (VALUES 
    ('latest', 'en', 0.8),
    ('news', 'en', 0.7),
    ('最新', 'zh', 0.8),
    ('消息', 'zh', 0.7),
    ('新聞', 'zh', 0.6)
) AS kw(keyword, language, confidence)
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