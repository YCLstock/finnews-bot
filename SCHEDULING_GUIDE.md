# FinNews-Bot 排程設定指南

## 🎯 分離架構概述

專案已分離為兩個獨立腳本，各自有不同的執行頻率：

### 🕷️ 爬蟲腳本 (crawler_only.py)
- **功能**: 爬取新聞 → 生成AI摘要 → 儲存到資料庫
- **建議頻率**: 每2-4小時執行一次
- **執行時間**: 不限制，任何時間都可以

### 🔔 推送腳本 (pusher_only.py)  
- **功能**: 檢查用戶訂閱 → 找符合條件文章 → 發送Discord通知
- **建議頻率**: 每10分鐘檢查一次
- **推送時間窗口**:
  - Daily: 08:00 ±30分鐘
  - Twice: 08:00, 20:00 ±30分鐘  
  - Thrice: 08:00, 13:00, 20:00 ±30分鐘

---

## ⚙️ Windows 工作排程器設定

### 1. 設定爬蟲排程

```powershell
# 每3小時執行爬蟲
schtasks /create /tn "FinNews-Crawler" /tr "python D:\AI\yahoo_test\finnews-bot\finnews-bot\crawler_only.py" /sc hourly /mo 3

# 或指定特定時間 (每天6次)
schtasks /create /tn "FinNews-Crawler" /tr "python D:\AI\yahoo_test\finnews-bot\finnews-bot\crawler_only.py" /sc daily /st 02:00,06:00,10:00,14:00,18:00,22:00
```

### 2. 設定推送排程

```powershell
# 每10分鐘檢查推送
schtasks /create /tn "FinNews-Pusher" /tr "python D:\AI\yahoo_test\finnews-bot\finnews-bot\pusher_only.py" /sc minute /mo 10
```

### 3. 管理排程

```powershell
# 查看排程
schtasks /query /tn "FinNews-Crawler"
schtasks /query /tn "FinNews-Pusher"

# 刪除排程
schtasks /delete /tn "FinNews-Crawler" /f
schtasks /delete /tn "FinNews-Pusher" /f

# 手動執行
schtasks /run /tn "FinNews-Crawler"
schtasks /run /tn "FinNews-Pusher"
```

---

## 🐧 Linux Cron 設定

### 1. 編輯 crontab

```bash
crontab -e
```

### 2. 添加排程規則

```bash
# 每3小時執行爬蟲
0 */3 * * * cd /path/to/finnews-bot && python crawler_only.py >> logs/crawler.log 2>&1

# 每10分鐘檢查推送
*/10 * * * * cd /path/to/finnews-bot && python pusher_only.py >> logs/pusher.log 2>&1
```

---

## 📊 監控與日誌

### 1. 建立日誌目錄

```bash
mkdir logs
```

### 2. 帶日誌的執行命令

```bash
# Windows
python crawler_only.py >> logs\crawler.log 2>&1
python pusher_only.py >> logs\pusher.log 2>&1

# Linux
python crawler_only.py >> logs/crawler.log 2>&1
python pusher_only.py >> logs/pusher.log 2>&1
```

### 3. 查看日誌

```bash
# 查看最新日誌
tail -f logs/crawler.log
tail -f logs/pusher.log

# 查看今日日誌
grep "$(date +%Y-%m-%d)" logs/crawler.log
grep "$(date +%Y-%m-%d)" logs/pusher.log
```

---

## 🧪 測試與驗證

### 1. 手動測試

```bash
# 測試爬蟲功能
python crawler_only.py

# 測試推送功能
python pusher_only.py

# 系統完整檢查
python test_simple.py
```

### 2. 驗證資料庫

- 檢查 `news_articles` 表是否有新文章
- 檢查 `subscriptions` 表的 `last_push_window` 更新
- 檢查 `push_history` 表的推送記錄

### 3. 驗證Discord

- 確認 webhook URL 正確
- 檢查 Discord 頻道是否收到訊息
- 確認訊息格式和內容正確

---

## ⚠️ 注意事項

### 1. 時區設定
- 系統使用台灣時間 (UTC+8)
- 推送時間窗口基於台灣時間計算

### 2. API 限制
- OpenAI API: 注意token使用量
- Discord API: 推送間隔1.5秒避免限制
- Supabase: 注意請求頻率

### 3. 錯誤處理
- 腳本包含完整的錯誤處理機制
- 失敗不會影響後續執行
- 詳細日誌記錄所有操作

### 4. 環境變數
- 確保 `.env` 檔案包含所有必要設定
- 定期檢查 API 金鑰有效性

---

## 🚀 建議的執行配置

### 生產環境

```
爬蟲頻率: 每3小時 (00:00, 03:00, 06:00, 09:00, 12:00, 15:00, 18:00, 21:00)
推送頻率: 每10分鐘檢查
```

### 開發環境

```
爬蟲頻率: 每小時 (測試用)
推送頻率: 每5分鐘檢查 (測試用)
```

### 測試環境

```
手動執行: 按需執行
日誌級別: 詳細模式
```

---

**🎯 完成設定後，您的FinNews-Bot將自動運行，定時爬取新聞並按用戶訂閱推送！**