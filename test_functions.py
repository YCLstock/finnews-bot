#!/usr/bin/env python3
"""
完整功能測試腳本
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

def test_web_scraping():
    """測試網頁爬取功能"""
    print("=== Testing Web Scraping ===")
    
    try:
        from scraper.scraper import NewsScraperManager
        scraper = NewsScraperManager()
        
        print("Testing Yahoo Finance news list scraping...")
        news_list = scraper.scrape_yahoo_finance_list()
        
        if news_list:
            print(f"Successfully scraped {len(news_list)} news items")
            for i, news in enumerate(news_list[:3]):  # 顯示前3則
                print(f"  {i+1}. {news.get('title', 'No title')[:50]}...")
        else:
            print("No news items found or scraping failed")
            
    except Exception as e:
        print(f"Web scraping failed: {e}")

def test_openai_summary():
    """測試OpenAI摘要生成"""
    print("\n=== Testing OpenAI Summary ===")
    
    try:
        from core.utils import generate_summary_optimized
        
        test_content = """
        台積電今日宣布，第三季度營收達到新台幣2000億元，較去年同期成長15%。
        公司表示，這主要受益於5G和人工智慧晶片需求強勁。
        董事長表示對未來前景樂觀，預計下季度將持續成長。
        """
        
        print("Testing summary generation with sample content...")
        summary = generate_summary_optimized(test_content)
        print(f"Generated summary: {summary}")
        
    except Exception as e:
        print(f"OpenAI summary generation failed: {e}")

def test_database_connection():
    """測試資料庫連接"""
    print("\n=== Testing Database Connection ===")
    
    try:
        # 避免Unicode問題，直接測試API
        import requests
        import os
        
        url = os.environ.get('SUPABASE_URL')
        key = os.environ.get('SUPABASE_SERVICE_KEY')
        
        if not url or not key:
            print("Missing Supabase credentials")
            return
            
        headers = {
            'apikey': key,
            'Authorization': f'Bearer {key}',
            'Content-Type': 'application/json'
        }
        
        # 測試連接到subscriptions表
        response = requests.get(
            f"{url}/rest/v1/subscriptions",
            headers=headers,
            params={'select': 'id', 'limit': 1}
        )
        
        if response.status_code == 200:
            print("Database connection successful")
            data = response.json()
            print(f"Found {len(data)} subscription records")
        else:
            print(f"Database connection failed: {response.status_code}")
            
    except Exception as e:
        print(f"Database test failed: {e}")

def test_discord_webhook():
    """測試Discord推送功能"""
    print("\n=== Testing Discord Webhook ===")
    
    try:
        from core.utils import validate_discord_webhook
        
        # 測試webhook驗證
        test_webhook = "https://discord.com/api/webhooks/123456789/abcdefg"
        is_valid = validate_discord_webhook(test_webhook)
        print(f"Webhook format validation: {is_valid}")
        
        # 如果您有真實的webhook URL，可以取消註釋下面的代碼進行實際測試
        # from core.utils import send_to_discord
        # test_articles = [{
        #     'title': '測試新聞標題',
        #     'summary': '這是一則測試新聞的摘要內容。',
        #     'original_url': 'https://example.com/test-news'
        # }]
        # result = send_to_discord("YOUR_WEBHOOK_URL", test_articles)
        # print(f"Discord send test result: {result}")
        
    except Exception as e:
        print(f"Discord webhook test failed: {e}")

def test_article_processing():
    """測試文章處理流程"""
    print("\n=== Testing Article Processing ===")
    
    try:
        from scraper.scraper import NewsScraperManager
        
        scraper = NewsScraperManager()
        
        # 測試簡單的內容爬取
        test_url = "https://finance.yahoo.com/news/example"  # 這只是格式測試
        print("Testing article content scraping structure...")
        
        # 這裡我們只測試函數是否存在，不實際爬取
        if hasattr(scraper, 'scrape_article_content'):
            print("Article content scraping method exists")
        else:
            print("Article content scraping method not found")
            
    except Exception as e:
        print(f"Article processing test failed: {e}")

if __name__ == "__main__":
    print("FinNews-Bot Complete Function Test")
    print("=" * 50)
    
    test_web_scraping()
    test_openai_summary()
    test_database_connection()
    test_discord_webhook()
    test_article_processing()
    
    print("\n" + "=" * 50)
    print("Complete test finished!")