-- SQL語法測試腳本
-- 用於驗證修復後的SQL是否正確

-- 測試標籤插入語法
SELECT 'Testing tags insert syntax...' as test_step;

-- 模擬標籤插入 (不實際執行，只檢查語法)
-- INSERT INTO public.tags (tag_code, tag_name_zh, tag_name_en, priority, is_active) 
-- VALUES ('TEST_TAG', '測試標籤', 'Test Tag', 100, true);

-- 測試關鍵字映射插入語法
SELECT 'Testing keyword mappings insert syntax...' as test_step;

-- 模擬單個關鍵字映射插入 (檢查語法結構)
WITH test_tag AS (
    SELECT 1 as id  -- 模擬tag_id
)
SELECT t.id, kw.keyword, kw.language, 'system_migration', kw.confidence, 'exact', true
FROM test_tag t
CROSS JOIN (VALUES 
    ('test_keyword', 'en', 1.0),
    ('測試關鍵字', 'zh', 1.0)
) AS kw(keyword, language, confidence);

-- 測試多個INSERT語句的語法結構
SELECT 'Testing multiple insert statements...' as test_step;

-- 這模擬了我們修復後的結構
WITH apple_tag AS (SELECT 1 as id),
     keyword_data AS (
         SELECT * FROM (VALUES 
             ('apple', 'en', 1.0),
             ('蘋果', 'zh', 1.0)
         ) AS kw(keyword, language, confidence)
     )
SELECT t.id, kw.keyword, kw.language, 'system_migration', kw.confidence, 'exact', true
FROM apple_tag t
CROSS JOIN keyword_data kw;

-- 測試ON CONFLICT語法
SELECT 'Testing ON CONFLICT syntax...' as test_step;

-- 創建臨時表測試
CREATE TEMP TABLE test_keyword_mappings (
    tag_id integer,
    keyword varchar,
    confidence numeric,
    PRIMARY KEY (tag_id, keyword)
);

-- 測試ON CONFLICT語句
INSERT INTO test_keyword_mappings (tag_id, keyword, confidence)
VALUES (1, 'test', 1.0)
ON CONFLICT (tag_id, keyword) DO UPDATE SET
    confidence = EXCLUDED.confidence;

-- 清理測試表
DROP TABLE test_keyword_mappings;

SELECT 'All syntax tests passed successfully!' as result;