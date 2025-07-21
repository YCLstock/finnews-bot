#!/usr/bin/env python3
"""
獨立的爬蟲執行程式
用於 Render Cron Job 或其他排程系統
支援智能推送頻率控制和批量處理
"""

import sys
import os
from pathlib import Path
from datetime import datetime

# 添加項目根目錄到 Python 路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scraper.scraper import scraper_manager
from core.config import settings
from core.database import db_manager
from core.utils import get_current_taiwan_time, format_taiwan_datetime

def main():
    """主執行函數 - 智能推送版本"""
    print("=" * 60)
    print("🚀 FinNews-Bot 智能推送排程開始執行")
    taiwan_time = get_current_taiwan_time()
    print(f"🕐 執行時間: {format_taiwan_datetime(taiwan_time)}")
    print("=" * 60)
    
    try:
        # 驗證環境變數
        settings.validate()
        print("✅ 環境變數驗證成功")
        
        # 檢查當前時間和符合條件的訂閱
        print("\n🔍 分析當前推送條件...")
        taiwan_time = get_current_taiwan_time()
        current_time = taiwan_time.strftime("%H:%M")
        print(f"當前時間 (台灣): {current_time}")
        
        # 顯示推送時間配置
        print("\n📋 推送時間配置:")
        for freq_type, config in db_manager.PUSH_SCHEDULES.items():
            times_str = ", ".join(config['times'])
            print(f"  - {freq_type}: {times_str} (最多 {config['max_articles']} 篇)")
        
        # 獲取符合推送條件的訂閱
        eligible_subscriptions = db_manager.get_eligible_subscriptions()
        
        if not eligible_subscriptions:
            print("\nℹ️ 目前沒有符合推送時間的訂閱需要處理")
            print("💡 提示: 系統會在 08:00, 13:00, 20:00 (±30分鐘) 進行推送檢查")
            return 0
        
        print(f"\n📊 本次推送分析:")
        print(f"  - 符合推送條件的訂閱: {len(eligible_subscriptions)} 個")
        
        # 按推送頻率類型分組顯示
        freq_stats = {}
        for sub in eligible_subscriptions:
            freq = sub.get('push_frequency_type', 'daily')
            freq_stats[freq] = freq_stats.get(freq, 0) + 1
        
        for freq, count in freq_stats.items():
            print(f"    * {freq}: {count} 個訂閱")
        
        # 執行智能爬蟲任務
        print(f"\n🎯 開始執行批量推送任務...")
        success = scraper_manager.process_news_for_subscriptions()
        
        if success:
            print("\n🎉 智能推送排程執行成功")
            print("📊 已完成本輪推送，用戶將收到最新的財經新聞摘要")
            return 0
        else:
            print("\n⚠️ 智能推送排程執行完成，但沒有推送任何新聞")
            print("💡 可能原因: 沒有符合關鍵字的新文章，或用戶已在此時間窗口收到推送")
            return 0
            
    except Exception as e:
        print(f"\n❌ 智能推送排程執行失敗: {e}")
        import traceback
        traceback.print_exc()
        
        # 在失敗時也顯示一些有用的調試信息
        try:
            print(f"\n🔧 調試信息:")
            taiwan_time = get_current_taiwan_time()
            print(f"  - 當前時間: {format_taiwan_datetime(taiwan_time)}")
            active_subs = db_manager.get_active_subscriptions()
            print(f"  - 活躍訂閱總數: {len(active_subs)}")
            
            # 顯示每個訂閱的推送狀態
            for sub in active_subs[:3]:  # 只顯示前3個
                freq = sub.get('push_frequency_type', 'daily')
                should_push = db_manager.should_push_now(sub)
                print(f"  - 用戶 {sub['user_id'][:8]}...: {freq} -> {'可推送' if should_push else '不可推送'}")
                
        except Exception as debug_error:
            print(f"  調試信息獲取失敗: {debug_error}")
        
        return 1
    
    finally:
        print("\n" + "=" * 60)
        print("🏁 FinNews-Bot 智能推送排程結束")
        taiwan_time = get_current_taiwan_time()
        print(f"⏰ 結束時間: {format_taiwan_datetime(taiwan_time)}")
        print("=" * 60)

def check_push_schedule():
    """檢查推送排程狀態（調試用）"""
    print("🔍 推送排程狀態檢查")
    print("-" * 40)
    
    try:
        taiwan_time = get_current_taiwan_time()
        current_time = taiwan_time.strftime("%H:%M")
        print(f"當前時間 (台灣): {current_time}")
        
        all_subs = db_manager.get_active_subscriptions()
        print(f"活躍訂閱總數: {len(all_subs)}")
        
        eligible_subs = db_manager.get_eligible_subscriptions()
        print(f"符合推送條件: {len(eligible_subs)}")
        
        print("\n詳細分析:")
        for sub in all_subs:
            user_id = sub['user_id'][:8] + "..."
            freq = sub.get('push_frequency_type', 'daily')
            last_window = sub.get('last_push_window', 'Never')
            should_push = db_manager.should_push_now(sub)
            
            print(f"  {user_id} | {freq} | 上次: {last_window} | {'✅' if should_push else '❌'}")
            
    except Exception as e:
        print(f"❌ 檢查失敗: {e}")

if __name__ == "__main__":
    # 支援調試模式
    if len(sys.argv) > 1 and sys.argv[1] == "--check":
        check_push_schedule()
    else:
        exit_code = main()
        sys.exit(exit_code) 