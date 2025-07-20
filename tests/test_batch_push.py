#!/usr/bin/env python3
"""
測試批量推送和時間窗口功能
用於功能驗證和調試
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
import uuid

# 添加項目根目錄到 Python 路徑
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 設置測試環境變數
os.environ["SUPABASE_URL"] = "https://gbobozzqoqfhqmttwzwn.supabase.co"
os.environ["SUPABASE_JWT_SECRET"] = "gpOhsTetmP5/UvTJCY4fNTSPvECvkbqfo83LCIYHYHRyxCEaXgDoWVSeDJOOUhhyFlUoTi8Ta9zXY0Gv8jFdkQ=="

from core.database import db_manager
from core.utils import send_batch_to_discord

def test_time_window_logic():
    """測試時間窗口邏輯"""
    print("🕐 測試時間窗口邏輯")
    print("=" * 40)
    
    # 測試不同時間點
    test_times = [
        ("07:30", "08:00", 30, True),   # 邊界內
        ("08:15", "08:00", 30, True),   # 邊界內
        ("08:35", "08:00", 30, False),  # 邊界外
        ("09:00", "08:00", 30, False),  # 邊界外
        ("12:45", "13:00", 30, True),   # 另一個窗口
        ("19:45", "20:00", 30, True),   # 晚間窗口
    ]
    
    for current, target, window, expected in test_times:
        result = db_manager.is_within_time_window(current, target, window)
        status = "✅" if result == expected else "❌"
        print(f"{status} {current} vs {target} (±{window}min): {result} (預期: {expected})")
    
    print()

def test_frequency_config():
    """測試推送頻率配置"""
    print("📋 測試推送頻率配置")
    print("=" * 40)
    
    for freq_type, config in db_manager.PUSH_SCHEDULES.items():
        print(f"{freq_type.upper()}:")
        print(f"  推送時間: {', '.join(config['times'])}")
        print(f"  時間窗口: ±{config['window_minutes']} 分鐘")
        print(f"  最大文章: {config['max_articles']} 篇")
        print()

def test_current_time_window():
    """測試當前時間窗口檢測"""
    print("🔍 測試當前時間窗口檢測")
    print("=" * 40)
    
    current_time = datetime.now().strftime("%H:%M")
    print(f"當前時間: {current_time}")
    
    for freq_type in ['daily', 'twice', 'thrice']:
        window = db_manager.get_current_time_window(current_time, freq_type)
        if window:
            print(f"✅ {freq_type}: 在推送窗口 {window}")
        else:
            print(f"❌ {freq_type}: 不在推送窗口")
    
    print()

def main():
    """主測試函數"""
    print("🧪 開始測試批量推送和時間窗口功能")
    print("=" * 60)
    
    tests = [
        ("時間窗口邏輯", test_time_window_logic),
        ("推送頻率配置", test_frequency_config),
        ("當前時間窗口檢測", test_current_time_window),
    ]
    
    for test_name, test_func in tests:
        print(f"\n🔸 執行測試: {test_name}")
        try:
            test_func()
            print(f"✅ {test_name} - 完成")
        except Exception as e:
            print(f"❌ {test_name} - 失敗: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("📊 核心功能測試完畢")
    print("\n💡 提示:")
    print("  - 使用 'python run_scraper.py --check' 檢查推送狀態")
    print("  - 使用 'python run_scraper.py' 執行智能推送")

if __name__ == "__main__":
    main() 