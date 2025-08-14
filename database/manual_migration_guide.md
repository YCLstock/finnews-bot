# 翻譯功能資料庫遷移指南

## Phase 1: 手動新增 translated_title 欄位

由於 Supabase 的安全限制，我們無法透過程式碼直接執行 DDL 語句。請按照以下步驟手動新增欄位：

### 方式一：透過 Supabase Dashboard

1. 登入 [Supabase Dashboard](https://supabase.com/dashboard)
2. 選擇您的專案：`finnews-bot`
3. 進入 `Table Editor`
4. 選擇 `news_articles` 表
5. 點擊右上角的 `Add Column` 按鈕
6. 設定欄位資訊：
   - **Name**: `translated_title`
   - **Type**: `text`
   - **Default Value**: 留空
   - **Is Nullable**: ✅ 勾選
   - **Is Unique**: ❌ 不勾選

### 方式二：透過 SQL Editor

1. 在 Supabase Dashboard 中進入 `SQL Editor`
2. 執行以下 SQL 語句：

```sql
-- 新增翻譯標題欄位
ALTER TABLE public.news_articles 
ADD COLUMN translated_title TEXT;

-- 新增欄位註釋
COMMENT ON COLUMN public.news_articles.translated_title 
IS '文章標題的中文翻譯，用於中文用戶的Discord通知顯示';

-- 建立部分索引（可選，用於效能優化）
CREATE INDEX CONCURRENTLY idx_news_articles_translated_title 
ON public.news_articles (translated_title) 
WHERE translated_title IS NOT NULL;
```

### 驗證步驟

完成新增後，請執行以下驗證腳本：

```bash
python database/test_translation_migration.py
```

### 預期結果

執行成功後，你應該看到：
- ✅ translated_title 欄位存在
- ✅ 基本查詢功能正常
- ✅ 新增包含翻譯的文章測試通過
- ✅ 查詢效能測試通過

## 注意事項

- 新增的 `translated_title` 欄位為 `TEXT` 類型，可為 `NULL`
- 不影響現有資料和功能
- 現有文章的 `translated_title` 將為 `NULL`，需要後續批次翻譯
- 新增索引可以提高查詢效能，但不是必須的

## 如果遇到問題

1. 確認您有資料庫的管理權限
2. 確認 `news_articles` 表存在且可正常訪問
3. 如果無法新增欄位，請檢查 Supabase 計畫限制

## 下一步

完成欄位新增並通過驗證測試後，我們將繼續：
- Phase 2: 建立翻譯服務
- Phase 3: 整合到爬蟲流程  
- Phase 4: 修改 Discord 推送邏輯