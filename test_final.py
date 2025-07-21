#!/usr/bin/env python3
"""
最終完整系統測試
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

def scrape_yahoo_finance():
    """改進的Yahoo Finance爬蟲"""
    print("=== Yahoo Finance News Scraping ===")
    
    url = 'https://finance.yahoo.com/topic/stock-market-news'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        print(f"HTTP Status: {response.status_code}")
        
        if response.status_code != 200:
            return []
            
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 嘗試不同的選擇器策略
        news_items = []
        
        # 策略1: 直接找h3 a標籤
        links = soup.select('h3 a')
        if not links:
            # 策略2: 找所有包含href的a標籤，過濾財經相關
            links = soup.select('a[href*="/news/"]')
        
        print(f"Found {len(links)} potential news links")
        
        for link in links[:10]:  # 限制前10個
            href = link.get('href')
            title = link.get_text(strip=True)
            
            if href and title and len(title) > 10:  # 過濾太短的標題
                # 確保完整URL
                if href.startswith('/'):
                    href = 'https://finance.yahoo.com' + href
                elif not href.startswith('http'):
                    continue
                    
                # 過濾財經相關新聞
                if any(keyword in href.lower() for keyword in ['finance', 'news', 'stock', 'market']):
                    news_items.append({
                        'title': title,
                        'link': href
                    })
        
        print(f"Successfully extracted {len(news_items)} news items:")
        for i, item in enumerate(news_items):
            print(f"  {i+1}. {item['title'][:60]}...")
            
        return news_items
        
    except Exception as e:
        print(f"Scraping failed: {e}")
        return []

def generate_summary(content):
    """使用OpenAI生成摘要"""
    print("=== Generating Summary with OpenAI ===")
    
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        print("Missing OpenAI API key")
        return None
        
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    data = {
        'model': 'gpt-3.5-turbo',
        'messages': [
            {
                'role': 'system', 
                'content': 'You are a financial news summarizer. Summarize news in Traditional Chinese, keep it concise and informative, under 150 characters.'
            },
            {'role': 'user', 'content': f'Please summarize this financial news: {content}'}
        ],
        'max_tokens': 200,
        'temperature': 0.3
    }
    
    try:
        response = requests.post('https://api.openai.com/v1/chat/completions', 
                               headers=headers, 
                               json=data, 
                               timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            summary = result['choices'][0]['message']['content'].strip()
            print(f"Generated summary: {summary}")
            return summary
        else:
            print(f"OpenAI API Error: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"Summary generation failed: {e}")
        return None

def save_article_to_db(article_data):
    """儲存文章到Supabase"""
    print("=== Saving Article to Database ===")
    
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
        response = requests.post(f'{url}/rest/v1/news_articles', 
                               headers=headers, 
                               json=article_data)
        
        print(f"Save status: {response.status_code}")
        
        if response.status_code in [200, 201]:
            print("Article saved successfully")
            return True
        else:
            print(f"Save failed: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"Database save failed: {e}")
        return False

def test_discord_webhook():
    """測試Discord webhook格式"""
    print("=== Testing Discord Webhook Format ===")
    
    # 測試webhook URL格式驗證
    test_webhooks = [
        "https://discord.com/api/webhooks/123456789/abcdefghijklmnop",
        "https://discordapp.com/api/webhooks/123456789/abcdefghijklmnop",
        "https://invalid-webhook.com/test",
        ""
    ]
    
    for webhook in test_webhooks:
        is_valid = webhook.startswith("https://discord") and "/webhooks/" in webhook
        print(f"Webhook: {webhook[:50]}... -> Valid: {is_valid}")

def run_complete_workflow():
    """執行完整的新聞處理工作流程"""
    print("\\n=== Complete News Processing Workflow ===")
    
    # 1. 爬取新聞
    news_items = scrape_yahoo_finance()
    if not news_items:
        print("Workflow failed: No news items scraped")
        return False
    
    # 2. 處理第一則新聞
    first_news = news_items[0]
    print(f"\\nProcessing: {first_news['title']}")
    
    # 3. 生成摘要（使用標題作為內容進行測試）
    summary = generate_summary(first_news['title'])
    if not summary:
        print("Workflow failed: Could not generate summary")
        return False
    
    # 4. 準備文章數據
    article_data = {
        'original_url': first_news['link'],
        'source': 'yahoo_finance',
        'title': first_news['title'],
        'summary': summary,
        'published_at': time.strftime('%Y-%m-%dT%H:%M:%SZ')
    }
    
    # 5. 儲存到資料庫
    saved = save_article_to_db(article_data)
    if not saved:
        print("Workflow failed: Could not save article")
        return False
    
    print("\\nComplete workflow executed successfully!")
    print(f"Processed article: {first_news['title'][:50]}...")
    print(f"Generated summary: {summary[:50]}...")
    
    return True

if __name__ == "__main__":
    print("FinNews-Bot Final System Test")
    print("=" * 60)
    
    # 執行完整工作流程
    success = run_complete_workflow()
    
    # 額外測試
    test_discord_webhook()
    
    print("\\n" + "=" * 60)
    if success:
        print("SUCCESS: All core functions are working!")
    else:
        print("FAILED: Some functions need attention")