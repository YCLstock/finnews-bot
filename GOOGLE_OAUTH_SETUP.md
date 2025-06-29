# Google OAuth 設置指南

## 📋 概述

根據您的系統需求文檔，FinNews-Bot 使用 **僅 Google OAuth 2.0** 進行用戶認證，不提供傳統的 Email/密碼註冊。

## 🔧 設置位置

**Google OAuth 的設置分為兩個部分：**

### 1. 🌐 Google Cloud Console 設置（必須）
**位置：** Google Cloud Console  
**責任：** 後端開發者  
**狀態：** ❌ **尚未設置**

### 2. 💻 Supabase 設置（必須）
**位置：** Supabase Dashboard  
**責任：** 後端開發者  
**狀態：** ❌ **尚未設置**

### 3. 🎨 前端整合（稍後）
**位置：** Next.js/Vue.js 前端  
**責任：** 前端開發者  
**狀態：** ⏳ **第二階段開發**

## 🚀 立即需要設置的部分

### Step 1: Google Cloud Console 設置

1. **創建 Google Cloud 項目**
   ```
   前往：https://console.cloud.google.com/
   - 創建新項目或選擇現有項目
   - 項目名稱建議：finnews-bot
   ```

2. **啟用 Google+ API**
   ```
   在 API 庫中搜索並啟用：
   - Google+ API
   - Google People API（推薦）
   ```

3. **創建 OAuth 2.0 憑證**
   ```
   前往：憑證 → 創建憑證 → OAuth 客戶端 ID
   
   應用程式類型：網路應用程式
   名稱：FinNews-Bot Web Client
   
   已授權的 JavaScript 來源：
   - http://localhost:3000 (開發環境)
   - https://your-vercel-app.vercel.app (生產環境)
   
   已授權的重新導向 URI：
   - https://your-project.supabase.co/auth/v1/callback
   - http://localhost:3000/auth/callback (開發環境)
   ```

4. **記錄重要資訊**
   ```
   獲取以下資訊：
   ✅ Client ID: 123456789-abcdef.apps.googleusercontent.com
   ✅ Client Secret: GOCSPX-xxxxxxxxxxxxxxxxx
   ```

### Step 2: Supabase 設置

1. **登入 Supabase Dashboard**
   ```
   前往：https://supabase.com/dashboard
   選擇您的項目
   ```

2. **設置 Google OAuth Provider**
   ```
   路徑：Authentication → Providers → Google
   
   設置項目：
   ✅ Enabled: 開啟
   ✅ Client ID: (從 Google Cloud Console 獲取)
   ✅ Client Secret: (從 Google Cloud Console 獲取)
   ✅ Redirect URL: 自動生成，複製此 URL 到 Google Cloud Console
   ```

3. **設置 Site URL**
   ```
   路徑：Authentication → URL Configuration
   
   Site URL: https://your-vercel-app.vercel.app
   Redirect URLs: 
   - https://your-vercel-app.vercel.app/auth/callback
   - http://localhost:3000/auth/callback
   ```

### Step 3: 環境變數設置

更新您的 `.env` 文件：

```env
# Supabase Configuration (已有)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-key-here
SUPABASE_ANON_KEY=your-anon-key-here

# Google OAuth (新增 - 可選，主要用於前端)
GOOGLE_CLIENT_ID=123456789-abcdef.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-xxxxxxxxxxxxxxxxx

# 其他配置...
```

## 🎯 前端整合（第二階段）

當您開始開發前端時，會需要：

### Next.js 範例（使用 @supabase/auth-helpers-nextjs）

```javascript
// pages/auth/login.js
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY
)

export default function Login() {
  const handleGoogleLogin = async () => {
    const { data, error } = await supabase.auth.signInWithOAuth({
      provider: 'google',
      options: {
        redirectTo: `${window.location.origin}/auth/callback`
      }
    })
  }

  return (
    <button onClick={handleGoogleLogin}>
      使用 Google 登入
    </button>
  )
}
```

### Vue.js 範例（使用 @supabase/supabase-js）

```javascript
// components/LoginButton.vue
<template>
  <button @click="handleGoogleLogin">
    使用 Google 登入
  </button>
</template>

<script>
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(
  process.env.VUE_APP_SUPABASE_URL,
  process.env.VUE_APP_SUPABASE_ANON_KEY
)

export default {
  methods: {
    async handleGoogleLogin() {
      const { data, error } = await supabase.auth.signInWithOAuth({
        provider: 'google',
        options: {
          redirectTo: `${window.location.origin}/auth/callback`
        }
      })
    }
  }
}
</script>
```

## ✅ 驗證設置

設置完成後，您可以測試：

1. **測試 OAuth 流程**
   ```bash
   # 使用 curl 測試 Supabase Auth
   curl -X POST 'https://your-project.supabase.co/auth/v1/authorize' \
     -H 'apikey: your-anon-key' \
     -H 'Content-Type: application/json' \
     -d '{"provider": "google"}'
   ```

2. **檢查 JWT 驗證**
   ```bash
   # 在後端項目中運行
   python test_jwt_auth.py
   ```

## 🔒 安全考量

1. **Client Secret 保護**
   - ❌ 不要在前端代碼中暴露 Client Secret
   - ✅ 只在 Supabase 後端和您的 API 中使用

2. **重定向 URL 限制**
   - ✅ 只設置必要的重定向 URL
   - ✅ 使用 HTTPS（生產環境）

3. **作用域限制**
   - ✅ 只請求必要的權限（email, profile）

## 🚨 目前狀態

**需要立即設置：**
- [ ] Google Cloud Console OAuth 憑證
- [ ] Supabase Google Provider 配置
- [ ] 環境變數更新

**稍後設置（第二階段）：**
- [ ] 前端 Google OAuth 整合
- [ ] 用戶界面設計
- [ ] 錯誤處理和用戶體驗優化

## 📞 需要幫助？

如果您在設置過程中遇到問題，請提供：
1. 具體的錯誤信息
2. 您正在設置的步驟
3. 螢幕截圖（如果有的話）

我可以協助您完成設置！ 