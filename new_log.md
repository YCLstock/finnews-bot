INFO:scraper.scraper:準備將 85 篇文章進行批次儲存...
INFO:httpx:HTTP Request: POST https://gbobozzqoqfhqmttwzwn.supabase.co/rest/v1/news_articles?columns=%22title%22%2C%22topics%22%2C%22published_at%22%2C%22tags%22%2C%22original_url%22%2C%22summary%22%2C%22source%22 "HTTP/2 409 Conflict"
[ERROR] 批量儲存新文章時錯誤: {'message': 'duplicate key value violates unique constraint "news_articles_original_url_key"', 'code': '23505', 'hint': None, 'details': 'Key (original_url)=(https://finance.yahoo.com/news/wall-st-futures-steady-investors-100441649.html) already exists.'}
INFO:scripts.run_news_collector:
新聞收集任務成功完成。
INFO:scripts.run_news_collector:  - 總共處理: 85 篇文章
INFO:scripts.run_news_collector:  - 新增文章: 0 篇
INFO:scripts.run_news_collector:  - 重複文章: 0 篇
INFO:scripts.run_news_collector:  - 處理失敗: 85 篇
INFO:scripts.run_news_collector: