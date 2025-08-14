-- 新增翻譯標題欄位到 news_articles 表
-- 翻譯功能 Phase 1: 資料庫遷移腳本

-- 新增翻譯標題欄位（可為null，不影響現有資料）
ALTER TABLE public.news_articles 
ADD COLUMN translated_title TEXT;

-- 新增註釋說明欄位用途
COMMENT ON COLUMN public.news_articles.translated_title 
IS '文章標題的中文翻譯，用於中文用戶的Discord通知顯示';

-- 建立部分索引（僅對有翻譯的文章建立索引以節省空間）
CREATE INDEX CONCURRENTLY idx_news_articles_translated_title 
ON public.news_articles (translated_title) 
WHERE translated_title IS NOT NULL;

-- 驗證遷移是否成功
SELECT 
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_name = 'news_articles' 
    AND table_schema = 'public'
    AND column_name = 'translated_title';