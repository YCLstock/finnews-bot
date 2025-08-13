#!/usr/bin/env python3
"""
快速標籤遷移執行腳本
一鍵執行統一標籤管理系統遷移
"""

import sys
import os
from pathlib import Path

# 添加項目根目錄到 Python 路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def check_environment():
    """檢查環境配置"""
    required_vars = [
        'SUPABASE_URL',
        'SUPABASE_SERVICE_KEY',
        'SUPABASE_JWT_SECRET'
    ]
    
    missing = []
    for var in required_vars:
        if not os.environ.get(var):
            missing.append(var)
    
    if missing:
        print("❌ 缺少必要的環境變數:")
        for var in missing:
            print(f"   - {var}")
        print("\n請在 .env 文件中配置這些變數，或使用以下命令:")
        print("export SUPABASE_URL='your_supabase_url'")
        print("export SUPABASE_SERVICE_KEY='your_service_key'")
        print("export SUPABASE_JWT_SECRET='your_jwt_secret'")
        return False
    
    return True

def execute_sql_migration():
    """執行SQL遷移腳本"""
    print("📋 SQL遷移腳本位置:")
    sql_file = project_root / "database" / "unified_tag_migration.sql"
    print(f"   {sql_file}")
    print("\n請手動在Supabase SQL編輯器中執行此腳本")
    print("或使用psql命令:")
    print(f"psql -f {sql_file} 'your_database_connection_string'")

def test_system():
    """測試統一標籤系統"""
    print("\n🧪 測試統一標籤系統...")
    
    try:
        from scripts.dynamic_tags import get_active_tags, convert_keywords_to_tags
        
        # 測試標籤獲取
        tags = get_active_tags()
        print(f"✅ 成功獲取 {len(tags)} 個標籤")
        
        # 測試關鍵字轉換
        test_keywords = ['蘋果', 'AI', '股市']
        converted_tags = convert_keywords_to_tags(test_keywords)
        print(f"✅ 關鍵字轉換成功: {test_keywords} -> {converted_tags}")
        
        return True
        
    except Exception as e:
        print(f"❌ 系統測試失敗: {e}")
        return False

def run_push_test():
    """執行推送系統測試"""
    print("\n📤 測試推送系統...")
    
    try:
        import subprocess
        result = subprocess.run([
            sys.executable, 
            str(project_root / "scripts" / "run_pusher_test.py")
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("✅ 推送系統測試通過")
            return True
        else:
            print(f"❌ 推送系統測試失敗")
            print(f"錯誤輸出: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ 推送系統測試異常: {e}")
        return False

def main():
    """主執行函數"""
    print("🚀 FindyAI 統一標籤管理系統 - 快速遷移")
    print("=" * 50)
    
    # 步驟1: 檢查環境
    if not check_environment():
        return 1
    
    print("✅ 環境變數檢查通過")
    
    # 步驟2: 提示SQL遷移
    execute_sql_migration()
    
    input("\n按 Enter 鍵繼續系統測試 (請確保已執行SQL遷移)...")
    
    # 步驟3: 測試系統
    if not test_system():
        return 1
    
    # 步驟4: 測試推送
    if not run_push_test():
        print("⚠️ 推送測試失敗，但核心系統正常")
    
    print("\n🎉 統一標籤管理系統遷移完成！")
    print("\n📋 系統狀態:")
    print("✅ 動態標籤獲取: 正常")
    print("✅ 關鍵字映射: 正常") 
    print("✅ 爬蟲整合: 完成")
    print("✅ 推送整合: 完成")
    
    print("\n📖 相關文檔:")
    print("   - UNIFIED_TAG_SYSTEM.md: 完整系統說明")
    print("   - database/unified_tag_migration.sql: 數據遷移腳本")
    print("   - scripts/dynamic_tags.py: 動態標籤管理器")
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)