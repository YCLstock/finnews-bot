#!/usr/bin/env python3
"""
簡單系統測試 - 無特殊字符
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

def main():
    print("FinNews-Bot System Test")
    print("=" * 40)
    
    # 1. 測試環境變數
    print("\n1. Environment Variables:")
    env_vars = ['SUPABASE_URL', 'SUPABASE_SERVICE_KEY', 'OPENAI_API_KEY']
    env_ok = True
    for var in env_vars:
        value = os.environ.get(var)
        if value:
            print(f"   {var}: OK")
        else:
            print(f"   {var}: MISSING")
            env_ok = False
    
    # 2. 測試模組導入
    print("\n2. Module Imports:")
    modules_ok = True
    try:
        from core.config import settings
        print("   core.config: OK")
    except Exception as e:
        print(f"   core.config: FAILED - {e}")
        modules_ok = False
    
    try:
        from core.utils import get_current_taiwan_time
        taiwan_time = get_current_taiwan_time()
        print(f"   core.utils: OK (Time: {taiwan_time.strftime('%H:%M:%S')})")
    except Exception as e:
        print(f"   core.utils: FAILED - {e}")
        modules_ok = False
    
    try:
        from scraper.scraper import NewsScraperManager
        scraper = NewsScraperManager()
        print("   scraper: OK")
    except Exception as e:
        print(f"   scraper: FAILED - {e}")
        modules_ok = False
    
    # 3. 測試HTTP請求
    print("\n3. HTTP Request:")
    try:
        response = requests.get('https://httpbin.org/json', timeout=10)
        if response.status_code == 200:
            print("   Basic HTTP: OK")
            http_ok = True
        else:
            print(f"   Basic HTTP: FAILED ({response.status_code})")
            http_ok = False
    except Exception as e:
        print(f"   Basic HTTP: FAILED - {e}")
        http_ok = False
    
    # 4. 測試OpenAI API
    print("\n4. OpenAI API:")
    openai_ok = False
    api_key = os.environ.get('OPENAI_API_KEY')
    if api_key:
        try:
            headers = {'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'}
            data = {
                'model': 'gpt-3.5-turbo',
                'messages': [{'role': 'user', 'content': 'Hello'}],
                'max_tokens': 10
            }
            response = requests.post('https://api.openai.com/v1/chat/completions', 
                                   headers=headers, json=data, timeout=30)
            if response.status_code == 200:
                print("   OpenAI API: OK")
                openai_ok = True
            else:
                print(f"   OpenAI API: FAILED ({response.status_code})")
        except Exception as e:
            print(f"   OpenAI API: FAILED - {e}")
    else:
        print("   OpenAI API: NO KEY")
    
    # 5. 測試Supabase
    print("\n5. Supabase Database:")
    supabase_ok = False
    url = os.environ.get('SUPABASE_URL')
    key = os.environ.get('SUPABASE_SERVICE_KEY')
    if url and key:
        try:
            headers = {'apikey': key, 'Authorization': f'Bearer {key}'}
            response = requests.get(f'{url}/rest/v1/subscriptions', 
                                  headers=headers, params={'limit': 1}, timeout=10)
            if response.status_code == 200:
                data = response.json()
                print(f"   Supabase: OK ({len(data)} records)")
                supabase_ok = True
            else:
                print(f"   Supabase: FAILED ({response.status_code})")
        except Exception as e:
            print(f"   Supabase: FAILED - {e}")
    else:
        print("   Supabase: NO CREDENTIALS")
    
    # 6. 測試文章儲存
    print("\n6. Article Save Test:")
    save_ok = False
    if url and key:
        try:
            headers = {'apikey': key, 'Authorization': f'Bearer {key}', 'Content-Type': 'application/json'}
            test_article = {
                'original_url': f'https://test.com/article-{int(time.time())}',
                'source': 'test',
                'title': 'System Test Article',
                'summary': 'Test article for system check',
                'published_at': time.strftime('%Y-%m-%dT%H:%M:%SZ')
            }
            response = requests.post(f'{url}/rest/v1/news_articles', 
                                   headers=headers, json=test_article, timeout=10)
            if response.status_code in [200, 201]:
                print("   Article Save: OK")
                save_ok = True
            else:
                print(f"   Article Save: FAILED ({response.status_code})")
        except Exception as e:
            print(f"   Article Save: FAILED - {e}")
    
    # 總結
    print("\n" + "=" * 40)
    print("RESULTS:")
    total_tests = 6
    passed_tests = sum([env_ok, modules_ok, http_ok, openai_ok, supabase_ok, save_ok])
    
    print(f"Passed: {passed_tests}/{total_tests} tests")
    
    if passed_tests == total_tests:
        print("SUCCESS: All systems working!")
        print("\nYour FinNews-Bot is ready for:")
        print("- News scraping")
        print("- AI summarization")
        print("- Database storage")
        print("- Discord notifications")
    elif passed_tests >= 4:
        print("PARTIAL SUCCESS: Core systems working")
        print("Some features may need attention")
    else:
        print("ATTENTION NEEDED: Multiple systems failing")
        print("Check configuration and API keys")
    
    return passed_tests == total_tests

if __name__ == "__main__":
    main()