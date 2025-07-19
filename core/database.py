from typing import List, Dict, Any, Optional
from datetime import datetime, timezone, timedelta
import uuid
from supabase import create_client, Client
from core.config import settings

class DatabaseManager:
    """Database operations manager for FinNews-Bot"""
    
    def __init__(self):
        """Initialize Supabase client"""
        if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_KEY:
            raise ValueError("Supabase configuration is missing")
        
        self.supabase: Client = create_client(
            settings.SUPABASE_URL, 
            settings.SUPABASE_SERVICE_KEY
        )
        
        # 推送時間配置
        self.PUSH_SCHEDULES = {
            "daily": {
                "times": ["08:00"],
                "window_minutes": 30,
                "max_articles": 10
            },
            "twice": {
                "times": ["08:00", "20:00"],
                "window_minutes": 30,
                "max_articles": 5
            },
            "thrice": {
                "times": ["08:00", "13:00", "20:00"],
                "window_minutes": 30,
                "max_articles": 3
            }
        }
    
    def get_active_subscriptions(self) -> List[Dict[str, Any]]:
        """從 Supabase 讀取所有活躍的訂閱任務"""
        try:
            data = self.supabase.table("subscriptions").select("*").eq("is_active", True).execute()
            print(f"🗂️ 從資料庫讀取到 {len(data.data)} 個活躍的訂閱任務。")
            return data.data
        except Exception as e:
            print(f"❌ 讀取訂閱任務錯誤: {e}")
            return []
    
    def get_subscriptions_by_user(self, user_id: str) -> List[Dict[str, Any]]:
        """根據用戶 ID 獲取訂閱任務（為了向後兼容，返回列表）"""
        try:
            data = self.supabase.table("subscriptions").select("*").eq("user_id", user_id).execute()
            return data.data
        except Exception as e:
            print(f"❌ 讀取用戶訂閱錯誤: {e}")
            return []
    
    def get_subscription_by_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """根據用戶 ID 獲取單一訂閱任務"""
        try:
            print(f"🔍 資料庫查詢: 正在查詢用戶 {user_id} 的訂閱")
            
            # 先確保用戶 profile 存在（靜默處理）
            self.ensure_user_profile_exists(user_id)
            
            data = self.supabase.table("subscriptions").select("*").eq("user_id", user_id).execute()
            
            if hasattr(data, 'data') and data.data:
                print(f"✅ 資料庫查詢成功: 找到用戶 {user_id} 的訂閱")
                return data.data[0]
            else:
                print(f"📭 資料庫查詢成功: 用戶 {user_id} 暫無訂閱記錄")
                return None
                
        except Exception as e:
            print(f"❌ 資料庫查詢錯誤: {e}")
            print(f"❌ 錯誤類型: {type(e).__name__}")
            import traceback
            print(f"❌ 詳細堆疊: {traceback.format_exc()}")
            
            # 重新拋出異常，讓上層處理
            raise e
    
    def ensure_user_profile_exists(self, user_id: str) -> bool:
        """確保用戶 profile 存在，如果不存在則創建"""
        try:
            print(f"🔍 檢查用戶 {user_id} 的 profile 是否存在")
            
            # 檢查 profile 是否存在
            profile_result = self.supabase.table("profiles").select("id").eq("id", user_id).execute()
            
            if profile_result.data:
                print(f"✅ 用戶 {user_id} 的 profile 已存在")
                return True
            
            print(f"📝 用戶 {user_id} 的 profile 不存在，正在創建...")
            
            # 創建 profile 記錄
            try:
                # 嘗試從 auth.users 獲取用戶資訊
                username = None
                try:
                    # 使用 RPC 函數或直接查詢（需要 service role key）
                    auth_user_result = self.supabase.table("auth.users").select("email, raw_user_meta_data").eq("id", user_id).execute()
                    if auth_user_result.data:
                        user_data = auth_user_result.data[0]
                        # 嘗試從 email 或 metadata 獲取用戶名
                        username = user_data.get("email", "").split("@")[0] if user_data.get("email") else None
                        if not username and user_data.get("raw_user_meta_data"):
                            meta_data = user_data.get("raw_user_meta_data", {})
                            username = meta_data.get("name") or meta_data.get("full_name") or meta_data.get("user_name")
                except Exception as auth_error:
                    print(f"⚠️ 無法從 auth.users 獲取用戶資訊: {auth_error}")
                
                profile_data = {
                    "id": user_id,
                    "platform_user_id": user_id,  # 使用 user_id 作為 platform_user_id
                    "username": username  # 從 auth 資料獲取的用戶名
                }
                
                create_result = self.supabase.table("profiles").insert(profile_data).execute()
                
                if create_result.data:
                    print(f"✅ 成功創建用戶 {user_id} 的 profile")
                    return True
                else:
                    print(f"❌ 創建 profile 失敗: 無資料返回")
                    return False
                    
            except Exception as create_error:
                print(f"❌ 創建 profile 時發生錯誤: {create_error}")
                return False
                
        except Exception as e:
            print(f"❌ 檢查/創建用戶 profile 錯誤: {e}")
            return False
    
    def create_subscription(self, subscription_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """創建新的訂閱任務（使用 UPSERT，因為每個用戶只能有一個訂閱）"""
        try:
            user_id = subscription_data.get("user_id")
            if not user_id:
                print("❌ 創建訂閱錯誤: 缺少 user_id")
                return None
            
            # 確保用戶 profile 存在
            if not self.ensure_user_profile_exists(user_id):
                print(f"❌ 無法確保用戶 {user_id} 的 profile 存在")
                return None
            
            print(f"📝 正在創建/更新訂閱: {subscription_data}")
            result = self.supabase.table("subscriptions").upsert(subscription_data).execute()
            
            if result.data:
                print(f"✅ 成功創建/更新訂閱")
                return result.data[0]
            else:
                print("❌ 創建訂閱失敗: 無資料返回")
                return None
                
        except Exception as e:
            print(f"❌ 創建訂閱錯誤: {e}")
            print(f"❌ 錯誤類型: {type(e).__name__}")
            import traceback
            print(f"❌ 詳細堆疊: {traceback.format_exc()}")
            return None
    
    def update_subscription(self, user_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """更新訂閱任務（使用 user_id 作為主鍵）"""
        try:
            # 確保用戶 profile 存在
            if not self.ensure_user_profile_exists(user_id):
                print(f"❌ 無法確保用戶 {user_id} 的 profile 存在")
                return None
            
            result = self.supabase.table("subscriptions").update(update_data).eq("user_id", user_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"❌ 更新訂閱錯誤: {e}")
            return None
    
    def delete_subscription(self, user_id: str) -> bool:
        """刪除訂閱任務（使用 user_id 作為主鍵）"""
        try:
            self.supabase.table("subscriptions").delete().eq("user_id", user_id).execute()
            return True
        except Exception as e:
            print(f"❌ 刪除訂閱錯誤: {e}")
            return False
    
    def is_article_processed(self, url: str) -> bool:
        """檢查文章是否已經被處理並儲存過"""
        try:
            result = self.supabase.table('news_articles').select('id', count='exact').eq('original_url', url).execute()
            return result.count > 0
        except Exception as e:
            print(f"❌ 檢查文章是否重複錯誤: {e}")
            return True  # 發生錯誤時，當作已處理以避免重複發送
    
    def save_new_article(self, article_data: Dict[str, Any]) -> Optional[int]:
        """將新處理的文章儲存到 Supabase"""
        try:
            result = self.supabase.table("news_articles").insert(article_data).execute()
            print(f"✅ 儲存成功: {article_data['title']}")
            return result.data[0]['id']
        except Exception as e:
            print(f"❌ 儲存新文章時錯誤: {e}")
            return None
    
    def log_push_history(self, user_id: str, article_ids: List[int], batch_id: str = None) -> bool:
        """記錄推送歷史到 Supabase（支援批量推送）"""
        if batch_id is None:
            batch_id = str(uuid.uuid4())
        
        records = [
            {
                "user_id": user_id, 
                "article_id": article_id,
                "batch_id": batch_id
            } 
            for article_id in article_ids
        ]
        
        try:
            self.supabase.table("push_history").insert(records).execute()
            print(f"📝 已紀錄推播歷史 {len(article_ids)} 筆 (批次ID: {batch_id[:8]}...)")
            return True
        except Exception as e:
            print(f"❌ 紀錄推播歷史失敗: {e}")
            return False
    
    def get_push_history_by_user(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """獲取用戶的推送歷史"""
        try:
            data = self.supabase.table("push_history").select(
                "*, news_articles(title, original_url, summary, published_at)"
            ).eq("user_id", user_id).order("pushed_at", desc=True).limit(limit).execute()
            return data.data
        except Exception as e:
            print(f"❌ 讀取推送歷史錯誤: {e}")
            return []
    
    def is_within_time_window(self, current_time: str, target_time: str, window_minutes: int) -> bool:
        """檢查當前時間是否在目標時間的窗口內"""
        try:
            # 解析時間字符串 (HH:MM)
            current_hour, current_min = map(int, current_time.split(':'))
            target_hour, target_min = map(int, target_time.split(':'))
            
            # 轉換為分鐘數以便比較
            current_total_min = current_hour * 60 + current_min
            target_total_min = target_hour * 60 + target_min
            
            # 檢查是否在窗口內（±window_minutes）
            diff = abs(current_total_min - target_total_min)
            
            # 處理跨午夜的情況
            if diff > 12 * 60:  # 如果差距超過12小時，可能是跨午夜
                diff = 24 * 60 - diff
            
            return diff <= window_minutes
        except Exception as e:
            print(f"❌ 時間窗口檢查錯誤: {e}")
            return False
    
    def should_push_now(self, subscription: Dict[str, Any]) -> bool:
        """檢查現在是否應該推送"""
        frequency_type = subscription.get('push_frequency_type', 'daily')
        current_time = datetime.now().strftime("%H:%M")
        current_window = self.get_current_time_window(current_time, frequency_type)
        
        if not current_window:
            return False
        
        # 檢查是否已經在這個時間窗口推送過
        last_push_window = subscription.get('last_push_window')
        today = datetime.now().strftime("%Y-%m-%d")
        current_window_key = f"{today}-{current_window}"
        
        if last_push_window == current_window_key:
            print(f"⏳ 用戶 {subscription['user_id']} 在時間窗口 {current_window} 已推送過")
            return False
        
        print(f"✅ 用戶 {subscription['user_id']} 可在時間窗口 {current_window} 推送")
        return True
    
    def get_current_time_window(self, current_time: str, frequency_type: str) -> Optional[str]:
        """獲取當前時間所屬的推送窗口"""
        schedule = self.PUSH_SCHEDULES.get(frequency_type, self.PUSH_SCHEDULES['daily'])
        window_minutes = schedule['window_minutes']
        
        for push_time in schedule['times']:
            if self.is_within_time_window(current_time, push_time, window_minutes):
                return push_time
        
        return None
    
    def get_max_articles_for_frequency(self, frequency_type: str) -> int:
        """根據推送頻率獲取最大文章數量"""
        schedule = self.PUSH_SCHEDULES.get(frequency_type, self.PUSH_SCHEDULES['daily'])
        return schedule['max_articles']
    
    def mark_push_window_completed(self, user_id: str, frequency_type: str) -> bool:
        """標記推送窗口為已完成（使用 user_id 作為主鍵）"""
        try:
            current_time = datetime.now().strftime("%H:%M")
            current_window = self.get_current_time_window(current_time, frequency_type)
            
            if current_window:
                today = datetime.now().strftime("%Y-%m-%d")
                window_key = f"{today}-{current_window}"
                
                result = self.supabase.table("subscriptions").update({
                    "last_push_window": window_key
                }).eq("user_id", user_id).execute()
                
                print(f"✅ 標記推送窗口完成: {window_key}")
                return True
        except Exception as e:
            print(f"❌ 標記推送窗口錯誤: {e}")
        
        return False
    
    def get_eligible_subscriptions(self) -> List[Dict[str, Any]]:
        """獲取當前時間符合推送條件的訂閱"""
        all_subscriptions = self.get_active_subscriptions()
        eligible = []
        
        for subscription in all_subscriptions:
            if self.should_push_now(subscription):
                eligible.append(subscription)
        
        print(f"📋 本輪符合推送條件的訂閱: {len(eligible)} 個")
        return eligible

# Create a global database manager instance
db_manager = DatabaseManager() 