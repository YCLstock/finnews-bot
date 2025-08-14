PS D:\AI\finnews-bot> python database/test_translation_migration.py
INFO:__main__:翻譯功能 Phase 1 測試開始
INFO:__main__:環境: development
INFO:__main__:資料庫: https://gbobozzqoqfhqmttwzwn.supabase.co
INFO:__main__:🚀 開始 Phase 1 資料庫遷移測試...
INFO:__main__:
📋 執行 欄位存在性測試...
INFO:__main__:🔍 測試 translated_title 欄位是否存在...        
INFO:httpx:HTTP Request: POST https://gbobozzqoqfhqmttwzwn.supabase.co/rest/v1/rpc/get_column_info "HTTP/2 404 Not Found"
ERROR:__main__:❌ 檢查欄位存在性失敗: {'message': 'Could not find the function public.get_column_info(column_name, table_name) in the schema cache', 'code': 'PGRST202', 'hint': None, 'details': 'Searched for the function 
public.get_column_info with parameters column_name, table_name or with a single unnamed json/jsonb parameter, but no matches were found in the schema cache.'}
ERROR:__main__:❌ 欄位存在性測試 失敗
INFO:__main__:
📋 執行 向後相容性測試...
INFO:__main__:🔍 測試向後相容性...
INFO:httpx:HTTP Request: GET https://gbobozzqoqfhqmttwzwn.supabase.co/rest/v1/news_articles?select=id%2Ctitle%2Csummary%2Coriginal_url%2Ctranslated_title&limit=5 "HTTP/2 200 OK"
INFO:__main__:✅ 基本查詢功能正常 (查詢到 5 筆資料)  
INFO:__main__:✅ 文章 ID 1 包含 translated_title 欄位
INFO:__main__:✅ 文章 ID 2 包含 translated_title 欄位
INFO:__main__:✅ 文章 ID 3 包含 translated_title 欄位
INFO:__main__:✅ 文章 ID 6 包含 translated_title 欄位
INFO:__main__:✅ 文章 ID 7 包含 translated_title 欄位
INFO:__main__:✅ 向後相容性測試 通過
INFO:__main__:
📋 執行 翻譯新增測試...
INFO:__main__:🔍 測試新增文章包含翻譯標題...
INFO:httpx:HTTP Request: POST https://gbobozzqoqfhqmttwzwn.supabase.co/rest/v1/news_articles "HTTP/2 201 Created"
INFO:__main__:✅ 成功新增包含翻譯的文章 (ID: 1396)
INFO:__main__:✅ 翻譯標題正確儲存
INFO:httpx:HTTP Request: DELETE https://gbobozzqoqfhqmttwzwn.supabase.co/rest/v1/news_articles?id=eq.1396 "HTTP/2 200 OK"
INFO:__main__:🗑️ 清理測試資料完成
INFO:__main__:✅ 翻譯新增測試 通過
INFO:__main__:
📋 執行 效能測試...
INFO:__main__:🔍 測試查詢效能...
INFO:httpx:HTTP Request: GET https://gbobozzqoqfhqmttwzwn.supabase.co/rest/v1/news_articles?select=id%2Ctitle%2Csummary%2Ctranslated_title&limit=100 "HTTP/2 200 OK"
INFO:__main__:✅ 查詢 100 筆文章耗時: 0.181 秒
INFO:__main__:✅ 查詢效能測試通過
INFO:__main__:✅ 效能測試 通過
INFO:__main__:
📊 測試結果: 3/4 個測試通過
ERROR:__main__:❌ 部分測試失敗，請檢查問題後重新執行
ERROR:__main__:
❌ Phase 1 測試失敗，請檢查問題