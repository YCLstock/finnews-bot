# FinNews-Bot 2.0 🤖📰

智能財經新聞推送系統 - 基於AWS Serverless架構

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com)
[![AWS Lambda](https://img.shields.io/badge/AWS-Lambda-orange.svg)](https://aws.amazon.com/lambda/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 🏗️ 系統架構

```
AWS Lambda(爬蟲+推送) → Supabase(資料庫) → Render(API) → Vercel(前端)
```

### 組件說明
- **AWS Lambda**: 新聞爬蟲 + 智能推送
- **Supabase**: 資料存儲 + 用戶管理  
- **Render**: 後端API服務 (用戶註冊、訂閱管理)
- **Vercel**: 前端界面

**自動化財經新聞摘要推送系統** - 透過 AI 摘要和智能推送頻率控制，讓您不錯過重要財經資訊。

## 🚀 **新功能亮點** (v2.0)

### 📅 **智能推送頻率控制**
- **簡化頻率選項**: 每日一次 / 兩次 / 三次
- **固定推送時間**: 08:00, 13:00, 20:00 (±30分鐘彈性窗口)
- **智能數量控制**: 根據頻率自動調整推送文章數量
- **防重複推送**: 時間窗口標記機制，避免重複推送

### 📦 **批量處理系統**
- **批量收集**: 一次收集多篇符合條件的新聞
- **批量推送**: 分別推送每則新聞，提升用戶體驗
- **失敗處理**: 部分失敗不影響整體，詳細錯誤報告
- **推送間隔**: 自動間隔 1.5 秒，避免 Discord API 限制

### 🔧 **增強後端 API**
- **JWT 本地驗證**: 95%+ 情況下不依賴 Supabase API，性能提升 10-100 倍
- **智能緩存**: Token 和 JWKS 緩存機制，大幅降低 API 調用成本
- **模組化架構**: 完整的 MVC 分層，便於維護和擴展

## 📋 **推送頻率配置**

| 頻率類型 | 推送時間 | 每次文章數 | 適用場景 |
|---------|----------|------------|----------|
| **daily** | 08:00 | 最多 10 篇 | 輕度關注用戶 |
| **twice** | 08:00, 20:00 | 最多 5 篇 | 一般投資用戶 |
| **thrice** | 08:00, 13:00, 20:00 | 最多 3 篇 | 重度投資用戶 |

> 💡 **時間窗口**: 每個推送時間前後 30 分鐘內都可觸發推送

## 🏗️ **系統架構**

```
finnews-bot/
├── 🎯 core/                    # 核心模組
│   ├── config.py              # 配置管理與環境變數
│   ├── database.py            # Supabase 資料庫操作
│   └── utils.py               # OpenAI + Discord 推送工具
├── 🚀 api/                     # FastAPI 後端服務
│   ├── main.py                # API 主程式
│   ├── auth.py                # JWT 認證 (本地驗證優化)
│   └── endpoints/             # RESTful API 端點
│       ├── subscriptions.py   # 訂閱管理 CRUD
│       └── history.py         # 推送歷史查詢
├── 🕷️ scraper/                # 智能爬蟲模組
│   └── scraper.py             # 新聞爬取 + 批量處理
├── ⚙️ run_scraper.py          # 排程執行腳本
└── 🧪 test_batch_push.py      # 功能測試腳本
```

## ⚡ **快速開始 (AWS Lambda 已部署)**

**系統已部署至AWS並自動運行！** 🎉

### 當前部署狀態
- ✅ **爬蟲**: 每4小時自動爬取新聞 (已運行)
- ✅ **推送**: 每10分鐘檢查用戶訂閱 (已運行)
- ✅ **監控**: CloudWatch 自動日誌記錄
- ✅ **環境**: Supabase + OpenAI 已配置

### 立即使用
1. **查看執行狀態**: [AWS Console](https://ap-southeast-1.console.aws.amazon.com/lambda/home?region=ap-southeast-1#/functions)
2. **監控日誌**: CloudWatch > 日誌群組 > `/aws/lambda/finnews-bot-*`
3. **測試功能**: 執行本地測試 `python test_lambda_simple.py`

### 維護指令
```bash
# 查看函數狀態
aws lambda get-function --function-name finnews-bot-crawler --region ap-southeast-1

# 查看最新執行日誌
aws logs tail /aws/lambda/finnews-bot-crawler --follow

# 手動觸發測試
aws lambda invoke --function-name finnews-bot-crawler --payload '{}' response.json
```

---

## 🔧 **環境設定**

### 1. **環境變數配置** (已完成 ✅)

AWS Lambda 環境變數已設定：

```env
# Supabase 資料庫 ✅
SUPABASE_URL=https://gbobozzqoqfhqmttwzwn.supabase.co
SUPABASE_SERVICE_KEY=已設定

# OpenAI API ✅
OPENAI_API_KEY=已設定

# 爬蟲配置 ✅
CRAWLER_LIMIT=10

# 本地開發用 .env 文件：
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-key
SUPABASE_JWT_SECRET=your-jwt-secret
OPENAI_API_KEY=sk-your-openai-key
YAHOO_FINANCE_URL=https://finance.yahoo.com/topic/stock-market-news
SCRAPER_TIMEOUT=30
SCRAPER_USER_AGENT=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36
API_HOST=0.0.0.0
API_PORT=8000
```

### 2. **資料庫結構** (Supabase)

執行以下 SQL 更新您的資料庫結構：

```sql
-- 🔄 更新訂閱表支援新推送頻率
ALTER TABLE subscriptions 
ADD COLUMN push_frequency_type TEXT DEFAULT 'daily' 
CHECK (push_frequency_type IN ('daily', 'twice', 'thrice'));

ALTER TABLE subscriptions 
ADD COLUMN last_push_window TEXT;

-- 🔄 更新推送歷史表支援批量記錄
ALTER TABLE push_history 
ADD COLUMN batch_id TEXT;

-- 📊 添加索引優化查詢
CREATE INDEX IF NOT EXISTS idx_subscriptions_frequency_type 
ON subscriptions(push_frequency_type);

CREATE INDEX IF NOT EXISTS idx_push_history_batch_id 
ON push_history(batch_id);
```

### 3. **依賴安裝**

```bash
pip install -r requirements.txt
```

## 🚀 **使用方式**

### 1. **啟動 API 服務**

```bash
# 開發環境
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# 生產環境
uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 2
```

### 2. **執行智能爬蟲**

```bash
# 立即執行 (檢查當前時間是否符合推送條件)
python run_scraper.py

# 檢查推送狀態 (調試用)
python run_scraper.py --check
```

### 3. **功能測試**

```bash
# 測試批量推送和時間窗口功能
python test_batch_push.py

# 測試 JWT 認證
python test_jwt_auth.py
```

## ⏰ **Cron Job 配置**

### Render 部署 (推薦)

```yaml
# render.yaml
services:
  - type: cron
    name: finnews-bot-scheduler
    env: python
    schedule: "*/10 * * * *"  # 每 10 分鐘檢查一次
    buildCommand: pip install -r requirements.txt
    startCommand: python run_scraper.py
```

### 傳統 Linux Cron

```bash
# 編輯 crontab
crontab -e

# 添加以下行 (每 10 分鐘檢查一次)
*/10 * * * * cd /path/to/finnews-bot && python run_scraper.py
```

## 📊 **API 文檔**

### 訂閱管理

```bash
# 📋 獲取用戶訂閱列表
GET /api/v1/subscriptions
Authorization: Bearer <jwt_token>

# ➕ 創建新訂閱
POST /api/v1/subscriptions
Content-Type: application/json
Authorization: Bearer <jwt_token>

{
  "delivery_target": "https://discord.com/api/webhooks/...",
  "keywords": ["台積電", "聯發科", "股市"],
  "push_frequency_type": "twice"
}

# ✏️ 更新訂閱
PUT /api/v1/subscriptions/{id}
Authorization: Bearer <jwt_token>

{
  "push_frequency_type": "daily",
  "keywords": ["新關鍵字"]
}

# 🔄 切換訂閱狀態
PATCH /api/v1/subscriptions/{id}/toggle
Authorization: Bearer <jwt_token>

# 🗑️ 刪除訂閱
DELETE /api/v1/subscriptions/{id}
Authorization: Bearer <jwt_token>
```

### 推送歷史

```bash
# 📈 獲取推送歷史
GET /api/v1/history?limit=50
Authorization: Bearer <jwt_token>

# 📊 推送統計
GET /api/v1/history/stats
Authorization: Bearer <jwt_token>
```

### 頻率選項

```bash
# 📅 獲取可用推送頻率
GET /api/v1/subscriptions/frequency-options

# 回應範例
{
  "options": [
    {
      "value": "daily",
      "label": "每日一次",
      "description": "每天早上 08:00 推送",
      "times": ["08:00"],
      "max_articles": 10
    }
  ]
}
```

## 🧪 **測試功能**

### 時間窗口測試

```python
# 測試不同時間點的推送判斷
from core.database import db_manager

# 檢查 08:15 是否在 08:00 ±30分鐘窗口內
result = db_manager.is_within_time_window("08:15", "08:00", 30)
print(result)  # True
```

### 批量推送測試

```python
# 模擬批量推送
test_articles = [
    {
        'title': '台積電股價上漲',
        'summary': '台積電今日股價上漲 3%...',
        'original_url': 'https://example.com/news1'
    }
]

success, failed = send_batch_to_discord(webhook_url, test_articles)
```

## 📈 **效能提升**

### JWT 認證優化
- **本地驗證**: 使用 HMAC SHA256 本地驗證 JWT
- **智能緩存**: 5 分鐘 Token 緩存，1 小時 JWKS 緩存
- **成本降低**: Supabase API 調用減少 90%+
- **速度提升**: 認證速度提升 10-100 倍

### 批量處理優化
- **並行處理**: 文章收集與處理並行
- **智能限制**: 根據頻率自動調整處理數量
- **失敗恢復**: 部分失敗不影響其他文章推送

## 🔒 **安全性**

- **JWT 認證**: 完整的使用者身份驗證
- **API 權限**: 用戶只能存取自己的資料
- **環境變數**: 敏感資訊透過環境變數管理
- **CORS 設定**: 限制跨域請求來源

## 🚀 **部署指南**

### 1. **AWS Lambda 部署** (已完成 ✅)

#### 部署狀態
- ✅ **爬蟲Lambda**: `finnews-bot-crawler` (ap-southeast-1)
- ✅ **推送Lambda**: `finnews-bot-pusher` (ap-southeast-1)  
- ✅ **環境變數**: Supabase + OpenAI 配置完成
- ✅ **自動排程**: EventBridge 定時觸發

#### 執行排程
- **爬蟲函數**: 每天 00:00, 04:00, 08:00, 12:00, 16:00, 20:00 (UTC時間)
- **推送函數**: 每10分鐘檢查用戶訂閱並推送

#### 部署配置
```yaml
爬蟲Lambda:
  記憶體: 512MB
  超時: 300秒
  觸發: EventBridge (每4小時)
  
推送Lambda:  
  記憶體: 256MB
  超時: 180秒
  觸發: EventBridge (每10分鐘)
```

### 2. **AWS 後續維護**

#### 監控與日誌
```bash
# 查看函數狀態
aws lambda get-function --function-name finnews-bot-crawler --region ap-southeast-1

# 查看最新日誌
aws logs tail /aws/lambda/finnews-bot-crawler --follow --region ap-southeast-1
aws logs tail /aws/lambda/finnews-bot-pusher --follow --region ap-southeast-1

# 手動測試執行
aws lambda invoke --function-name finnews-bot-crawler --payload '{}' response.json --region ap-southeast-1
```

#### 程式碼更新流程
```bash
# 1. 修改程式碼後，重新部署
cd aws/deploy
./deploy.bat  # Windows
# 或
./deploy.sh   # Linux/Mac

# 2. 或僅更新函數代碼
aws lambda update-function-code \
    --function-name finnews-bot-crawler \
    --zip-file fileb://crawler-deployment.zip \
    --region ap-southeast-1
```

#### 環境變數更新
```bash
# 更新爬蟲環境變數
aws lambda update-function-configuration \
    --function-name finnews-bot-crawler \
    --environment Variables='{"SUPABASE_URL":"新值","OPENAI_API_KEY":"新值"}' \
    --region ap-southeast-1
```

#### 排程調整
```bash
# 修改爬蟲執行頻率 (例改為每2小時)
aws events put-rule \
    --name finnews-crawler-schedule \
    --schedule-expression "rate(2 hours)" \
    --region ap-southeast-1

# 或指定固定時間 (每天6次)
aws events put-rule \
    --name finnews-crawler-schedule \
    --schedule-expression "cron(0 0,4,8,12,16,20 * * ? *)" \
    --region ap-southeast-1
```

### 3. **故障排除**

#### 常見問題
```bash
# 函數超時 - 增加超時時間
aws lambda update-function-configuration \
    --function-name finnews-bot-crawler \
    --timeout 600 \
    --region ap-southeast-1

# 記憶體不足 - 增加記憶體
aws lambda update-function-configuration \
    --function-name finnews-bot-crawler \
    --memory-size 1024 \
    --region ap-southeast-1

# 檢查權限問題
aws iam get-role --role-name finnews-lambda-role
```

#### 監控指標
- **AWS Console**: Lambda > 函數 > 監控
- **CloudWatch**: 自動建立日誌群組
- **EventBridge**: 規則執行狀態

### 4. **本地開發**

```bash
# 克隆專案
git clone https://github.com/yourusername/finnews-bot.git
cd finnews-bot

# 建立虛擬環境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安裝依賴
pip install -r requirements.txt

# 設定環境變數
cp .env.example .env
# 編輯 .env 填入您的設定

# 本地測試Lambda函數
python test_lambda_simple.py

# 啟動API服務 (如需要)
uvicorn api.main:app --reload
```

## 🆕 **版本更新**

### v2.1 (2025-01-20) - AWS Lambda 部署版本
- ✅ **AWS Lambda 部署**: 完整的Serverless架構遷移
- ✅ **雙函數設計**: 爬蟲函數 + 推送函數分離
- ✅ **EventBridge 排程**: 自動化定時執行
- ✅ **環境變數管理**: 安全的配置管理
- ✅ **CloudWatch 監控**: 完整的日誌和監控
- ✅ **部署自動化**: 一鍵部署腳本
- ✅ **故障排除指南**: 完整的維護文檔

### v2.0 (2024-12-xx)
- ✅ 推送頻率簡化 (daily/twice/thrice)
- ✅ 批量處理和推送系統
- ✅ JWT 本地驗證優化
- ✅ 智能時間窗口控制
- ✅ 失敗處理和錯誤恢復
- ✅ 完整的測試套件

### v1.0 (2024-11-xx)
- ✅ 基礎爬蟲功能
- ✅ OpenAI 摘要生成
- ✅ Discord 推送
- ✅ Supabase 資料庫整合

## 📝 **開發計劃**

### 🔄 第二階段: 前端 Web UI
- [ ] Next.js/Vue.js 前端框架
- [ ] 用戶儀表板
- [ ] 訂閱管理界面
- [ ] 推送歷史視覺化
- [ ] 即時通知系統

### 🔄 第三階段: 進階功能
- [ ] 多新聞源支援
- [ ] 個人化推薦
- [ ] 行動 App
- [ ] Webhook 整合
- [ ] 進階統計分析

## 🤝 **貢獻**

歡迎提交 Issue 和 Pull Request！

## 📄 **授權**

MIT License - 請參閱 [LICENSE](LICENSE) 文件

---

**🎯 讓 AI 幫您篩選重要財經資訊，節省時間，掌握先機！** 