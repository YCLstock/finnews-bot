#!/usr/bin/env python3
"""
獨立推送腳本 - 只負責檢查訂閱和推送通知
執行頻率建議：每10分鐘
"""
import sys
import os
import time
import requests
import json
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime, timezone, timedelta

# 添加項目根目錄到 Python 路徑
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 載入環境變數
load_dotenv()

def log_message(message):
    """輸出帶時間戳的訊息"""
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] {message}")

def get_taiwan_time():
    """獲取台灣時間"""
    taiwan_tz = timezone(timedelta(hours=8))
    return datetime.now(taiwan_tz)

def get_active_subscriptions():
    """獲取所有活躍的訂閱"""
    supabase_url = os.environ.get('SUPABASE_URL')
    supabase_key = os.environ.get('SUPABASE_SERVICE_KEY')
    
    if not supabase_url or not supabase_key:
        log_message("Missing Supabase credentials")
        return []
    
    headers = {
        'apikey': supabase_key,
        'Authorization': f'Bearer {supabase_key}'
    }
    
    try:
        response = requests.get(
            f"{supabase_url}/rest/v1/subscriptions",
            headers=headers,
            params={'is_active': 'eq.true'},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            log_message(f"Found {len(data)} active subscriptions")
            return data
        else:
            log_message(f"Failed to get subscriptions: {response.status_code}")
            return []
            
    except Exception as e:
        log_message(f"Error getting subscriptions: {e}")
        return []

def should_push_now(subscription):
    """檢查是否應該推送（根據頻率和時間窗口）"""
    frequency_type = subscription.get('push_frequency_type', 'daily')
    last_push_window = subscription.get('last_push_window', '')
    
    # 推送時間配置
    push_schedules = {
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
    
    schedule = push_schedules.get(frequency_type, push_schedules['daily'])
    taiwan_time = get_taiwan_time()
    current_time = taiwan_time.strftime("%H:%M")
    today = taiwan_time.strftime("%Y-%m-%d")
    
    # 檢查是否在任何推送時間窗口內
    for push_time in schedule['times']:
        if is_within_time_window(current_time, push_time, schedule['window_minutes']):
            window_key = f"{today}-{push_time}"
            if last_push_window != window_key:
                return True, push_time, schedule['max_articles']
    
    return False, None, 0

def is_within_time_window(current_time, target_time, window_minutes):
    """檢查當前時間是否在目標時間窗口內"""
    try:
        current_hour, current_min = map(int, current_time.split(':'))
        target_hour, target_min = map(int, target_time.split(':'))
        
        current_total_min = current_hour * 60 + current_min
        target_total_min = target_hour * 60 + target_min
        
        diff = abs(current_total_min - target_total_min)
        
        # 處理跨午夜情況
        if diff > 12 * 60:
            diff = 24 * 60 - diff
        
        return diff <= window_minutes
    except:
        return False

def get_recent_articles(max_count, keywords=[]):
    """獲取最近的文章"""
    supabase_url = os.environ.get('SUPABASE_URL')
    supabase_key = os.environ.get('SUPABASE_SERVICE_KEY')
    
    if not supabase_url or not supabase_key:
        return []
    
    headers = {
        'apikey': supabase_key,
        'Authorization': f'Bearer {supabase_key}'
    }
    
    try:
        # 獲取最近24小時的文章
        yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
        
        params = {
            'select': 'id,title,summary,original_url,published_at',
            'published_at': f'gte.{yesterday}',
            'order': 'published_at.desc',
            'limit': max_count * 2  # 多取一些以便過濾
        }
        
        response = requests.get(
            f"{supabase_url}/rest/v1/news_articles",
            headers=headers,
            params=params,
            timeout=10
        )
        
        if response.status_code == 200:
            articles = response.json()
            
            # 如果有關鍵字，進行過濾
            if keywords:
                filtered_articles = []
                for article in articles:
                    title_lower = article['title'].lower()
                    summary_lower = article['summary'].lower()
                    
                    if any(keyword.lower() in title_lower or keyword.lower() in summary_lower 
                          for keyword in keywords):
                        filtered_articles.append(article)
                
                articles = filtered_articles
            
            return articles[:max_count]
        else:
            return []
            
    except Exception as e:
        log_message(f"Error getting articles: {e}")
        return []

def send_to_discord(webhook_url, articles, frequency_type):
    """發送文章到Discord"""
    if not webhook_url or not webhook_url.startswith("https://discord"):
        log_message("Invalid Discord webhook URL")
        return False
    
    success_count = 0
    for i, article in enumerate(articles):
        try:
            payload = {
                "embeds": [{
                    "title": f"📰 {article['title']}",
                    "description": article['summary'],
                    "color": 3447003,  # 藍色
                    "fields": [
                        {
                            "name": "🔗 原文連結",
                            "value": f"[點此閱讀完整內容]({article['original_url']})",
                            "inline": False
                        }
                    ],
                    "footer": {
                        "text": f"第 {i+1}/{len(articles)} 則 • {frequency_type.upper()} 推送 • {time.strftime('%Y-%m-%d %H:%M:%S')}"
                    },
                    "timestamp": time.strftime('%Y-%m-%dT%H:%M:%S.000Z')
                }]
            }
            
            response = requests.post(webhook_url, json=payload, timeout=15)
            response.raise_for_status()
            
            success_count += 1
            log_message(f"  Sent article {i+1}: {article['title'][:50]}...")
            
            # Discord API 限制間隔
            if i < len(articles) - 1:
                time.sleep(1.5)
                
        except Exception as e:
            log_message(f"  Failed to send article {i+1}: {e}")
    
    return success_count > 0

def mark_push_completed(user_id, push_time):
    """標記推送已完成"""
    supabase_url = os.environ.get('SUPABASE_URL')
    supabase_key = os.environ.get('SUPABASE_SERVICE_KEY')
    
    if not supabase_url or not supabase_key:
        return False
    
    headers = {
        'apikey': supabase_key,
        'Authorization': f'Bearer {supabase_key}',
        'Content-Type': 'application/json'
    }
    
    taiwan_time = get_taiwan_time()
    today = taiwan_time.strftime("%Y-%m-%d")
    window_key = f"{today}-{push_time}"
    
    try:
        update_data = {
            "last_push_window": window_key,
            "last_pushed_at": datetime.now(timezone.utc).isoformat()
        }
        
        response = requests.patch(
            f"{supabase_url}/rest/v1/subscriptions",
            headers=headers,
            json=update_data,
            params={'user_id': f'eq.{user_id}'},
            timeout=10
        )
        
        return response.status_code in [200, 204]
        
    except Exception as e:
        log_message(f"Error marking push completed: {e}")
        return False

def main():
    """主要執行函數"""
    log_message("=== FinNews-Bot Pusher Started ===")
    
    # 1. 獲取活躍訂閱
    subscriptions = get_active_subscriptions()
    if not subscriptions:
        log_message("No active subscriptions found")
        return
    
    # 2. 檢查每個訂閱
    push_count = 0
    
    for subscription in subscriptions:
        user_id = subscription.get('user_id')
        delivery_target = subscription.get('delivery_target')
        keywords = subscription.get('keywords', [])
        
        log_message(f"Checking subscription for user: {user_id}")
        
        # 檢查是否應該推送
        should_push, push_time, max_articles = should_push_now(subscription)
        
        if not should_push:
            log_message("  Not in push time window, skipping")
            continue
        
        log_message(f"  Push time window: {push_time}, max articles: {max_articles}")
        
        # 獲取文章
        articles = get_recent_articles(max_articles, keywords)
        if not articles:
            log_message("  No recent articles found")
            continue
        
        log_message(f"  Found {len(articles)} articles to push")
        
        # 發送到Discord
        if send_to_discord(delivery_target, articles, subscription.get('push_frequency_type', 'daily')):
            # 標記推送完成
            if mark_push_completed(user_id, push_time):
                log_message(f"  Push completed successfully for user {user_id}")
                push_count += 1
            else:
                log_message(f"  Push sent but failed to mark as completed")
        else:
            log_message(f"  Failed to send push for user {user_id}")
    
    log_message(f"=== Pusher Completed ===")
    log_message(f"Successful pushes: {push_count}/{len(subscriptions)}")

if __name__ == "__main__":
    main()