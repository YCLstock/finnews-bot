# 🚀 FinNews-Bot 系統說明手冊 v3.0

> **最新版本**: 2025-08-02  
> **架構**: Render Cloud API + 本地排程服務 + Supabase 資料庫  
> **特色**: OpenAI 語義分析 + 用戶引導系統 + 智能推送

---

## 📋 目錄

1. [系統架構概覽](#系統架構概覽)
2. [核心功能說明](#核心功能說明)
3. [檔案結構與責任](#檔案結構與責任)
4. [爬蟲排程系統](#爬蟲排程系統)
5. [關鍵字系統詳解](#關鍵字系統詳解)
6. [用戶引導系統](#用戶引導系統)
7. [推送系統](#推送系統)
8. [API 端點說明](#api-端點說明)
9. [部署與維護](#部署與維護)
10. [故障排除](#故障排除)

---

## 🏗️ 系統架構概覽

### **整體架構圖**
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  前端 (Vercel)   │────│  後端 API (Render) │────│ 資料庫 (Supabase) │
│  Next.js 15     │    │  FastAPI         │    │  PostgreSQL     │
│  用戶界面        │    │  用戶引導 API     │    │  用戶資料        │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                    ┌─────────┴─────────┐
                    │                   │
          ┌─────────▼────────┐ ┌────────▼─────────┐
          │  本地爬蟲服務      │ │  本地推送服務      │
          │  新聞資料收集      │ │  Discord 推送     │
          │  關鍵字分析       │ │  個人化摘要       │
          └──────────────────┘ └──────────────────┘
```

### **技術棧**
- **前端**: Next.js 15 + React 19 + TypeScript + Tailwind CSS
- **後端**: FastAPI + Python 3.9 + OpenAI API
- **資料庫**: Supabase (PostgreSQL)
- **部署**: Vercel (前端) + Render (後端)
- **推送**: Discord Webhooks
- **AI**: OpenAI Embeddings API (text-embedding-ada-002)

---

## ⚙️ 核心功能說明

### **1. 新聞爬蟲與收集**
- **Yahoo Finance 新聞爬蟲**: 自動收集財經新聞
- **AI 標籤分析**: 使用 AI 自動標記新聞類別
- **重複過濾**: 避免推送重複內容
- **多語言摘要**: 支援繁中、簡中、英文摘要

### **2. 用戶引導系統** ⭐ **新功能**
- **智能引導**: 3-5 分鐘完成個人化設定
- **投資領域選擇**: 6 大投資領域 (加密貨幣、科技股等)
- **關鍵字優化**: AI 語義分析 + 聚焦度評分
- **個人化建議**: 根據用戶行為提供優化建議

### **3. 智能推送系統**
- **個人化推送**: 基於用戶關鍵字和興趣
- **頻率控制**: 每日 1-3 次推送
- **AI 摘要**: OpenAI 生成個人化摘要
- **Discord 整合**: 透過 Webhook 推送到 Discord

### **4. 關鍵字管理**
- **語義聚類**: OpenAI Embeddings API 分析關鍵字相關性
- **聚焦度評分**: 0-1 分數衡量關鍵字集中度
- **智能建議**: AI 提供關鍵字優化建議
- **備援機制**: 規則分析作為 AI 備援

---

## 📁 檔案結構與責任

### **🔥 主要服務檔案**

| 檔案路徑 | 主要功能 | 負責內容 |
|---------|---------|----------|
| `api/main.py` | **FastAPI 主應用** | HTTP 服務、路由註冊、CORS 設定 |
| `scripts/run_scraper.py` | **新聞爬蟲主程式** | Yahoo Finance 爬蟲、排程執行 |
| `scripts/run_smart_pusher.py` | **智能推送主程式** | 個人化推送、Discord 發送 |
| `core/user_guidance.py` | **用戶引導系統** | 引導流程、AI 分析、聚焦度計算 |
| `core/semantic_clustering.py` | **語義聚類引擎** | OpenAI API、關鍵字分析 |

### **📊 API 端點檔案**

| 檔案路徑 | API 路由 | 負責功能 |
|---------|---------|----------|
| `api/endpoints/guidance.py` | `/api/v1/guidance/*` | 用戶引導、AI 分析 API |
| `api/endpoints/subscriptions.py` | `/api/v1/subscriptions/*` | 訂閱管理、關鍵字設定 |
| `api/endpoints/history.py` | `/api/v1/history/*` | 推送歷史、統計分析 |
| `api/endpoints/tags.py` | `/api/v1/tags/*` | 標籤管理、新聞分類 |
| `api/auth.py` | **JWT 認證模組** | 用戶認證、權限驗證 |

### **🧠 核心業務邏輯**

| 檔案路徑 | 負責功能 | 詳細說明 |
|---------|---------|----------|
| `core/database.py` | **資料庫操作** | Supabase 連接、CRUD 操作 |
| `core/enhanced_topics_mapper.py` | **Topics 映射** | 新聞分類、標籤對應 |
| `core/tag_manager.py` | **標籤管理** | AI 標籤分析、關鍵字映射 |
| `core/utils.py` | **通用工具** | 文本處理、時間格式化 |
| `core/config.py` | **設定管理** | 環境變數、配置驗證 |

### **🔄 排程服務檔案**

| 檔案路徑 | 執行頻率 | 負責功能 |
|---------|---------|----------|
| `scripts/run_news_collector.py` | **每 30 分鐘** | 收集新聞、存入資料庫 |
| `scripts/run_keyword_sync.py` | **每 1 小時** | 同步關鍵字、更新映射 |

---

## 🕒 爬蟲排程系統

### **排程架構**
```
本地排程服務 (Windows Task Scheduler / Cron)
│
├── 新聞收集 (30分鐘) ── scripts/run_scraper.py
│   ├── Yahoo Finance 爬蟲
│   ├── 新聞去重
│   ├── AI 標籤分析
│   └── 存入 Supabase
│
├── 關鍵字同步 (1小時) ── scripts/run_keyword_sync.py
│   ├── 更新關鍵字映射
│   ├── 語義聚類分析
│   └── Topics 更新
│
└── 智能推送 (用戶設定) ── scripts/run_smart_pusher.py
    ├── 檢查推送時間窗口
    ├── 個人化內容篩選
    ├── OpenAI 摘要生成
    └── Discord 推送
```

### **詳細排程設定**

#### **1. 新聞爬蟲** (`scripts/run_scraper.py`)
```python
# 執行頻率: 每 30 分鐘
# 負責檔案: scripts/run_scraper.py
# 主要流程:
1. 連接 Yahoo Finance RSS
2. 解析新聞內容
3. AI 標籤分析 (core/tag_manager.py)
4. 去重檢查
5. 存入 news_articles 表
6. 記錄執行日誌
```

**設定範例 (Windows)**:
```batch
# Windows Task Scheduler
python D:\AI\finnews-bot\scripts\run_scraper.py
# 觸發器: 每 30 分鐘重複
```

#### **2. 智能推送** (`scripts/run_smart_pusher.py`)
```python
# 執行頻率: 每小時檢查一次
# 負責檔案: scripts/run_smart_pusher.py
# 主要流程:
1. 檢查活躍訂閱用戶
2. 計算推送時間窗口
3. 個人化內容篩選
4. OpenAI 摘要生成
5. Discord Webhook 推送
6. 更新推送歷史
```

#### **3. 關鍵字同步** (`scripts/run_keyword_sync.py`)
```python
# 執行頻率: 每小時
# 負責檔案: scripts/run_keyword_sync.py
# 主要流程:
1. 同步用戶關鍵字
2. 更新關鍵字映射
3. 語義聚類分析
4. Topics 映射更新
```

---

## 🔑 關鍵字系統詳解

### **關鍵字處理流程**
```
用戶輸入關鍵字
        │
        ▼
語義分析 (core/semantic_clustering.py)
        │
        ├── OpenAI Embeddings API ────── 主要方法
        │   ├── 生成語義向量
        │   ├── 計算相似度矩陣  
        │   ├── DBSCAN 聚類
        │   └── 聚焦度評分 (0-1)
        │
        └── 規則分析 ────────────────── 備援方法
            ├── 關鍵字匹配
            ├── Topics 分組
            └── 簡化聚焦度
        │
        ▼
Topics 映射 (core/enhanced_topics_mapper.py)
        │
        ├── 12 個預定義 Topics
        ├── 語義相似度匹配
        └── 個人化建議生成
        │
        ▼
存入資料庫 (subscriptions 表)
```

### **聚焦度評分算法**

**檔案**: `core/semantic_clustering.py` 的 `_calculate_focus_score()` 方法

```python
聚焦度計算公式:
focus_score = (平均聚類內相似度 + 聚類分離度 + 覆蓋度) / 3

評分標準:
- 0.8-1.0: 非常聚焦 (優秀)
- 0.6-0.8: 良好聚焦 (良好)  
- 0.4-0.6: 一般聚焦 (需優化)
- 0.0-0.4: 分散聚焦 (建議重設)
```

### **關鍵字優化建議**

**檔案**: `core/user_guidance.py` 的 `_generate_optimization_suggestions()` 方法

| 聚焦度範圍 | 建議類型 | 具體建議 |
|-----------|---------|----------|
| 0.8-1.0 | 維持現狀 | 關鍵字設定良好，無需調整 |
| 0.6-0.8 | 微調優化 | 移除1-2個相關性低的關鍵字 |
| 0.4-0.6 | 重點優化 | 聚焦到2-3個主要投資領域 |
| 0.0-0.4 | 重新設定 | 建議重新進行引導流程 |

---

## 🎯 用戶引導系統

### **引導流程架構**

**檔案**: `core/user_guidance.py` + `api/endpoints/guidance.py`

```
新用戶註冊
        │
        ▼
步驟1: 歡迎介紹 (start_user_onboarding)
        │
        ▼  
步驟2: 投資領域選擇 (process_investment_focus_selection)
        │
        ├── 6大投資領域多選:
        │   ├── crypto (加密貨幣)
        │   ├── tech_stocks (科技股)
        │   ├── traditional_stocks (傳統股票)
        │   ├── real_estate (房地產)
        │   ├── economy_policy (經濟政策)
        │   └── business_news (商業新聞)
        │
        ▼
步驟3: 關鍵字自訂 (analyze_user_keywords)
        │
        ├── 基於選擇推薦關鍵字
        ├── 用戶自訂關鍵字
        └── OpenAI 語義分析
        │
        ▼
步驟4: AI 分析結果 (finalize_user_onboarding)
        │
        ├── 聚焦度評分
        ├── 聚類結果展示
        ├── 個人化建議
        └── 完成設定
```

### **投資領域配置**

**檔案**: `core/user_guidance.py` 中的 `INVESTMENT_FOCUS_CONFIG`

```python
INVESTMENT_FOCUS_CONFIG = {
    "crypto": {
        "name": "加密貨幣",
        "keywords": ["比特幣", "以太坊", "加密貨幣", "區塊鏈", "數位資產"],
        "description": "Bitcoin、Ethereum 等數位貨幣投資"
    },
    "tech_stocks": {
        "name": "科技股",  
        "keywords": ["蘋果", "微軟", "特斯拉", "輝達", "科技股"],
        "description": "Apple、Microsoft、Tesla 等科技公司股票"
    },
    # ... 其他領域配置
}
```

### **引導 API 端點**

**檔案**: `api/endpoints/guidance.py`

| API 端點 | HTTP 方法 | 功能說明 |
|---------|---------|----------|
| `/api/v1/guidance/status` | GET | 獲取用戶引導狀態 |
| `/api/v1/guidance/start-onboarding` | POST | 開始引導流程 |
| `/api/v1/guidance/investment-focus` | POST | 處理投資領域選擇 |
| `/api/v1/guidance/analyze-keywords` | POST | AI 關鍵字分析 |
| `/api/v1/guidance/finalize-onboarding` | POST | 完成引導設定 |
| `/api/v1/guidance/optimization-suggestions` | GET | 獲取優化建議 |

---

## 📨 推送系統

### **推送流程架構**

**檔案**: `scripts/run_smart_pusher.py`

```
推送檢查 (每小時執行)
        │
        ▼
1. 獲取活躍訂閱 (core/database.py)
        │
        ├── 檢查 is_active = true
        ├── 檢查推送時間窗口
        └── 計算上次推送時間間隔
        │
        ▼
2. 個人化內容篩選
        │
        ├── 關鍵字匹配
        ├── Tags 匹配  
        ├── 時間範圍篩選
        └── 去重過濾
        │
        ▼
3. AI 摘要生成 (OpenAI API)
        │
        ├── 文章內容分析
        ├── 個人化摘要
        ├── 多語言支援
        └── 格式化輸出
        │
        ▼
4. Discord 推送
        │
        ├── Webhook 發送
        ├── 錯誤處理
        └── 更新推送歷史
```

### **推送頻率控制**

**檔案**: `core/database.py` 中的推送邏輯

| 頻率設定 | 英文代碼 | 推送間隔 | 推送時間 |
|---------|---------|---------|----------|
| 每日一次 | `daily` | 24 小時 | 上午 9:00 |
| 每日兩次 | `twice` | 12 小時 | 上午 9:00, 下午 6:00 |
| 每日三次 | `thrice` | 8 小時 | 上午 9:00, 下午 2:00, 晚上 8:00 |

### **推送內容模板**

**檔案**: `scripts/run_smart_pusher.py` 中的 `format_discord_message()` 方法

```markdown
🚨 **{用戶名稱}** 的財經新聞摘要 📊

📅 **推送時間**: {時間戳記}
🔍 **匹配關鍵字**: {關鍵字列表}

📰 **新聞摘要**:
{OpenAI 生成的個人化摘要}

🔗 **原始連結**: {新聞連結}

---
⚙️ 管理訂閱: {前端連結}
```

---

## 🌐 API 端點說明

### **認證系統**

**檔案**: `api/auth.py`

```python
# JWT 認證流程
1. Supabase Auth 發放 JWT Token
2. 前端在 Authorization Header 傳送 Token  
3. JWTVerifier 驗證 Token 有效性
4. 解析 user_id 用於 API 操作
```

### **完整 API 文檔**

| 分類 | 端點 | 方法 | 功能 | 負責檔案 |
|-----|------|------|------|---------|
| **認證** | `/api/v1/health` | GET | 健康檢查 | `api/main.py` |
| **認證** | `/api/v1/config` | GET | 客戶端配置 | `api/main.py` |
| | | | | |
| **用戶引導** | `/api/v1/guidance/status` | GET | 引導狀態 | `api/endpoints/guidance.py` |
| **用戶引導** | `/api/v1/guidance/start-onboarding` | POST | 開始引導 | `api/endpoints/guidance.py` |
| **用戶引導** | `/api/v1/guidance/investment-focus` | POST | 投資領域選擇 | `api/endpoints/guidance.py` |
| **用戶引導** | `/api/v1/guidance/analyze-keywords` | POST | 關鍵字分析 | `api/endpoints/guidance.py` |
| **用戶引導** | `/api/v1/guidance/finalize-onboarding` | POST | 完成引導 | `api/endpoints/guidance.py` |
| **用戶引導** | `/api/v1/guidance/optimization-suggestions` | GET | 優化建議 | `api/endpoints/guidance.py` |
| | | | | |
| **訂閱管理** | `/api/v1/subscriptions` | GET | 獲取訂閱 | `api/endpoints/subscriptions.py` |
| **訂閱管理** | `/api/v1/subscriptions` | POST | 創建訂閱 | `api/endpoints/subscriptions.py` |
| **訂閱管理** | `/api/v1/subscriptions` | PUT | 更新訂閱 | `api/endpoints/subscriptions.py` |
| **訂閱管理** | `/api/v1/subscriptions/toggle` | POST | 切換狀態 | `api/endpoints/subscriptions.py` |
| | | | | |
| **推送歷史** | `/api/v1/history` | GET | 推送歷史 | `api/endpoints/history.py` |
| **推送歷史** | `/api/v1/history/stats` | GET | 推送統計 | `api/endpoints/history.py` |
| | | | | |
| **標籤管理** | `/api/v1/tags` | GET | 所有標籤 | `api/endpoints/tags.py` |
| **標籤管理** | `/api/v1/tags/active` | GET | 活躍標籤 | `api/endpoints/tags.py` |

---

## 🚀 部署與維護

### **環境變數設定**

**檔案**: `.env` (參考 `env_example.txt`)

```bash
# Supabase 設定
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-key
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_JWT_SECRET=your-jwt-secret

# OpenAI API
OPENAI_API_KEY=sk-proj-your-openai-key

# API 設定  
API_HOST=0.0.0.0
API_PORT=8000
SECRET_KEY=your-secret-key

# 爬蟲設定
SCRAPER_TIMEOUT=40
MAX_RETRIES=3
DEBUG=false
```

### **部署檢查清單**

#### **Render 後端部署**
- [ ] 環境變數已設定
- [ ] `requirements.txt` 已更新
- [ ] `render.yaml` 設定正確
- [ ] 健康檢查端點可存取
- [ ] OpenAI API 金鑰有效

#### **Vercel 前端部署**  
- [ ] `NEXT_PUBLIC_API_URL` 指向 Render URL
- [ ] Supabase 環境變數已設定
- [ ] 新頁面路由正常
- [ ] 引導流程可存取

#### **本地排程服務**
- [ ] Python 環境已設定
- [ ] 排程任務已建立
- [ ] 日誌記錄正常
- [ ] 錯誤監控啟用

### **監控要點**

| 監控項目 | 檢查頻率 | 負責檔案 | 關鍵指標 |
|---------|---------|---------|----------|
| API 健康狀態 | 每 5 分鐘 | `api/main.py` | HTTP 200 回應 |
| 爬蟲執行狀態 | 每 30 分鐘 | `scripts/run_scraper.py` | 新聞收集數量 |
| 推送成功率 | 每小時 | `scripts/run_smart_pusher.py` | Discord 推送成功率 |
| 資料庫連接 | 每 10 分鐘 | `core/database.py` | 連接回應時間 |
| OpenAI API | 每次呼叫 | `core/semantic_clustering.py` | API 回應時間、成功率 |

---

## 🛠️ 故障排除

### **常見問題與解決方案**

#### **1. API 連接問題**

**問題**: 前端無法連接後端 API
```bash
# 檢查步驟:
1. 確認 Render 服務運行中
2. 檢查 CORS 設定 (api/main.py)
3. 驗證環境變數 NEXT_PUBLIC_API_URL
4. 測試健康檢查端點: GET /api/v1/health
```

**負責檔案**: `api/main.py`, `api/endpoints/*`

#### **2. OpenAI API 問題**

**問題**: 語義分析失敗
```bash
# 檢查步驟:
1. 驗證 OPENAI_API_KEY 有效性
2. 檢查 API 使用額度
3. 查看錯誤日誌
4. 確認備援機制啟動
```

**負責檔案**: `core/semantic_clustering.py`

#### **3. 爬蟲停止運行**

**問題**: 新聞收集中斷
```bash
# 檢查步驟:
1. 檢查排程任務運行狀態
2. 驗證網路連接
3. 檢查 Yahoo Finance RSS 可用性
4. 查看爬蟲日誌檔案
```

**負責檔案**: `scripts/run_scraper.py`

#### **4. Discord 推送失敗**

**問題**: Discord 訊息未送達
```bash
# 檢查步驟:
1. 驗證 Discord Webhook URL
2. 檢查 Discord 伺服器狀態
3. 確認推送頻率設定
4. 查看推送歷史記錄
```

**負責檔案**: `scripts/run_smart_pusher.py`

#### **5. 資料庫連接問題**

**問題**: Supabase 連接失敗
```bash
# 檢查步驟:
1. 驗證 Supabase 憑證
2. 檢查資料庫可用性
3. 確認網路連接
4. 查看資料庫日誌
```

**負責檔案**: `core/database.py`

### **日誌檔案位置**

| 服務 | 日誌檔案 | 內容 |
|-----|---------|------|
| Render API | Render Dashboard | HTTP 請求、錯誤日誌 |
| 本地爬蟲 | `logs/scraper.log` | 爬蟲執行記錄 |
| 本地推送 | `logs/pusher.log` | 推送執行記錄 |
| 前端 | Vercel Dashboard | 部署、運行日誌 |

---

## 📊 效能指標

### **系統效能基準**

| 指標 | 目標值 | 監控方法 |
|-----|-------|---------|
| API 回應時間 | < 500ms | Render 監控 |
| 新聞爬取效率 | 每次 > 10 篇 | 爬蟲日誌 |
| 推送成功率 | > 95% | Discord API 回應 |
| 聚焦度計算 | < 2 秒 | OpenAI API 回應時間 |
| 用戶引導完成率 | > 80% | 前端分析 |

### **資源使用監控**

- **Render**: CPU < 80%, 記憶體 < 1GB
- **Supabase**: 連接數 < 60, 查詢時間 < 100ms  
- **OpenAI**: 每月 Token 使用量監控
- **Discord**: Webhook 呼叫頻率限制

---

## 📞 技術支援

### **開發團隊聯繫**

- **系統架構**: 檢查 `SYSTEM_MANUAL_FINAL.md`
- **API 文檔**: 檢查 `api/endpoints/` 目錄
- **問題回報**: GitHub Issues

### **更新履歷**

- **v3.0** (2025-08-02): 新增用戶引導系統、OpenAI 整合
- **v2.1** (2025-07-31): 語義聚類、聚焦度評分
- **v2.0** (2025-07-28): Render 部署、FastAPI 重構

---

**📝 文檔最後更新**: 2025-08-02  
**🔄 系統版本**: v3.0  
**👨‍💻 維護者**: FinNews-Bot 開發團隊