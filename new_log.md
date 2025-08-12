PS D:\AI\finnews-bot> python scripts/run_real_push_test.py
INFO:core.delivery_manager:Delivery manager initialized with platforms: ['discord', 'email']
Loaded mapping config: 12 topics
INFO:__main__:🚀 Starting Real Email Push Test...
INFO:__main__:正在從資料庫查詢 'limyuha27@gmail.com' 的訂閱設定...
INFO:httpx:HTTP Request: GET https://gbobozzqoqfhqmttwzwn.supabase.co/rest/v1/subscriptions?select=%2A&delivery_target=eq.limyuha27%40gmail.com&delivery_platform=eq.email&limit=1 "HTTP/2 200 OK"
INFO:__main__:成功找到訂閱設定。
INFO:__main__:準備為用戶 85a739f1-0c2a-44be-9d79-8b018154d4db 執行真實推送測試 (使用用戶偏好)...
INFO:scripts.run_smart_pusher:
--- 處理用戶 85a739f1... 的推送 (daily) ---
INFO:scripts.run_smart_pusher:用戶 85a739f1... 不在推送時間窗口 (SKIP)
WARNING:__main__:⚠️ 初次推送未發送任何內容，現嘗試使用預設主題進行推送...
INFO:__main__:使用備用關鍵字進行推送: ['stock', 'inflation', 'economy']
INFO:scripts.run_smart_pusher:
--- 處理用戶 85a739f1... 的推送 (daily) ---
INFO:scripts.run_smart_pusher:用戶 85a739f1... 不在推送時間窗口 (SKIP)
ERROR:__main__:❌ 備用推送也失敗了。可能近期沒有任何相關主題的文章。
INFO:__main__:🏁 Real Email Push Test Finished.