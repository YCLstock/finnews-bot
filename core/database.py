from typing import List, Dict, Any, Optional
from datetime import datetime, timezone, timedelta
import uuid
import logging
from supabase import create_client, Client
from core.config import settings
from core.utils import get_current_taiwan_time, get_current_utc_time, utc_to_taiwan_time

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
            print(f"[DB] Retrieved {len(data.data)} active subscriptions from database")
            return data.data
        except Exception as e:
            print(f"[ERROR] Failed to read subscriptions: {e}")
            return []
    
    def get_subscriptions_by_user(self, user_id: str) -> List[Dict[str, Any]]:
        """根據用戶 ID 獲取訂閱任務（為了向後兼容，返回列表）"""
        try:
            data = self.supabase.table("subscriptions").select("*").eq("user_id", user_id).execute()
            return data.data
        except Exception as e:
            print(f"[ERROR] 讀取用戶訂閱錯誤: {e}")
            return []
    
    def get_subscription_by_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """根據用戶 ID 獲取單一訂閱任務"""
        try:
            print(f"[INFO] 資料庫查詢: 正在查詢用戶 {user_id} 的訂閱")
            
            # 先確保用戶 profile 存在（靜默處理）
            self.ensure_user_profile_exists(user_id)
            
            data = self.supabase.table("subscriptions").select("*").eq("user_id", user_id).execute()
            
            if hasattr(data, 'data') and data.data:
                print(f"[OK] 資料庫查詢成功: 找到用戶 {user_id} 的訂閱")
                return data.data[0]
            else:
                print(f"[INFO] 資料庫查詢成功: 用戶 {user_id} 暫無訂閱記錄")
                return None
                
        except Exception as e:
            print(f"[ERROR] 資料庫查詢錯誤: {e}")
            print(f"[ERROR] 錯誤類型: {type(e).__name__}")
            import traceback
            print(f"[ERROR] 詳細堆疊: {traceback.format_exc()}")
            
            # 重新拋出異常，讓上層處理
            raise e
    
    def ensure_user_profile_exists(self, user_id: str) -> bool:
        """確保用戶 profile 存在，如果不存在則創建"""
        try:
            print(f"[INFO] 檢查用戶 {user_id} 的 profile 是否存在")
            
            # 檢查 profile 是否存在
            profile_result = self.supabase.table("profiles").select("id").eq("id", user_id).execute()
            
            if profile_result.data:
                print(f"[OK] 用戶 {user_id} 的 profile 已存在")
                return True
            
            print(f"[INFO] 用戶 {user_id} 的 profile 不存在，正在創建...")
            
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
                    print(f"[WARN] 無法從 auth.users 獲取用戶資訊: {auth_error}")
                
                profile_data = {
                    "id": user_id,
                    "platform_user_id": user_id,  # 使用 user_id 作為 platform_user_id
                    "username": username  # 從 auth 資料獲取的用戶名
                }
                
                create_result = self.supabase.table("profiles").insert(profile_data).execute()
                
                if create_result.data:
                    print(f"[OK] 成功創建用戶 {user_id} 的 profile")
                    return True
                else:
                    print(f"[ERROR] 創建 profile 失敗: 無資料返回")
                    return False
                    
            except Exception as create_error:
                print(f"[ERROR] 創建 profile 時發生錯誤: {create_error}")
                return False
                
        except Exception as e:
            print(f"[ERROR] 檢查/創建用戶 profile 錯誤: {e}")
            return False
    
    def create_subscription(self, subscription_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """創建新的訂閱任務（使用 UPSERT，因為每個用戶只能有一個訂閱）"""
        try:
            user_id = subscription_data.get("user_id")
            if not user_id:
                print("[ERROR] 創建訂閱錯誤: 缺少 user_id")
                return None
            
            # 確保用戶 profile 存在
            if not self.ensure_user_profile_exists(user_id):
                print(f"[ERROR] 無法確保用戶 {user_id} 的 profile 存在")
                return None
            
            print(f"[INFO] 正在創建/更新訂閱: {subscription_data}")
            result = self.supabase.table("subscriptions").upsert(subscription_data).execute()
            
            if result.data:
                print(f"[OK] 成功創建/更新訂閱")
                return result.data[0]
            else:
                print("[ERROR] 創建訂閱失敗: 無資料返回")
                return None
                
        except Exception as e:
            print(f"[ERROR] 創建訂閱錯誤: {e}")
            print(f"[ERROR] 錯誤類型: {type(e).__name__}")
            import traceback
            print(f"[ERROR] 詳細堆疊: {traceback.format_exc()}")
            return None
    
    def update_subscription(self, user_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """更新訂閱任務（使用 user_id 作為主鍵）"""
        try:
            # 確保用戶 profile 存在
            if not self.ensure_user_profile_exists(user_id):
                print(f"[ERROR] 無法確保用戶 {user_id} 的 profile 存在")
                return None
            
            result = self.supabase.table("subscriptions").update(update_data).eq("user_id", user_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"[ERROR] 更新訂閱錯誤: {e}")
            return None
    
    def delete_subscription(self, user_id: str) -> bool:
        """刪除訂閱任務（使用 user_id 作為主鍵）"""
        try:
            self.supabase.table("subscriptions").delete().eq("user_id", user_id).execute()
            return True
        except Exception as e:
            print(f"[ERROR] 刪除訂閱錯誤: {e}")
            return False
    
    def is_article_processed(self, url: str) -> bool:
        """檢查文章是否已經被處理並儲存過"""
        try:
            result = self.supabase.table('news_articles').select('id', count='exact').eq('original_url', url).execute()
            return result.count > 0
        except Exception as e:
            print(f"[ERROR] 檢查文章是否重複錯誤: {e}")
            return True  # 發生錯誤時，當作已處理以避免重複發送
    
    def save_new_article(self, article_data: Dict[str, Any]) -> Optional[int]:
        """將新處理的文章儲存到 Supabase"""
        try:
            result = self.supabase.table("news_articles").insert(article_data).execute()
            print(f"[OK] 儲存成功: {article_data['title']}")
            return result.data[0]['id']
        except Exception as e:
            print(f"[ERROR] 儲存新文章時錯誤: {e}")
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
            print(f"[INFO] 已紀錄推播歷史 {len(article_ids)} 筆 (批次ID: {batch_id[:8]}...)")
            return True
        except Exception as e:
            print(f"[ERROR] 紀錄推播歷史失敗: {e}")
            return False
    
    def get_push_history_by_user(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """獲取用戶的推送歷史"""
        try:
            data = self.supabase.table("push_history").select(
                "*, news_articles(title, original_url, summary, published_at)"
            ).eq("user_id", user_id).order("pushed_at", desc=True).limit(limit).execute()
            return data.data
        except Exception as e:
            print(f"[ERROR] 讀取推送歷史錯誤: {e}")
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
            print(f"[ERROR] 時間窗口檢查錯誤: {e}")
            return False
    
    def should_push_now(self, subscription: Dict[str, Any]) -> bool:
        """檢查現在是否應該推送（使用台灣時間）"""
        frequency_type = subscription.get('push_frequency_type', 'daily')
        
        # 使用台灣時間進行推送邏輯檢查
        taiwan_time = get_current_taiwan_time()
        current_time = taiwan_time.strftime("%H:%M")
        current_window = self.get_current_time_window(current_time, frequency_type)
        
        if not current_window:
            return False
        
        # 檢查是否已經在這個時間窗口推送過
        last_push_window = subscription.get('last_push_window')
        today = taiwan_time.strftime("%Y-%m-%d")
        current_window_key = f"{today}-{current_window}"
        
        if last_push_window == current_window_key:
            print(f"[INFO] 用戶 {subscription['user_id']} 在時間窗口 {current_window} 已推送過")
            return False
        
        print(f"[OK] 用戶 {subscription['user_id']} 可在時間窗口 {current_window} 推送 (台灣時間: {taiwan_time.strftime('%H:%M')})")
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
        """標記推送窗口為已完成（使用 user_id 作為主鍵，基於台灣時間）"""
        try:
            # 使用台灣時間確保一致性
            taiwan_time = get_current_taiwan_time()
            current_time = taiwan_time.strftime("%H:%M")
            current_window = self.get_current_time_window(current_time, frequency_type)
            
            if current_window:
                today = taiwan_time.strftime("%Y-%m-%d")
                window_key = f"{today}-{current_window}"
                
                # 同時更新 last_pushed_at 為 UTC 時間
                utc_now = get_current_utc_time()
                
                result = self.supabase.table("subscriptions").update({
                    "last_push_window": window_key,
                    "last_pushed_at": utc_now.isoformat()
                }).eq("user_id", user_id).execute()
                
                print(f"[OK] 標記推送窗口完成: {window_key} (台灣時間: {taiwan_time.strftime('%Y-%m-%d %H:%M:%S')})")
                return True
        except Exception as e:
            print(f"[ERROR] 標記推送窗口錯誤: {e}")
        
        return False
    
    def get_eligible_subscriptions(self) -> List[Dict[str, Any]]:
        """獲取當前時間符合推送條件的訂閱"""
        all_subscriptions = self.get_active_subscriptions()
        eligible = []
        
        for subscription in all_subscriptions:
            if self.should_push_now(subscription):
                eligible.append(subscription)
        
        print(f"[INFO] 本輪符合推送條件的訂閱: {len(eligible)} 個")
        return eligible
    
    def get_users_with_outdated_tags(self) -> List[Dict[str, Any]]:
        """獲取需要更新標籤的用戶（關鍵字更新時間晚於標籤更新時間）"""
        try:
            print("[INFO] 檢查需要更新標籤的用戶...")
            
            # 查詢所有活躍用戶的時間戳
            result = self.supabase.table('subscriptions').select(
                'user_id, original_keywords, keywords_updated_at, tags_updated_at'
            ).eq('is_active', True).execute()
            
            outdated_users = []
            for user in result.data:
                keywords_time = user.get('keywords_updated_at')
                tags_time = user.get('tags_updated_at')
                
                # 如果關鍵字更新時間晚於標籤更新時間，需要更新
                if keywords_time and tags_time and keywords_time > tags_time:
                    outdated_users.append(user)
                elif keywords_time and not tags_time:  # 新用戶，從未轉換過標籤
                    outdated_users.append(user)
            
            print(f"[INFO] 發現 {len(outdated_users)} 個用戶需要更新標籤")
            return outdated_users
            
        except Exception as e:
            print(f"[ERROR] 檢查用戶失敗: {e}")
            return []
    
    def update_user_subscribed_tags(self, user_id: str, tags: List[str]) -> bool:
        """更新用戶的訂閱標籤"""
        try:
            update_data = {
                'subscribed_tags': tags,
                'tags_updated_at': get_current_utc_time().isoformat()
            }
            
            result = self.supabase.table('subscriptions').update(
                update_data
            ).eq('user_id', user_id).execute()
            
            return len(result.data) > 0
            
        except Exception as e:
            print(f"[ERROR] 更新用戶 {user_id} 標籤失敗: {e}")
            return False
    
    def mark_keywords_as_updated(self, user_id: str) -> bool:
        """標記用戶關鍵字為已更新（當用戶修改關鍵字時調用）"""
        try:
            update_data = {
                'keywords_updated_at': get_current_utc_time().isoformat()
            }
            
            result = self.supabase.table('subscriptions').update(
                update_data
            ).eq('user_id', user_id).execute()
            
            return len(result.data) > 0
            
        except Exception as e:
            print(f"[ERROR] 標記用戶 {user_id} 關鍵字更新失敗: {e}")
            return False

    # ====== 用戶引導與聚類相關方法 ======
    
    def save_user_guidance_history(self, user_id: str, guidance_type: str, 
                                 original_keywords: List[str], suggested_keywords: List[str],
                                 user_choice: str, guidance_result: Dict[str, Any]) -> bool:
        """保存用戶引導歷史記錄"""
        try:
            guidance_data = {
                'user_id': user_id,
                'guidance_type': guidance_type,
                'original_keywords': original_keywords,
                'suggested_keywords': suggested_keywords,
                'user_choice': user_choice,
                'guidance_result': guidance_result,
                'created_at': datetime.now(timezone.utc).isoformat()
            }
            
            result = self.supabase.table('user_guidance_history').insert(guidance_data).execute()
            logger.info(f"Saved guidance history for user {user_id}")
            return len(result.data) > 0
            
        except Exception as e:
            logger.error(f"Failed to save guidance history for user {user_id}: {e}")
            return False
    
    def save_keyword_clustering_result(self, user_id: str, original_keywords: List[str],
                                     clustered_keywords: List[List[str]], cluster_confidence: float,
                                     primary_topics: List[str], cluster_method: str) -> bool:
        """保存關鍵字聚類結果"""
        try:
            cluster_data = {
                'user_id': user_id,
                'original_keywords': original_keywords,
                'clustered_keywords': clustered_keywords,
                'cluster_confidence': cluster_confidence,
                'primary_topics': primary_topics,
                'cluster_method': cluster_method,
                'is_active': True,
                'created_at': datetime.now(timezone.utc).isoformat(),
                'updated_at': datetime.now(timezone.utc).isoformat()
            }
            
            result = self.supabase.table('keyword_clusters').insert(cluster_data).execute()
            logger.info(f"Saved clustering result for user {user_id}")
            return len(result.data) > 0
            
        except Exception as e:
            logger.error(f"Failed to save clustering result for user {user_id}: {e}")
            return False
    
    def get_user_preferences(self, user_id: str) -> Optional[Dict[str, Any]]:
        """獲取用戶偏好設定"""
        try:
            result = self.supabase.table('user_preferences').select('*').eq('user_id', user_id).execute()
            
            if result.data:
                return result.data[0]
            return None
            
        except Exception as e:
            logger.error(f"Failed to get user preferences for {user_id}: {e}")
            return None
    
    def update_user_preferences(self, user_id: str, focus_score: float, 
                              primary_topics: List[str], engagement_patterns: Dict[str, Any] = None,
                              optimization_suggestions: Dict[str, Any] = None) -> bool:
        """更新或創建用戶偏好設定"""
        try:
            preferences_data = {
                'user_id': user_id,
                'focus_score': focus_score,
                'primary_topics': primary_topics,
                'engagement_patterns': engagement_patterns or {},
                'optimization_suggestions': optimization_suggestions or {},
                'last_optimization_at': datetime.now(timezone.utc).isoformat(),
                'updated_at': datetime.now(timezone.utc).isoformat()
            }
            
            # 嘗試更新，如果不存在則插入
            existing = self.get_user_preferences(user_id)
            
            if existing:
                result = self.supabase.table('user_preferences').update(preferences_data).eq('user_id', user_id).execute()
            else:
                preferences_data['created_at'] = datetime.now(timezone.utc).isoformat()
                result = self.supabase.table('user_preferences').insert(preferences_data).execute()
            
            logger.info(f"Updated user preferences for {user_id}")
            return len(result.data) > 0
            
        except Exception as e:
            logger.error(f"Failed to update user preferences for {user_id}: {e}")
            return False
    
    def update_user_guidance_status(self, user_id: str, guidance_completed: bool = True,
                                  focus_score: float = None) -> bool:
        """更新用戶引導完成狀態"""
        try:
            update_data = {
                'guidance_completed': guidance_completed,
                'last_guidance_at': datetime.now(timezone.utc).isoformat()
            }
            
            if focus_score is not None:
                update_data['focus_score'] = focus_score
            
            result = self.supabase.table('subscriptions').update(update_data).eq('user_id', user_id).execute()
            
            logger.info(f"Updated guidance status for user {user_id}")
            return len(result.data) > 0
            
        except Exception as e:
            logger.error(f"Failed to update guidance status for {user_id}: {e}")
            return False
    
    def get_users_needing_guidance(self) -> List[Dict[str, Any]]:
        """獲取需要引導的用戶"""
        try:
            # 查找未完成引導的活躍用戶
            result = self.supabase.table('subscriptions').select(
                'user_id, keywords, guidance_completed, focus_score, last_guidance_at'
            ).eq('is_active', True).eq('guidance_completed', False).execute()
            
            return result.data
            
        except Exception as e:
            logger.error(f"Failed to get users needing guidance: {e}")
            return []
    
    def get_users_with_low_focus_score(self, threshold: float = 0.5) -> List[Dict[str, Any]]:
        """獲取聚焦度較低的用戶"""
        try:
            result = self.supabase.table('subscriptions').select(
                'user_id, keywords, focus_score, last_guidance_at'
            ).eq('is_active', True).lt('focus_score', threshold).execute()
            
            return result.data
            
        except Exception as e:
            logger.error(f"Failed to get users with low focus score: {e}")
            return []
    
    def get_user_clustering_history(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """獲取用戶的聚類歷史記錄"""
        try:
            result = self.supabase.table('keyword_clusters').select('*').eq(
                'user_id', user_id
            ).eq('is_active', True).order('created_at', desc=True).limit(limit).execute()
            
            return result.data
            
        except Exception as e:
            logger.error(f"Failed to get clustering history for {user_id}: {e}")
            return []
    
    def get_user_guidance_history(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """獲取用戶的引導歷史記錄"""
        try:
            result = self.supabase.table('user_guidance_history').select('*').eq(
                'user_id', user_id
            ).order('created_at', desc=True).limit(limit).execute()
            
            return result.data
            
        except Exception as e:
            logger.error(f"Failed to get guidance history for {user_id}: {e}")
            return []
    
    def update_subscription_with_enhanced_data(self, user_id: str, keywords: List[str],
                                             focus_score: float, primary_topics: List[str],
                                             clustering_method: str = "semantic") -> bool:
        """使用增強數據更新用戶訂閱"""
        try:
            update_data = {
                'keywords': keywords,
                'focus_score': focus_score,
                'clustering_method': clustering_method,
                'keywords_updated_at': datetime.now(timezone.utc).isoformat(),
                'updated_at': datetime.now(timezone.utc).isoformat()
            }
            
            result = self.supabase.table('subscriptions').update(update_data).eq('user_id', user_id).execute()
            
            # 同時更新用戶偏好
            self.update_user_preferences(user_id, focus_score, primary_topics)
            
            logger.info(f"Updated subscription with enhanced data for user {user_id}")
            return len(result.data) > 0
            
        except Exception as e:
            logger.error(f"Failed to update subscription with enhanced data for {user_id}: {e}")
            return False

# Create a global database manager instance
db_manager = DatabaseManager() 