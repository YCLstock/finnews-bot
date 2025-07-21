#!/usr/bin/env python3
"""
FinNews-Bot 完整調度器
整合新聞爬取、關鍵字同步、推送等所有定時任務
"""
import sys
import os
import time
import schedule
from pathlib import Path
from datetime import datetime

# 添加項目根目錄到 Python 路徑
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from services.keyword_sync_service import keyword_sync_service
from scraper.scraper import scraper_manager
from core.utils import get_current_taiwan_time, format_taiwan_datetime

def run_keyword_sync():
    """執行關鍵字同步任務"""
    print("\n" + "="*50)
    print("Starting keyword sync task...")
    taiwan_time = get_current_taiwan_time()
    print(f"Execution time: {format_taiwan_datetime(taiwan_time)}")
    
    try:
        success = keyword_sync_service.process_all_pending()
        if success:
            print("Keyword sync task completed successfully")
        else:
            print("Keyword sync task partially failed")
    except Exception as e:
        print(f"Keyword sync task failed: {e}")
    
    print("="*50)

def run_news_processing():
    """執行新聞處理和推送任務"""
    print("\n" + "="*50)
    print("Starting news processing task...")
    taiwan_time = get_current_taiwan_time()
    print(f"Execution time: {format_taiwan_datetime(taiwan_time)}")
    
    try:
        success = scraper_manager.process_news_for_subscriptions()
        if success:
            print("News processing task completed successfully")
        else:
            print("News processing task completed, but no new pushes")
    except Exception as e:
        print(f"News processing task failed: {e}")
    
    print("="*50)

def setup_scheduler():
    """設置所有定時任務"""
    
    # 關鍵字同步任務：每小時執行
    schedule.every().hour.do(run_keyword_sync)
    
    # 新聞處理任務：在推送時間點執行
    # 每日早上 8:00
    schedule.every().day.at("08:00").do(run_news_processing)
    
    # 每日下午 1:00（for twice/thrice 用戶）
    schedule.every().day.at("13:00").do(run_news_processing)
    
    # 每日晚上 8:00
    schedule.every().day.at("20:00").do(run_news_processing)
    
    print("Scheduled tasks configured:")
    print("  - Keyword sync: Every hour")
    print("  - News processing: Daily at 08:00, 13:00, 20:00")

def run_scheduler():
    """運行調度器主循環"""
    print("FinNews-Bot Scheduler Starting...")
    print(f"Start time: {format_taiwan_datetime(get_current_taiwan_time())}")
    
    setup_scheduler()
    
    print("\nScheduler running, press Ctrl+C to stop...")
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # 每分鐘檢查一次
            
    except KeyboardInterrupt:
        print("\n\nReceived stop signal, shutting down scheduler...")
        print(f"Stop time: {format_taiwan_datetime(get_current_taiwan_time())}")
        print("Scheduler safely closed")

def run_immediate_test():
    """立即執行測試（調試用）"""
    print("Immediate test mode")
    
    print("\n1. Testing keyword sync...")
    run_keyword_sync()
    
    print("\n2. Testing news processing...")
    run_news_processing()
    
    print("\nTest completed")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "--test":
            run_immediate_test()
        elif sys.argv[1] == "--keyword-sync":
            run_keyword_sync()
        elif sys.argv[1] == "--news":
            run_news_processing()
        else:
            print("Usage:")
            print("  python scheduler.py           # Run full scheduler")
            print("  python scheduler.py --test    # Test all tasks immediately")
            print("  python scheduler.py --keyword-sync  # Test keyword sync only")
            print("  python scheduler.py --news    # Test news processing only")
    else:
        run_scheduler()