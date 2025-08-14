  由於我們要在生成摘要時一併翻譯標題，這會影響到資料的儲存和使用方式。因此，正如您所說，我們需要連同資料庫一起修改。

  以下是我們需要執行的完整待辦事項列表 (To-Do List)，涵蓋了從資料庫到最終通知的每一個環節。

  ---

  Phase 1: 資料庫基礎建設

   * 任務 1：為文章新增「翻譯標題」欄位
       * 目標：在資料庫中建立一個地方，專門存放由 AI 翻譯好的中文標題。
       * 動作：我需要先檢查 database_schema.md 來確認文章資料表的確切名稱 (我猜測是 articles)，然後在該資料表中新增一個名為 translated_title 的欄位。
       * SQL 指令範例：ALTER TABLE articles ADD COLUMN translated_title TEXT;
       * 理由：將翻譯結果儲存起來，這樣在每次發送通知時，就不用重複翻譯，能大幅節省 API 成本和處理時間。

  Phase 2: AI 核心邏輯修改

   * 任務 2：修改 AI 處理函式，合併摘要與翻譯任務
       * 目標：修改目前呼叫 OpenAI 的函式，讓它在一次請求中同時完成兩件事。
       * 涉及檔案：很可能是 core/utils.py 或 scraper/scraper.py。
       * 動作：
           1. 重寫 Prompt：設計新的指令，要求 gpt-3.5-turbo 以 JSON 格式，同時回傳「摘要內容」和「翻譯後的標題」。       
           2. 指定輸出格式：在 API 呼叫中，明確要求 response_format={ 'type': 'json_object' }，來提高回傳 JSON 的穩定性。
           3. 修改函式回傳值：讓這個 AI 處理函式，從只回傳一個摘要字串，改為回傳一個包含兩項資訊的字典 (dictionary)。    
           4. 增強錯誤處理：加入邏輯來處理 API 呼叫失敗，或回傳的 JSON 格式不正確的情況。

  Phase 3: 資料儲存流程修改

   * 任務 3：更新儲存文章至資料庫的程式碼
       * 目標：將 AI 產出的新資料（翻譯標題）正確存入資料庫。
       * 涉及檔案：主要是爬蟲或儲存文章的腳本，例如 scraper/scraper.py。
       * 動作：
           1. 修改呼叫 AI 函式的地方，以接收新的字典回傳值。
           2. 從字典中分別取出「摘要」和「翻譯標題」。
           3. 在儲存文章到資料庫時，將 translated_title 一併存入在任務1中新增的欄位。

  Phase 4: 終端通知邏輯修改

   * 任務 4：更新 Discord 通知，使用翻譯後的標題
       * 目標：讓 Discord 通知使用我們新的中文標題，並實現「極簡預覽」。
       * 涉及檔案：core/delivery_manager.py。
       * 動作：
           1. 在發送通知的 send_articles 方法中，修改建立 Discord embed 的邏輯。
           2. 優先使用 translated_title 作為通知的標題。如果這個欄位是空的（例如翻譯失敗或原文就是中文），則退回使用原始的 title。
           3. 將 embed 中的 description 欄位設為空，確保手機預覽只會顯示標題。