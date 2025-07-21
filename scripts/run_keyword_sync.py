#!/usr/bin/env python3
"""
關鍵字同步定時任務
每小時執行一次，檢查用戶關鍵字變動並轉換為AI標籤
"""
import sys
import os
from pathlib import Path
from datetime import datetime

# 添加項目根目錄到 Python 路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from services.keyword_sync_service import keyword_sync_service
from core.config import settings
from core.utils import get_current_taiwan_time, format_taiwan_datetime

def main():
    """主執行函數 - 關鍵字同步任務"""
    print("=" * 60)
    print("🔄 FinNews-Bot 關鍵字同步任務開始執行")
    taiwan_time = get_current_taiwan_time()
    print(f"🕐 執行時間: {format_taiwan_datetime(taiwan_time)}")
    print("=" * 60)
    
    try:
        # 驗證環境變數
        settings.validate()
        print("✅ 環境變數驗證成功")
        
        # 執行關鍵字同步服務
        print("\n🚀 開始執行關鍵字同步...")
        success = keyword_sync_service.process_all_pending()
        
        if success:
            print("\n🎉 關鍵字同步任務執行成功")
            print("📊 所有用戶標籤已更新至最新狀態")
            return 0
        else:
            print("\n⚠️ 關鍵字同步任務完成，但部分處理失敗")
            return 1
            
    except Exception as e:
        print(f"\n❌ 關鍵字同步任務執行失敗: {e}")
        import traceback
        traceback.print_exc()
        
        return 1
    
    finally:
        print("\n" + "=" * 60)
        print("🏁 FinNews-Bot 關鍵字同步任務結束")
        taiwan_time = get_current_taiwan_time()
        print(f"⏰ 結束時間: {format_taiwan_datetime(taiwan_time)}")
        print("=" * 60)

def check_sync_status():
    """檢查同步狀態（調試用）"""
    print("關鍵字同步狀態檢查")
    print("-" * 40)
    
    try:
        from core.database import db_manager
        
        taiwan_time = get_current_taiwan_time()
        print(f"當前時間 (台灣): {taiwan_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 檢查需要更新的用戶
        outdated_users = db_manager.get_users_with_outdated_tags()
        print(f"需要更新標籤的用戶: {len(outdated_users)}")
        
        # 檢查所有活躍用戶
        all_users = db_manager.get_active_subscriptions()
        print(f"活躍用戶總數: {len(all_users)}")
        
        print("\n詳細分析:")
        for user in all_users[:5]:  # 只顯示前5個
            user_id = user['user_id'][:8] + "..."
            keywords = user.get('original_keywords', [])
            tags = user.get('subscribed_tags', [])
            keywords_time = user.get('keywords_updated_at', 'Never')
            tags_time = user.get('tags_updated_at', 'Never')
            
            needs_update = user in outdated_users
            
            print(f"  {user_id} | Keywords: {len(keywords)} | Tags: {len(tags)} | {'Need Update' if needs_update else 'Up-to-date'}")
            print(f"    Keywords time: {keywords_time}")
            print(f"    Tags time: {tags_time}")
            
    except Exception as e:
        print(f"Check failed: {e}")

if __name__ == "__main__":
    # 支援調試模式
    if len(sys.argv) > 1 and sys.argv[1] == "--check":
        check_sync_status()
    else:
        exit_code = main()
        sys.exit(exit_code)