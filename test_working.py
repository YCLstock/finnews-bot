#!/usr/bin/env python3
"""
實用的系統測試 - 測試核心功能是否正常運作
"""
import sys
import os
import time
import requests
import json
from pathlib import Path
from dotenv import load_dotenv

# 添加項目根目錄到 Python 路徑
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 載入環境變數
load_dotenv()

def test_environment():
    """測試環境設定"""
    print("=== Environment Test ===")
    
    required_vars = {
        'SUPABASE_URL': os.environ.get('SUPABASE_URL'),
        'SUPABASE_SERVICE_KEY': os.environ.get('SUPABASE_SERVICE_KEY'),
        'OPENAI_API_KEY': os.environ.get('OPENAI_API_KEY')
    }
    
    all_good = True
    for var_name, var_value in required_vars.items():
        if var_value:
            print(f"✓ {var_name}: Set")
        else:
            print(f"✗ {var_name}: Missing")
            all_good = False
    
    return all_good

def test_web_request():
    """測試基本網路請求"""
    print("\\n=== Web Request Test ===")
    
    try:
        response = requests.get('https://httpbin.org/json', timeout=10)
        if response.status_code == 200:
            print("✓ Basic HTTP request: Working")
            return True
        else:
            print(f"✗ Basic HTTP request: Failed ({response.status_code})")
            return False
    except Exception as e:
        print(f"✗ Basic HTTP request: Exception ({e})")
        return False

def test_openai_api():
    """測試OpenAI API"""
    print("\\n=== OpenAI API Test ===")
    
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        print("✗ OpenAI API: No API key")
        return False
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    data = {
        'model': 'gpt-3.5-turbo',
        'messages': [
            {'role': 'user', 'content': 'Say "API test successful" in Traditional Chinese.'}
        ],
        'max_tokens': 50
    }
    
    try:
        response = requests.post('https://api.openai.com/v1/chat/completions', 
                               headers=headers, 
                               json=data, 
                               timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            message = result['choices'][0]['message']['content']
            print(f"✓ OpenAI API: Working ({message.strip()})")
            return True
        else:
            print(f"✗ OpenAI API: Failed ({response.status_code})")
            return False
            
    except Exception as e:
        print(f"✗ OpenAI API: Exception ({e})")
        return False

def test_supabase_db():
    """測試Supabase資料庫"""
    print("\\n=== Supabase Database Test ===")
    
    url = os.environ.get('SUPABASE_URL')
    key = os.environ.get('SUPABASE_SERVICE_KEY')
    
    if not url or not key:
        print("✗ Supabase: Missing credentials")
        return False
    
    headers = {
        'apikey': key,
        'Authorization': f'Bearer {key}',
        'Content-Type': 'application/json'
    }
    
    try:
        # 測試基本連接
        response = requests.get(f'{url}/rest/v1/', headers=headers, timeout=10)
        if response.status_code != 200:
            print(f"✗ Supabase: Connection failed ({response.status_code})")
            return False
        
        # 測試訂閱表
        response = requests.get(f'{url}/rest/v1/subscriptions', 
                              headers=headers, 
                              params={'limit': 1}, 
                              timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Supabase: Working ({len(data)} subscriptions found)")
            return True
        else:
            print(f"✗ Supabase: Table access failed ({response.status_code})")
            return False
            
    except Exception as e:
        print(f"✗ Supabase: Exception ({e})")
        return False

def test_article_save():
    """測試文章儲存功能"""
    print("\\n=== Article Save Test ===")
    
    url = os.environ.get('SUPABASE_URL')
    key = os.environ.get('SUPABASE_SERVICE_KEY')
    
    if not url or not key:
        print("✗ Article Save: Missing credentials")
        return False
    
    headers = {
        'apikey': key,
        'Authorization': f'Bearer {key}',
        'Content-Type': 'application/json'
    }
    
    # 創建測試文章
    test_article = {
        'original_url': f'https://test.example.com/article-{int(time.time())}',
        'source': 'test',
        'title': 'Test Article - System Check',
        'summary': 'This is a test article created by the system check.',
        'published_at': time.strftime('%Y-%m-%dT%H:%M:%SZ')
    }
    
    try:
        response = requests.post(f'{url}/rest/v1/news_articles', 
                               headers=headers, 
                               json=test_article,
                               timeout=10)
        
        if response.status_code in [200, 201]:
            print("✓ Article Save: Working")
            return True
        else:
            print(f"✗ Article Save: Failed ({response.status_code})")
            print(f"  Error: {response.text[:100]}")
            return False
            
    except Exception as e:
        print(f"✗ Article Save: Exception ({e})")
        return False

def test_core_modules():
    """測試核心模組導入"""
    print("\\n=== Core Modules Test ===")
    
    modules = {
        'core.config': False,
        'core.utils': False,
        'scraper.scraper': False
    }
    
    # 測試core.config
    try:
        from core.config import settings
        modules['core.config'] = True
        print("✓ core.config: Imported")
    except Exception as e:
        print(f"✗ core.config: Failed ({e})")
    
    # 測試core.utils
    try:
        from core.utils import get_current_taiwan_time, validate_discord_webhook
        taiwan_time = get_current_taiwan_time()
        is_valid = validate_discord_webhook('https://discord.com/api/webhooks/test')
        modules['core.utils'] = True
        print("✓ core.utils: Working")
    except Exception as e:
        print(f"✗ core.utils: Failed ({e})")
    
    # 測試scraper.scraper
    try:
        from scraper.scraper import NewsScraperManager
        scraper = NewsScraperManager()
        modules['scraper.scraper'] = True
        print("✓ scraper.scraper: Working")
    except Exception as e:
        print(f"✗ scraper.scraper: Failed ({e})")
    
    return all(modules.values())

def run_system_check():
    """執行完整系統檢查"""
    print("FinNews-Bot System Check")
    print("=" * 50)
    
    tests = [
        test_environment,
        test_core_modules, 
        test_web_request,
        test_openai_api,
        test_supabase_db,
        test_article_save
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"Test failed with exception: {e}")
            results.append(False)
    
    print("\\n" + "=" * 50)
    print("SYSTEM CHECK RESULTS:")
    print(f"✓ Passed: {sum(results)}/{len(results)} tests")
    
    if all(results):
        print("🎉 SUCCESS: All systems are working!")
        print("\\nYour FinNews-Bot is ready to:")
        print("  • Scrape financial news")
        print("  • Generate AI summaries") 
        print("  • Save articles to database")
        print("  • Send Discord notifications")
    else:
        print("⚠️  PARTIAL: Some systems need attention")
        print("Check the failed tests above")
    
    return all(results)

if __name__ == "__main__":
    run_system_check()