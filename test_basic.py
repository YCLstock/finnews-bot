#!/usr/bin/env python3
"""
基本功能測試腳本
"""
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# 添加項目根目錄到 Python 路徑
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 載入環境變數
load_dotenv()

def test_core_imports():
    """測試核心模組導入"""
    print("=== Testing Core Imports ===")
    
    try:
        from core.config import settings
        print("OK: core.config imported")
    except Exception as e:
        print(f"FAIL: core.config - {e}")
    
    try:
        from core.utils import get_current_taiwan_time
        print("OK: core.utils imported")
    except Exception as e:
        print(f"FAIL: core.utils - {e}")
    
    try:
        from scraper.scraper import NewsScraperManager
        print("OK: scraper.scraper imported")
    except Exception as e:
        print(f"FAIL: scraper.scraper - {e}")

def test_basic_functions():
    """測試基本功能"""
    print("\n=== Testing Basic Functions ===")
    
    try:
        from core.utils import get_current_taiwan_time, validate_discord_webhook
        
        # 測試時間功能
        taiwan_time = get_current_taiwan_time()
        print(f"Taiwan time: {taiwan_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 測試webhook驗證
        test_webhook = 'https://discord.com/api/webhooks/123/abc'
        is_valid = validate_discord_webhook(test_webhook)
        print(f"Webhook validation: {is_valid}")
        
    except Exception as e:
        print(f"Basic functions failed: {e}")

def test_scraper_init():
    """測試爬蟲初始化"""
    print("\n=== Testing Scraper Initialization ===")
    
    try:
        from scraper.scraper import NewsScraperManager
        scraper = NewsScraperManager()
        print("Scraper initialized successfully")
        print(f"Debug folder exists: {scraper.debug_folder.exists()}")
    except Exception as e:
        print(f"Scraper initialization failed: {e}")

def test_environment():
    """測試環境變數"""
    print("\n=== Testing Environment Variables ===")
    
    required_vars = ['SUPABASE_URL', 'SUPABASE_SERVICE_KEY', 'OPENAI_API_KEY']
    for var in required_vars:
        value = os.environ.get(var)
        if value:
            print(f"OK {var}: Set ({value[:20]}...)")
        else:
            print(f"MISSING {var}: Not set")

if __name__ == "__main__":
    print("FinNews-Bot Basic Function Test")
    print("=" * 50)
    
    test_environment()
    test_core_imports()
    test_basic_functions()
    test_scraper_init()
    
    print("\n" + "=" * 50)
    print("Test completed!")