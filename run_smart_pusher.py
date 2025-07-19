#!/usr/bin/env python3
"""
智能推送器 - 基於已存儲文章的推送系統
不進行爬取，只從資料庫中選擇合適的文章進行推送
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any

# 添加項目根目錄到 Python 路徑
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.config import settings
from core.database import db_manager
from core.utils import get_current_taiwan_time, format_taiwan_datetime, send_batch_to_discord, create_push_summary_message

class SmartPusher:
    """智能推送器 - 基於已存儲文章"""
    
    def __init__(self):
        pass
    
    def get_eligible_articles_for_user(self, subscription: Dict[str, Any], hours_limit: int = 6) -> List[Dict[str, Any]]:
        """為特定用戶獲取符合條件的文章"""
        user_id = subscription['user_id']
        keywords = subscription.get('keywords', [])
        frequency_type = subscription.get('push_frequency_type', 'daily')
        max_articles = db_manager.get_max_articles_for_frequency(frequency_type)
        
        print(f"🔍 為用戶 {user_id[:8]}... 選擇文章 (最多 {max_articles} 篇)")
        
        try:
            # 計算時間範圍（只推送最近N小時的文章）
            cutoff_time = get_current_taiwan_time() - timedelta(hours=hours_limit)
            cutoff_iso = cutoff_time.isoformat()
            
            # 從資料庫查詢文章
            query_builder = db_manager.supabase.table("news_articles").select("*")
            
            # 時間過濾
            query_builder = query_builder.gte("published_at", cutoff_iso)
            
            # 排序：最新的優先
            query_builder = query_builder.order("published_at", desc=True)
            
            # 限制數量（查詢更多，以便有篩選空間）
            query_builder = query_builder.limit(max_articles * 3)
            
            result = query_builder.execute()
            all_articles = result.data if result.data else []
            
            print(f"📊 查詢到 {len(all_articles)} 篇最近 {hours_limit} 小時的文章")
            
            if not all_articles:
                print(f"📭 沒有找到最近 {hours_limit} 小時的文章")
                return []
            
            # 檢查用戶已推送過的文章
            pushed_articles = self.get_user_pushed_articles(user_id, hours_limit * 2)  # 檢查更長時間避免重複
            pushed_urls = {article.get('news_articles', {}).get('original_url') for article in pushed_articles}
            
            # 過濾已推送的文章
            unread_articles = [article for article in all_articles 
                             if article['original_url'] not in pushed_urls]
            
            print(f"📋 過濾後未推送文章: {len(unread_articles)} 篇")
            
            if not unread_articles:
                print(f"📭 沒有新的未推送文章")
                return []
            
            # 根據關鍵字篩選和排序
            selected_articles = self.select_articles_by_preference(unread_articles, keywords, max_articles)
            
            print(f"✅ 最終選擇文章: {len(selected_articles)} 篇")
            return selected_articles
            
        except Exception as e:
            print(f"❌ 獲取用戶文章時發生錯誤: {e}")
            return []
    
    def get_user_pushed_articles(self, user_id: str, hours_limit: int = 12) -> List[Dict[str, Any]]:
        """獲取用戶最近推送過的文章"""
        try:
            cutoff_time = get_current_taiwan_time() - timedelta(hours=hours_limit)
            cutoff_iso = cutoff_time.isoformat()
            
            result = db_manager.supabase.table("push_history").select(
                "*, news_articles(original_url)"
            ).eq("user_id", user_id).gte("pushed_at", cutoff_iso).execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            print(f"❌ 獲取用戶推送歷史錯誤: {e}")
            return []
    
    def select_articles_by_preference(self, articles: List[Dict[str, Any]], keywords: List[str], max_count: int) -> List[Dict[str, Any]]:
        """根據用戶偏好選擇文章"""
        if not articles:
            return []
        
        # 如果沒有關鍵字，返回最新的文章
        if not keywords:
            print(f"📰 用戶無關鍵字，選擇最新 {max_count} 篇通用財經新聞")
            return articles[:max_count]
        
        print(f"🎯 根據關鍵字篩選: {', '.join(keywords)}")
        
        # 分類文章：關鍵字匹配 vs 通用
        keyword_matches = []
        general_articles = []
        
        keywords_lower = [kw.lower().strip() for kw in keywords]
        
        for article in articles:
            title_lower = article['title'].lower()
            summary_lower = article.get('summary', '').lower()
            
            # 檢查標題和摘要中的關鍵字匹配
            matched = any(kw in title_lower or kw in summary_lower for kw in keywords_lower)
            
            if matched:
                keyword_matches.append(article)
            else:
                general_articles.append(article)
        
        print(f"📊 關鍵字匹配文章: {len(keyword_matches)} 篇")
        print(f"📊 通用文章: {len(general_articles)} 篇")
        
        # 選擇策略：優先關鍵字匹配，不足時補充通用文章
        selected = []
        
        # 1. 添加關鍵字匹配的文章
        selected.extend(keyword_matches[:max_count])
        
        # 2. 如果不足，添加通用文章
        remaining_slots = max_count - len(selected)
        if remaining_slots > 0:
            selected.extend(general_articles[:remaining_slots])
            print(f"📝 補充 {min(remaining_slots, len(general_articles))} 篇通用文章")
        
        return selected
    
    def process_user_subscription(self, subscription: Dict[str, Any]) -> bool:
        """處理單個用戶的推送"""
        user_id = subscription['user_id']
        frequency_type = subscription.get('push_frequency_type', 'daily')
        
        print(f"\n--- ⚙️ 處理用戶 {user_id[:8]}... 的推送 ({frequency_type}) ---")
        
        # 檢查推送時機
        if not db_manager.should_push_now(subscription):
            print(f"⏭️ 用戶 {user_id[:8]}... 不在推送時間窗口")
            return False
        
        # 獲取合適的文章
        articles = self.get_eligible_articles_for_user(subscription, hours_limit=6)
        
        # 檢查是否有足夠的文章（至少需要1篇）
        min_articles = 1
        if len(articles) < min_articles:
            print(f"📭 用戶 {user_id[:8]}... 沒有足夠的新文章 (需要至少 {min_articles} 篇)")
            print(f"⏭️ 跳過本次推送，等待下次推送時間")
            return False
        
        # 推送到 Discord
        print(f"📤 開始推送 {len(articles)} 篇文章到 Discord...")
        success, failed_articles = send_batch_to_discord(
            subscription['delivery_target'],
            articles,
            subscription
        )
        
        if success:
            # 記錄推送歷史
            successful_articles = [article for article in articles if article not in failed_articles]
            
            # 獲取文章ID並記錄推送歷史
            article_ids = []
            for article in successful_articles:
                # 由於文章已在資料庫中，我們需要通過URL查找ID
                try:
                    result = db_manager.supabase.table("news_articles").select("id").eq(
                        "original_url", article['original_url']
                    ).execute()
                    
                    if result.data:
                        article_ids.append(result.data[0]['id'])
                except Exception as e:
                    print(f"⚠️ 查找文章ID失敗: {e}")
            
            if article_ids:
                # 批量記錄推送歷史
                batch_success = db_manager.log_push_history(user_id, article_ids)
                if batch_success:
                    print(f"📝 已記錄推送歷史: {len(article_ids)} 篇文章")
                
                # 標記推送窗口為已完成
                db_manager.mark_push_window_completed(user_id, frequency_type)
                
                # 發送推送總結消息
                create_push_summary_message(
                    subscription['delivery_target'],
                    len(successful_articles),
                    len(articles),
                    frequency_type
                )
                
                print(f"🎉 用戶 {user_id[:8]}... 推送完成: {len(successful_articles)} 篇成功")
                return True
        
        print(f"❌ 用戶 {user_id[:8]}... 推送失敗")
        return False
    
    def run_smart_push(self) -> bool:
        """執行智能推送"""
        print("=" * 60)
        print("🚀 FinNews-Bot 智能推送器開始執行")
        taiwan_time = get_current_taiwan_time()
        print(f"🕐 執行時間: {format_taiwan_datetime(taiwan_time)}")
        print("=" * 60)
        
        try:
            # 驗證環境變數
            settings.validate()
            print("✅ 環境變數驗證成功")
            
            # 獲取符合推送條件的訂閱
            eligible_subscriptions = db_manager.get_eligible_subscriptions()
            
            if not eligible_subscriptions:
                print("\nℹ️ 目前沒有符合推送時間的訂閱需要處理")
                print("💡 提示: 系統會在 08:00, 13:00, 20:00 (±30分鐘) 進行推送檢查")
                return True  # 這不算失敗
            
            print(f"\n📊 本次推送分析:")
            print(f"  - 符合推送條件的訂閱: {len(eligible_subscriptions)} 個")
            
            # 按推送頻率類型分組顯示
            freq_stats = {}
            for sub in eligible_subscriptions:
                freq = sub.get('push_frequency_type', 'daily')
                freq_stats[freq] = freq_stats.get(freq, 0) + 1
            
            for freq, count in freq_stats.items():
                print(f"    * {freq}: {count} 個訂閱")
            
            # 處理每個符合條件的訂閱
            overall_success = False
            success_count = 0
            
            for subscription in eligible_subscriptions:
                success = self.process_user_subscription(subscription)
                if success:
                    overall_success = True
                    success_count += 1
            
            print(f"\n📊 推送結果統計:")
            print(f"  - 處理訂閱: {len(eligible_subscriptions)} 個")
            print(f"  - 推送成功: {success_count} 個")
            print(f"  - 推送失敗: {len(eligible_subscriptions) - success_count} 個")
            
            if overall_success:
                print(f"\n🎉 智能推送任務完成！{success_count} 個用戶收到新聞")
            else:
                print(f"\n⚠️ 智能推送完成，但沒有成功推送任何內容")
                print("💡 可能原因: 沒有足夠的新文章，或用戶已在此時間窗口收到推送")
            
            return True
            
        except Exception as e:
            print(f"\n❌ 智能推送任務失敗: {e}")
            import traceback
            traceback.print_exc()
            return False
            
        finally:
            print("\n" + "=" * 60)
            print("🏁 FinNews-Bot 智能推送器結束")
            taiwan_time = get_current_taiwan_time()
            print(f"⏰ 結束時間: {format_taiwan_datetime(taiwan_time)}")
            print("=" * 60)

def main():
    """主執行函數"""
    pusher = SmartPusher()
    success = pusher.run_smart_push()
    return 0 if success else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)