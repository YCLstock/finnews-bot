#!/usr/bin/env python3
"""
完整系統測試 - 避免Unicode問題
"""
import sys
import os
import time
import requests
import json
from pathlib import Path
from dotenv import load_dotenv
from bs4 import BeautifulSoup

# 添加項目根目錄到 Python 路徑
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 載入環境變數
load_dotenv()

def test_yahoo_finance_scraping():
    """測試Yahoo Finance爬蟲"""
    print("=== Testing Yahoo Finance Scraping ===")
    
    url = 'https://finance.yahoo.com/topic/stock-market-news'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        print(f"HTTP Status: {response.status_code}")
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            items = soup.select('li.stream-item')
            print(f"Found {len(items)} news items")
            
            news_list = []
            for item in items[:5]:  # 取前5則
                title_elem = item.select_one('h2 a') or item.select_one('h3 a')
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    link = title_elem.get('href')
                    if link and not link.startswith('http'):
                        link = 'https://finance.yahoo.com' + link
                    
                    news_list.append({
                        'title': title,
                        'link': link
                    })
            
            print(f"Successfully parsed {len(news_list)} news items:")
            for i, news in enumerate(news_list):
                print(f"  {i+1}. {news['title'][:60]}...")
                
            return news_list
            
    except Exception as e:
        print(f"Yahoo Finance scraping failed: {e}")
        return []

def test_openai_api():
    """測試OpenAI API"""
    print("\n=== Testing OpenAI API ===")
    
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        print("Missing OpenAI API key")
        return False
        
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    test_content = "Apple Inc. reported strong quarterly earnings, beating analyst expectations with revenue of $95 billion."
    
    data = {
        'model': 'gpt-3.5-turbo',
        'messages': [
            {'role': 'system', 'content': 'You are a financial news summarizer. Summarize the following in Traditional Chinese, keeping it under 100 characters.'},
            {'role': 'user', 'content': test_content}
        ],
        'max_tokens': 150,
        'temperature': 0.3
    }
    
    try:
        response = requests.post('https://api.openai.com/v1/chat/completions', 
                               headers=headers, 
                               json=data, 
                               timeout=30)
        
        print(f"OpenAI API Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            summary = result['choices'][0]['message']['content']
            print(f"Generated summary: {summary}")
            return True
        else:
            print(f"OpenAI API Error: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"OpenAI API test failed: {e}")
        return False

def test_supabase_connection():
    """測試Supabase資料庫連接"""
    print("\n=== Testing Supabase Database ===")
    
    url = os.environ.get('SUPABASE_URL')
    key = os.environ.get('SUPABASE_SERVICE_KEY')
    
    if not url or not key:
        print("Missing Supabase credentials")
        return False
        
    headers = {
        'apikey': key,
        'Authorization': f'Bearer {key}',
        'Content-Type': 'application/json'
    }
    
    try:
        # 測試訂閱表
        response = requests.get(f'{url}/rest/v1/subscriptions', 
                              headers=headers, 
                              params={'limit': 1})
        
        print(f"Subscriptions table status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Found {len(data)} subscription records")
            return True
        else:
            print(f"Database Error: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"Supabase test failed: {e}")
        return False

def test_article_saving():
    """測試文章儲存功能"""
    print("\n=== Testing Article Saving ===")
    
    url = os.environ.get('SUPABASE_URL')
    key = os.environ.get('SUPABASE_SERVICE_KEY')
    
    if not url or not key:
        print("Missing Supabase credentials")
        return False
        
    headers = {
        'apikey': key,
        'Authorization': f'Bearer {key}',
        'Content-Type': 'application/json'
    }
    
    # 測試文章數據
    test_article = {
        'original_url': 'https://example.com/test-article-' + str(int(time.time())),
        'source': 'yahoo_finance',
        'title': 'Test Article Title',
        'summary': 'This is a test article summary.',
        'published_at': '2025-07-20T22:30:00Z'
    }
    
    try:
        # 嘗試儲存測試文章
        response = requests.post(f'{url}/rest/v1/news_articles', 
                               headers=headers, 
                               json=test_article)
        
        print(f"Article saving status: {response.status_code}")
        
        if response.status_code in [200, 201]:
            data = response.json()
            print("Article saved successfully")
            if data:
                print(f"Article ID: {data[0].get('id', 'Unknown')}")
            return True
        else:
            print(f"Article saving Error: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"Article saving test failed: {e}")
        return False

def run_integration_test():
    """執行整合測試"""
    print("\n=== Integration Test ===")
    
    # 1. 爬取新聞
    news_list = test_yahoo_finance_scraping()
    if not news_list:
        print("Integration test failed: No news scraped")
        return False
    
    # 2. 測試OpenAI摘要
    openai_ok = test_openai_api()
    if not openai_ok:
        print("Integration test failed: OpenAI API not working")
        return False
    
    # 3. 測試資料庫
    db_ok = test_supabase_connection()
    if not db_ok:
        print("Integration test failed: Database not accessible")
        return False
    
    print("Integration test completed successfully!")
    return True

if __name__ == "__main__":
    print("FinNews-Bot Complete System Test")
    print("=" * 50)
    
    # 執行各項測試
    test_yahoo_finance_scraping()
    test_openai_api()
    test_supabase_connection()
    test_article_saving()
    run_integration_test()
    
    print("\n" + "=" * 50)
    print("All tests completed!")