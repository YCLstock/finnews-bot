"""
AWS Lambda函數 - 智能推送
負責：根據用戶訂閱設定推送相關新聞
"""
import json
import os
import sys
from pathlib import Path

# 添加專案根目錄到路徑
sys.path.append(str(Path(__file__).parent.parent.parent))

from core.database import db_manager
from core.utils import get_current_taiwan_time, send_batch_to_discord

def lambda_handler(event, context):
    """Lambda主入口函數"""
    
    print("🚀 AWS Lambda 智能推送開始執行")
    taiwan_time = get_current_taiwan_time()
    print(f"🕐 執行時間: {taiwan_time.strftime('%Y-%m-%d %H:%M:%S')} (台灣時間)")
    
    try:
        # 檢查環境變數
        required_vars = ['SUPABASE_URL', 'SUPABASE_SERVICE_KEY']
        for var in required_vars:
            if not os.environ.get(var):
                raise ValueError(f"缺少環境變數: {var}")
        
        # 獲取符合推送條件的訂閱
        eligible_subscriptions = db_manager.get_eligible_subscriptions()
        
        if not eligible_subscriptions:
            print("📭 目前沒有符合推送條件的訂閱")
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': '沒有符合推送條件的訂閱',
                    'push_count': 0
                })
            }
        
        print(f"📋 找到 {len(eligible_subscriptions)} 個符合推送條件的訂閱")
        
        success_count = 0
        
        for subscription in eligible_subscriptions:
            user_id = subscription['user_id']
            frequency_type = subscription.get('push_frequency_type', 'daily')
            keywords = subscription.get('keywords', [])
            discord_webhook = subscription.get('discord_webhook_url')
            
            if not discord_webhook:
                print(f"⚠️ 用戶 {user_id} 沒有設置Discord webhook")
                continue
            
            print(f"📤 處理用戶 {user_id} 的推送 (頻率: {frequency_type})")
            
            # 獲取相關文章
            articles = get_articles_for_user(subscription)
            
            if not articles:
                print(f"📭 用戶 {user_id} 沒有相關的新文章")
                continue
            
            # 推送到Discord
            try:
                result = send_batch_to_discord(
                    webhook_url=discord_webhook,
                    articles=articles,
                    user_keywords=keywords
                )
                
                if result:
                    # 記錄推送歷史
                    article_ids = [article.get('id') for article in articles if article.get('id')]
                    db_manager.log_push_history(user_id, article_ids)
                    
                    # 標記推送窗口完成
                    db_manager.mark_push_window_completed(user_id, frequency_type)
                    
                    success_count += 1
                    print(f"✅ 用戶 {user_id} 推送成功")
                else:
                    print(f"❌ 用戶 {user_id} 推送失敗")
                    
            except Exception as push_error:
                print(f"❌ 用戶 {user_id} 推送異常: {push_error}")
                continue
        
        print(f"🎉 推送任務完成！成功推送 {success_count} 個用戶")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': f'成功推送 {success_count} 個用戶',
                'push_count': success_count,
                'execution_time': taiwan_time.isoformat()
            })
        }
        
    except Exception as e:
        print(f"❌ 推送執行失敗: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'execution_time': taiwan_time.isoformat()
            })
        }

def get_articles_for_user(subscription):
    """為用戶獲取相關文章"""
    try:
        user_keywords = subscription.get('keywords', [])
        frequency_type = subscription.get('push_frequency_type', 'daily')
        max_articles = db_manager.get_max_articles_for_frequency(frequency_type)
        
        # 從資料庫獲取最新文章
        # 這裡需要實現根據關鍵字篩選的邏輯
        articles = db_manager.get_recent_articles_for_keywords(
            keywords=user_keywords,
            limit=max_articles
        )
        
        return articles
        
    except Exception as e:
        print(f"❌ 獲取用戶文章失敗: {e}")
        return []