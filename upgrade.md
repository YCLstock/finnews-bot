### **FinNews-Bot 智慧推送升級計畫書**

**文件版本**: 1.0
**日期**: 2025-08-04

#### **1. 總體目標**

本次升級的核心目標是將 FinNews-Bot 從一個**被動的「關鍵字過濾器」**，轉變為一個**主動的、由用戶需求驅動的「智慧資訊供應鏈」**。我們將透過啟用並整合系統中已存在但閒置的「大腦」模組 (`topics_mapper`) 和「AI 標籤」資產，實現以下價值：

*   **提升精準度**：透過語義理解，準確過濾掉字面匹配但語義無關的噪聲新聞。
*   **提升全面性**：透過關聯分析，主動發掘沒有直接關鍵字但用戶可能高度感興趣的重要新聞。
*   **提升靈活性**：優雅地處理用戶設定的、超出系統預定義範圍的冷門或新潮關鍵字。
*   **提升系統效率**：為下一階段的「智能爬取」奠定基礎，從源頭上提升資訊獲取的相關性。

#### **2. 核心架構升級：混合評分引擎 (Hybrid Scoring Engine)**

我們將在推送流程中引入一個全新的核心元件：**混合評分引擎**。此引擎將取代現有的、單純的「字串包含」判斷邏輯。

其核心評分公式如下：

`最終關聯性分數 = (標籤匹配分數 * 0.7) + (關鍵字匹配分數 * 0.3)`

*   **標籤匹配分數 (Tag Score)**：代表系統對文章**語義**的理解，權重高。
*   **關鍵字匹配分數 (Keyword Score)**：代表對用戶**原始輸入**的尊重，作為補充和處理未知情況的「安全網」，權重低。

#### **3. 實施階段與步驟**

**第一階段：推送器智能化升級 (Pusher Intelligence Upgrade)**

此階段的目標是讓推送器「學會思考」，能夠利用 AI 標籤和用戶意圖進行智慧篩選。

*   **涉及的主要檔案**: `scripts/run_smart_pusher.py`
*   **涉及的輔助檔案**: `core/topics_mapper.py` (被呼叫)

**修改步驟詳解：**

1.  **步驟 1.1: 引入依賴與修改主流程**
    *   **檔案**: `scripts/run_smart_pusher.py`
    *   **修改描述**:
        *   在檔案頂部，引入 `from core.topics_mapper import topics_mapper`。
        *   修改 `SmartPusher` 類中的主要文章選擇方法 (例如 `select_articles_by_preference` 或 `get_eligible_articles_for_user`)。舊的邏輯是直接遍歷文章比對關鍵字，新的邏輯將改為：
            1.  呼叫一個新函式，將用戶的原始關鍵字轉化為標準化的「興趣主題」。
            2.  對每一篇候選文章，呼叫另一個新函式來計算其「最終關聯性分數」。
            3.  根據計算出的分數進行排序，並選出分數最高的 N 篇文章。

2.  **步驟 1.2: 新增「用戶意圖轉化」函式**
    *   **檔案**: `scripts/run_smart_pusher.py`
    *   **建議函式名**: `_get_user_interest_topics(self, keywords: list) -> list`
    *   **修改描述**:
        *   此函式接收用戶的原始關鍵字列表 (`keywords`) 作為輸入。
        *   它將呼叫 `topics_mapper.map_keywords_to_topics(keywords)`。
        *   它處理 `topics_mapper` 的返回結果，提取出標準化的主題 Code (例如 `['TECH', 'EARNINGS']`) 並返回。
        *   **關鍵欄位提示**:
            *   輸入: `user_subscriptions['keywords']`
            *   輸出: 一個標準化的 Topic Code 列表，將用於計算 `tag_score`。

3.  **步驟 1.3: 新增「混合評分」核心函式**
    *   **檔案**: `scripts/run_smart_pusher.py`
    *   **建議函式名**: `_calculate_hybrid_score(self, article: dict, user_keywords: list, interest_topics: list) -> float`
    *   **修改描述**:
        *   此函式是評分引擎的核心，接收一篇文章、用戶的原始關鍵字、以及步驟 1.2 產生的「興趣主題」列表。
        *   **計算 `tag_score`**: 比較文章的 AI 標籤 (`article['tags']`) 與用戶的「興趣主題」(`interest_topics`) 的匹配程度。可以計算交集的大小或更複雜的加權分數。
        *   **計算 `keyword_score`**: 沿用舊的邏輯，檢查用戶的原始關鍵字 (`user_keywords`) 是否出現在文章的標題 (`article['title']`) 或摘要 (`article['summary']`) 中。
        *   **計算最終分數**: 套用 `(tag_score * 0.7) + (keyword_score * 0.3)` 公式，返回一個浮點數。
        *   **關鍵欄位提示**:
            *   輸入 (文章): `news_articles['tags']`, `news_articles['title']`, `news_articles['summary']`
            *   輸入 (用戶): `user_subscriptions['keywords']`, 以及步驟 1.2 的結果。
            *   輸出: 關聯性分數 (0.0 ~ 1.0)。

**第二階段：爬蟲智能化升級 (Scraper Intelligence Upgrade) - 未來規劃**

此階段的目標是讓爬蟲從源頭上就抓取更相關的內容。

*   **涉及的主要檔案**: `scraper/scraper.py`, `scripts/run_news_collector.py`
*   **修改描述**:
    *   在爬取任務開始前，分析**所有用戶**的 `keywords`，透過 `topics_mapper` 匯總出一個全站的「主題熱度」分佈圖。
    *   根據此分佈圖，動態生成 Yahoo Finance 的 Topic 頁面 URL (`finance.yahoo.com/topic/TECH` 等) 列表，並分配爬取資源。
    *   爬蟲抓取到的文章，需要將其來源 Topic 存入 `news_articles['topics']` 欄位，以供後續分析。

#### **4. 關鍵資料欄位對應**

為確保端到端資料流的一致性，以下是本次升級涉及的核心欄位對應關係：

| 資料來源 (Source) | 關鍵欄位 (Key Field) | 在新系統中的作用 |
| :--- | :--- | :--- |
| `user_subscriptions` | `keywords` (jsonb) | **輸入**: 用戶的原始偏好設定。用於**意圖轉化**和計算 `keyword_score`。 |
| `user_subscriptions` | `subscribed_tags` (jsonb) | **輸出/中間產物**: 儲存由 `keywords` 轉化而來的標準化興趣主題。 |
| `news_articles` | `tags` (jsonb) | **輸入**: 文章的 AI 標籤。用於計算 `tag_score` 的核心依據。 |
| `news_articles` | `title` (text) | **輸入**: 用於計算 `keyword_score`。 |
| `news_articles` | `summary` (text) | **輸入**: 用於計算 `keyword_score`。 |
| `news_articles` | `topics` (jsonb) | **(未來階段使用)** 記錄文章是從哪個 Yahoo Finance Topic 頁面爬取的。 |

#### **5. 測試計畫**

為確保升級的穩定性和正確性，需要執行以下測試：

1.  **單元測試 (Unit Tests)**:
    *   **對象**: `_get_user_interest_topics` 函式。
    *   **內容**: 測試各種關鍵字組合（包含已知、未知、混合的關鍵字）是否能正確轉化為預期的 Topic 列表。
    *   **對象**: `_calculate_hybrid_score` 函式。
    *   **內容**: 構造各種模擬的文章和用戶偏好，驗證以下場景的評分是否符合預期：
        *   高 `tag_score`, 高 `keyword_score` (完美匹配)
        *   高 `tag_score`, 低 `keyword_score` (語義相關但無直接關鍵字)
        *   低 `tag_score`, 高 `keyword_score` (字面匹配但語義無關，如「蘋果西打」)
        *   低 `tag_score`, 低 `keyword_score` (完全不相關)

2.  **整合測試 (Integration Tests)**:
    *   **對象**: `run_smart_pusher.py` 與 `core/topics_mapper.py` 的協同工作。
    *   **內容**: 確保在 `run_smart_pusher.py` 中呼叫 `topics_mapper` 時，資料的傳入和傳出格式正確，無縫銜接。

3.  **端到端用戶案例測試 (End-to-End User Case Tests)**:
    *   **內容**: 在一個測試環境中，完整地執行一次推送流程。使用我們之前討論過的具體案例進行驗證：
        *   **案例一 (降噪測試)**：用戶關鍵字為「蘋果」，驗證系統是否能推送「蘋果 M4 晶片」新聞，而**過濾掉**「蘋果西打」新聞。
        *   **案例二 (關聯發掘測試)**：用戶關鍵字為「蘋果」，驗證系統是否能推送「庫克談 Vision Pro」這類**沒有直接關鍵字但 AI 標籤相關**的新聞。
        *   **案例三 (超出範圍測試)**：用戶關鍵字為「量子計算」，驗證系統是否依然能透過 `keyword_score` 的保底機制，推送直接包含「量子計算」的文章。

#### **6. 結論**

本計畫旨在透過對 `run_smart_pusher.py` 的核心邏輯進行一次集中、高效的升級，以最小的改動成本，最大化地釋放出現有 AI 標籤和標籤映射系統的潛在價值。計畫的成功實施，將是 FinNews-Bot 邁向真正「智能化」的關鍵第一步。