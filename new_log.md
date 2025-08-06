PS D:\AI\finnews-bot> python scripts/test_scraper_collection.py
============================================================
臨時測試腳本：驗證 scraper.py 的 collect_news_from_topics
============================================================        
[INFO] 將對以下 1 個主題進行測試爬取，每個主題最多處理 2 篇文章：   
  - 主題: TECH, URL: https://finance.yahoo.com/topic/tech

--- [INFO] 開始處理主題: TECH ---
[SCRAPE] 正在從 https://finance.yahoo.com/topic/tech 爬取新聞列表...
[SUCCESS] 成功爬取到 45 則新聞標題。
INFO:httpx:HTTP Request: GET https://gbobozzqoqfhqmttwzwn.supabase.co/rest/v1/news_articles?select=id&original_url=eq.https%3A%2F%2Ffinance.yahoo.com%2Fnews%2Fambiq-micro-stock-pops-ipo-050000409.html 
"HTTP/2 200 OK"
[SKIP] 文章已處理過: Ambiq Micro Stock Pops on IPO Debut: What's Fuelin...
INFO:httpx:HTTP Request: GET https://gbobozzqoqfhqmttwzwn.supabase.co/rest/v1/news_articles?select=id&original_url=eq.https%3A%2F%2Ffinance.yahoo.com%2Fnews%2Fjeh-aerospace-nets-11m-scale-003000739.html "HTTP/2 200 OK"
[PROCESS] 正在處理新文章: Jeh Aerospace nets $11M to scale the commercial ai...
[SELENIUM] 正在啟動瀏覽器抓取: https://finance.yahoo.com/news/jeh-aerospace-nets-11m-scale-003000739....

DevTools listening on ws://127.0.0.1:1309/devtools/browser/a71008ba-2b6c-45f8-88e1-bf3864092a3c
[18048:14684:0805/140416.063:ERROR:net\socket\ssl_client_socket_impl.cc:896] handshake failed; returned -1, SSL error code 1, net_error -200
[18048:14684:0805/140418.395:ERROR:net\socket\ssl_client_socket_impl.cc:896] handshake failed; returned -1, SSL error code 1, net_error -101
[18048:14684:0805/140419.043:ERROR:net\socket\ssl_client_socket_impl.cc:896] handshake failed; returned -1, SSL error code 1, net_error -200
[18048:14684:0805/140419.138:ERROR:net\socket\ssl_client_socket_impl.cc:896] handshake failed; returned -1, SSL error code 1, net_error -201
[18048:14684:0805/140437.561:ERROR:net\socket\ssl_client_socket_impl.cc:896] handshake failed; returned -1, SSL error code 1, net_error -200
[8436:520:0805/140445.813:ERROR:gpu\command_buffer\service\gles2_cmd_decoder_passthrough.cc:1095] [GroupMarkerNotSet(crbug.com/242999)!:A040BB001C390000]Automatic fallback to software WebGL has been deprecated. Please use the --enable-unsafe-swiftshader (about:flags#enable-unsafe-swiftshader) flag to opt in to lower security guarantees for trusted content.
WARNING: All log messages before absl::InitializeLog() is called are written to STDERR
I0000 00:00:1754373889.672840    8076 voice_transcription.cc:58] Registering VoiceTranscriptionCapability
[35572:10760:0805/140449.956:ERROR:google_apis\gcm\engine\registration_request.cc:291] Registration response error message: DEPRECATED_ENDPOINT
Created TensorFlow Lite XNNPACK delegate for CPU.
[SUCCESS] 成功擷取文章內文，約 6207 字。
📅 設定文章發布時間為當前時間: 2025-08-05 14:05:05 (UTC+8)
DEBUG: Inside _process_single_article - Type of news_item['link']: <class 'str'>
DEBUG: Inside _process_single_article - Type of tags: <class 'list'>
INFO:httpx:HTTP Request: POST https://gbobozzqoqfhqmttwzwn.supabase.co/rest/v1/news_articles "HTTP/2 201 Created"
[OK] 儲存成功: Jeh Aerospace nets $11M to scale the commercial aircraft supply chain in India
[SUCCESS] 新文章已儲存，ID: 64
INFO:httpx:HTTP Request: GET https://gbobozzqoqfhqmttwzwn.supabase.co/rest/v1/news_articles?select=id&original_url=eq.https%3A%2F%2Ffinance.yahoo.com%2Fnews%2Fveteran-fund-manager-raises-eyebrows-224522166.html "HTTP/2 200 OK"
[PROCESS] 正在處理新文章: Veteran fund manager raises eyebrows with Palantir...
[SELENIUM] 正在啟動瀏覽器抓取: https://finance.yahoo.com/news/veteran-fund-manager-raises-eyebrows-22...

DevTools listening on ws://127.0.0.1:1731/devtools/browser/36274f7a-ea92-4438-bbe3-3e34eba64a86
[17516:27340:0805/140514.499:ERROR:net\socket\ssl_client_socket_impl.cc:896] handshake failed; returned -1, SSL error code 1, net_error -200
[17516:27340:0805/140514.541:ERROR:net\socket\ssl_client_socket_impl.cc:896] handshake failed; returned -1, SSL error code 1, net_error -101
[17516:27340:0805/140516.703:ERROR:net\socket\ssl_client_socket_impl.cc:896] handshake failed; returned -1, SSL error code 1, net_error -201
[31496:35196:0805/140536.548:ERROR:gpu\command_buffer\service\gles2_cmd_decoder_passthrough.cc:1095] [GroupMarkerNotSet(crbug.com/242999)!:A000A700EC770000]Automatic fallback to software WebGL has been deprecated. Please use the --enable-unsafe-swiftshader (about:flags#enable-unsafe-swiftshader) flag to opt in to lower security guarantees for trusted content.
[17516:27340:0805/140540.370:ERROR:net\socket\ssl_client_socket_impl.cc:896] handshake failed; returned -1, SSL error code 1, net_error -200
[17516:27340:0805/140540.386:ERROR:net\socket\ssl_client_socket_impl.cc:896] handshake failed; returned -1, SSL error code 1, net_error -101
[17516:27340:0805/140540.976:ERROR:net\socket\ssl_client_socket_impl.cc:896] handshake failed; returned -1, SSL error code 1, net_error -201
[ERROR] 擷取內文時發生錯誤: Message: timeout: Timed out receiving message from renderer: 39.450
  (Session info: chrome=138.0.7204.158)
Stacktrace:
        GetHandleVerifier [0x0x7ff692ffe415+77285]
        GetHandleVerifier [0x0x7ff692ffe470+77376]
        (No symbol) [0x0x7ff692dc9a6a]
        (No symbol) [0x0x7ff692db73ac]
        (No symbol) [0x0x7ff692db709a]
        (No symbol) [0x0x7ff692db4c68]
        (No symbol) [0x0x7ff692db56cf]
        (No symbol) [0x0x7ff692dc42ee]
        (No symbol) [0x0x7ff692dda2b1]
        (No symbol) [0x0x7ff692de141a]
        (No symbol) [0x0x7ff692db5e6d]
        (No symbol) [0x0x7ff692dd9f08]
        (No symbol) [0x0x7ff692e70bb8]
        (No symbol) [0x0x7ff692e483e3]
        (No symbol) [0x0x7ff692e11521]
        (No symbol) [0x0x7ff692e122b3]
        GetHandleVerifier [0x0x7ff6932e1efd+3107021]
        GetHandleVerifier [0x0x7ff6932dc29d+3083373]
        GetHandleVerifier [0x0x7ff6932fbedd+3213485]
        GetHandleVerifier [0x0x7ff69301884e+184862]
        GetHandleVerifier [0x0x7ff69302055f+216879]
        GetHandleVerifier [0x0x7ff693007084+113236]
        GetHandleVerifier [0x0x7ff693007239+113673]
        GetHandleVerifier [0x0x7ff692fee298+11368]
        BaseThreadInitThunk [0x0x7ffa97a37374+20]
        RtlUserThreadStart [0x0x7ffa97cdcc91+33]

INFO:httpx:HTTP Request: GET https://gbobozzqoqfhqmttwzwn.supabase.co/rest/v1/news_articles?select=id&original_url=eq.https%3A%2F%2Ffinance.yahoo.com%2Fnews%2Ftech-industry-insiders-share-picks-224010241.html "HTTP/2 200 OK"
[PROCESS] 正在處理新文章: Tech industry insiders share their picks for the n...
[SELENIUM] 正在啟動瀏覽器抓取: https://finance.yahoo.com/news/tech-industry-insiders-share-picks-2240...

DevTools listening on ws://127.0.0.1:2225/devtools/browser/66d2fb72-803c-452a-9301-9d6b088d1a68
[37820:22796:0805/140559.134:ERROR:gpu\command_buffer\service\gles2_cmd_decoder_passthrough.cc:1095] [GroupMarkerNotSet(crbug.com/242999)!:A0C03D00EC200000]Automatic fallback to software WebGL has been deprecated. Please use the --enable-unsafe-swiftshader (about:flags#enable-unsafe-swiftshader) flag to opt in to lower security guarantees for trusted content.
[7344:9112:0805/140601.466:ERROR:net\socket\ssl_client_socket_impl.cc:896] handshake failed; returned -1, SSL error code 1, net_error -101
[7344:9112:0805/140602.516:ERROR:net\socket\ssl_client_socket_impl.cc:896] handshake failed; returned -1, SSL error code 1, net_error -201
[37820:22796:0805/140621.827:ERROR:gpu\command_buffer\service\gles2_cmd_decoder_passthrough.cc:1095] [GroupMarkerNotSet(crbug.com/242999)!:A0F03D00EC200000]Automatic fallback to software WebGL has been deprecated. Please use the --enable-unsafe-swiftshader (about:flags#enable-unsafe-swiftshader) flag to opt in to lower security guarantees for trusted content.
[37820:22796:0805/140623.439:ERROR:gpu\command_buffer\service\gles2_cmd_decoder_passthrough.cc:1095] [GroupMarkerNotSet(crbug.com/242999)!:A0C03D00EC200000]Automatic fallback to software WebGL has been deprecated. Please use the --enable-unsafe-swiftshader (about:flags#enable-unsafe-swiftshader) flag to opt in to lower security guarantees for trusted content.
[SUCCESS] 成功擷取文章內文，約 6541 字。
📅 設定文章發布時間為當前時間: 2025-08-05 14:06:41 (UTC+8)
DEBUG: Inside _process_single_article - Type of news_item['link']: <class 'str'>
DEBUG: Inside _process_single_article - Type of tags: <class 'list'>
INFO:httpx:HTTP Request: POST https://gbobozzqoqfhqmttwzwn.supabase.co/rest/v1/news_articles "HTTP/2 201 Created"
[OK] 儲存成功: Tech industry insiders share their picks for the next startups who will ride the IPO wave after Figma’s blockbuster debut
[SUCCESS] 新文章已儲存，ID: 65
[INFO] 已達到主題 TECH 的處理上限 (2 篇文章)，跳過剩餘文章。

[SUCCESS] collect_news_from_topics 測試執行成功！
  - 總共處理: 4 篇文章
  - 新增文章: 2 篇
  - 重複文章: 1 篇
  - 處理失敗: 1 篇

============================================================
測試腳本結束
============================================================