# FinNews-Bot API Documentation

## 系統架構概述

FinNews-Bot 是一個財經新聞聚合和個人化推送系統，採用 FastAPI + Supabase + React 架構。

### 技術棧
- **後端**: FastAPI (Python)
- **資料庫**: Supabase (PostgreSQL)
- **前端**: React + TypeScript
- **認證**: Supabase Auth
- **推送**: Discord Webhook / Email

---

## 資料庫結構

### 核心資料表

#### 1. subscriptions (用戶訂閱)
```sql
CREATE TABLE public.subscriptions (
  user_id uuid PRIMARY KEY,
  is_active boolean DEFAULT true,
  news_sources jsonb DEFAULT '[]'::jsonb,
  delivery_platform delivery_platforms DEFAULT 'discord',
  delivery_target text NOT NULL,
  push_frequency_hours integer DEFAULT 24,
  keywords jsonb DEFAULT '[]'::jsonb,
  summary_language summary_languages DEFAULT 'zh-tw',
  last_pushed_at timestamp with time zone,
  updated_at timestamp with time zone DEFAULT now(),
  push_frequency_type text DEFAULT 'daily',
  last_push_window text,
  subscribed_tags text[] DEFAULT '{}',
  original_keywords text[] DEFAULT '{}',
  keywords_updated_at timestamp with time zone DEFAULT now(),
  tags_updated_at timestamp with time zone DEFAULT now(),
  guidance_completed boolean DEFAULT false,
  focus_score numeric DEFAULT 0.0,
  last_guidance_at timestamp with time zone,
  clustering_method text DEFAULT 'rule_based',
  primary_topics text[] DEFAULT '{}', -- 新增欄位
  FOREIGN KEY (user_id) REFERENCES public.profiles(id)
);
```

#### 2. news_articles (新聞文章)
```sql
CREATE TABLE public.news_articles (
  id bigint PRIMARY KEY,
  original_url text UNIQUE NOT NULL,
  source text NOT NULL,
  title text NOT NULL,
  summary text NOT NULL,
  published_at timestamp with time zone,
  created_at timestamp with time zone DEFAULT now(),
  tags text[] DEFAULT '{}'
);
```

#### 3. profiles (用戶資料)
```sql
CREATE TABLE public.profiles (
  id uuid PRIMARY KEY,
  platform_user_id text UNIQUE NOT NULL,
  username text,
  updated_at timestamp with time zone DEFAULT now(),
  FOREIGN KEY (id) REFERENCES auth.users(id)
);
```

#### 4. push_history (推送歷史)
```sql
CREATE TABLE public.push_history (
  id bigint PRIMARY KEY,
  user_id uuid NOT NULL,
  article_id bigint NOT NULL,
  pushed_at timestamp with time zone DEFAULT now(),
  batch_id text,
  FOREIGN KEY (user_id) REFERENCES public.profiles(id),
  FOREIGN KEY (article_id) REFERENCES public.news_articles(id)
);
```

---

## API 端點詳細說明

### 🚀 快速設定 API (`/api/v1/quick-onboarding/*`)

#### GET `/api/v1/quick-onboarding/templates`
**功能**: 獲取快速設定模板  
**認證**: 不需要  

**回應範例**:
```json
{
  "success": true,
  "templates": [
    {
      "id": "tech",
      "name": "科技股追蹤",
      "name_en": "Tech Stocks",
      "description": "關注蘋果、特斯拉、AI等科技趨勢",
      "icon": "💻",
      "keywords": ["蘋果", "特斯拉", "AI", "科技股"],
      "sample_news": "蘋果發布新 iPhone、特斯拉股價動態、AI技術突破",
      "focus_score": 0.85
    }
  ],
  "supported_platforms": ["discord", "email"],
  "platform_info": {
    "discord": {
      "name": "Discord",
      "description": "推送到 Discord 頻道",
      "icon": "💬"
    }
  }
}
```

#### POST `/api/v1/quick-onboarding/setup`
**功能**: 30秒快速設定訂閱  
**認證**: 需要  

**請求參數**:
```json
{
  "interest_category": "tech|crypto|market",
  "delivery_platform": "discord|email",
  "delivery_target": "webhook_url_or_email",
  "summary_language": "zh-tw",
  "push_frequency_type": "daily|twice|thrice"
}
```

**回應範例**:
```json
{
  "success": true,
  "subscription_id": "user-uuid",
  "template_used": "科技股追蹤",
  "keywords": ["蘋果", "特斯拉", "AI", "科技股"],
  "focus_score": 0.85,
  "message": "🎉 快速設定完成！",
  "next_steps": [
    "您的個人化新聞推送已設定完成",
    "將透過 discord 接收 科技股追蹤 相關新聞"
  ]
}
```

#### GET `/api/v1/quick-onboarding/platform-info`
**功能**: 獲取支援的推送平台資訊  

#### POST `/api/v1/quick-onboarding/validate-target`
**功能**: 驗證推送目標格式（僅格式驗證）  

#### GET `/api/v1/quick-onboarding/migration-check`
**功能**: 檢查用戶現有訂閱狀態  
**認證**: 需要  

---

### 📋 訂閱管理 API (`/api/v1/subscriptions/*`)

#### GET `/api/v1/subscriptions/`
**功能**: 獲取用戶訂閱資訊  
**認證**: 需要  

**回應範例**:
```json
{
  "user_id": "uuid",
  "delivery_platform": "discord",
  "delivery_target": "webhook_url",
  "keywords": ["蘋果", "特斯拉"],
  "news_sources": ["yahoo_finance"],
  "summary_language": "zh-tw",
  "push_frequency_type": "daily",
  "is_active": true,
  "focus_score": 0.85,
  "guidance_completed": true,
  "clustering_method": "rule_based",
  "primary_topics": ["tech", "electric-vehicles"]
}
```

#### POST `/api/v1/subscriptions/`
**功能**: 創建新訂閱  
**認證**: 需要  

#### PUT `/api/v1/subscriptions/`
**功能**: 更新現有訂閱  
**認證**: 需要  

#### DELETE `/api/v1/subscriptions/`
**功能**: 刪除訂閱  
**認證**: 需要  

#### PATCH `/api/v1/subscriptions/toggle`
**功能**: 切換訂閱啟用狀態  
**認證**: 需要  

#### GET `/api/v1/subscriptions/frequency-options`
**功能**: 獲取推送頻率選項  

#### POST `/api/v1/subscriptions/validate-connectivity`
**功能**: 測試推送目標連通性  
**認證**: 需要  

---

### 🎯 用戶引導 API (`/api/v1/guidance/*`)

#### GET `/api/v1/guidance/investment-focus-areas`
**功能**: 獲取投資領域選項  

#### GET `/api/v1/guidance/status`
**功能**: 檢查用戶引導狀態  
**認證**: 需要  

**回應範例**:
```json
{
  "has_subscription": true,
  "guidance_completed": false,
  "needs_guidance": true,
  "focus_score": 0.0,
  "last_guidance_at": null,
  "clustering_enabled": true
}
```

#### POST `/api/v1/guidance/start-onboarding`
**功能**: 開始用戶引導流程  
**認證**: 需要  

#### POST `/api/v1/guidance/investment-focus`
**功能**: 處理投資領域選擇  
**認證**: 需要  

#### POST `/api/v1/guidance/analyze-keywords`
**功能**: 分析用戶關鍵字並提供建議  
**認證**: 需要  

#### POST `/api/v1/guidance/finalize-onboarding`
**功能**: 完成用戶引導流程  
**認證**: 需要  

#### GET `/api/v1/guidance/optimization-suggestions`
**功能**: 獲取優化建議  
**認證**: 需要  

#### POST `/api/v1/guidance/clustering-analysis`
**功能**: 執行關鍵字語義聚類分析  
**認證**: 需要  

#### GET `/api/v1/guidance/enhanced-topics`
**功能**: 獲取用戶的增強版Topics推薦  
**認證**: 需要  

#### GET `/api/v1/guidance/focus-score`
**功能**: 獲取用戶當前的聚焦度評分  
**認證**: 需要  

#### POST `/api/v1/guidance/update-keywords`
**功能**: 更新用戶關鍵字並重新進行聚類分析  
**認證**: 需要  

---

### 📊 推送歷史 API (`/api/v1/history/*`)

#### GET `/api/v1/history/`
**功能**: 獲取用戶推送歷史  
**認證**: 需要  

**請求參數**:
- `limit`: 限制筆數 (預設: 50)

**回應範例**:
```json
[
  {
    "id": "123",
    "user_id": "uuid",
    "article": {
      "id": "456",
      "title": "蘋果股價創新高",
      "summary": "蘋果公司股價今日...",
      "original_url": "https://...",
      "published_at": "2024-01-01T00:00:00Z"
    },
    "pushed_at": "2024-01-01T08:00:00Z",
    "batch_id": "batch-uuid"
  }
]
```

#### GET `/api/v1/history/stats`
**功能**: 獲取推送統計資訊  
**認證**: 需要  

---

### 🏷️ 標籤管理 API (`/api/v1/tags/*`)

#### GET `/api/v1/tags/`
**功能**: 獲取所有可用標籤  

#### GET `/api/v1/tags/categories`
**功能**: 獲取標籤分類  

#### GET `/api/v1/tags/preview`
**功能**: 預覽標籤效果  

#### GET `/api/v1/tags/preferences`
**功能**: 獲取用戶標籤偏好  
**認證**: 需要  

#### POST `/api/v1/tags/preferences`
**功能**: 更新用戶標籤偏好  
**認證**: 需要  

---

## 資料流程圖

### 1. 快速設定流程
```
前端選擇模板 → POST /quick-onboarding/setup → 
資料庫創建訂閱 → 回傳設定完成狀態
```

### 2. 自定義引導流程
```
GET /guidance/status → POST /guidance/start-onboarding → 
POST /guidance/investment-focus → POST /guidance/analyze-keywords → 
POST /guidance/finalize-onboarding → 資料庫創建訂閱
```

### 3. 新聞推送流程
```
定時任務掃描活躍訂閱 → 新聞匹配用戶關鍵字 → 
AI摘要處理 → 推送到用戶指定平台 → 記錄推送歷史
```

---

## 認證機制

系統使用 Supabase Auth JWT Token 進行認證：

### 前端認證流程
```typescript
// 獲取當前用戶
const { data: { user } } = await supabase.auth.getUser()

// 設定請求標頭
const headers = {
  'Authorization': `Bearer ${session.access_token}`,
  'Content-Type': 'application/json'
}
```

### 後端認證驗證
```python
# 使用依賴注入獲取當前用戶ID
async def get_current_user_id(
    authorization: str = Header(...)
) -> str:
    # JWT Token 驗證邏輯
    return user_id
```

---

## 錯誤處理

### 標準錯誤格式
```json
{
  "detail": "錯誤訊息",
  "error_code": "ERROR_CODE",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

### 常見錯誤代碼
- `401`: 未授權 (缺少或無效的 Token)
- `403`: 禁止訪問 (權限不足)
- `404`: 資源不存在
- `422`: 請求參數驗證失敗
- `500`: 伺服器內部錯誤

---

## 部署相關

### 環境變數
```env
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_KEY=your_service_key
SUPABASE_ANON_KEY=your_anon_key
OPENAI_API_KEY=your_openai_key
```

### 資料庫初始化
執行以下 SQL 語句添加新欄位：
```sql
ALTER TABLE public.subscriptions 
ADD COLUMN primary_topics text[] DEFAULT '{}';
```

---

## 版本資訊

- **API 版本**: v1
- **最後更新**: 2024-01-01
- **維護狀態**: 積極維護

## 聯絡資訊

如有技術問題或建議，請聯絡開發團隊。