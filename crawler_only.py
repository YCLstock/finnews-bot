#!/usr/bin/env python3
"""
獨立爬蟲腳本 - 只負責爬取新聞和生成摘要
執行頻率建議：每2-4小時
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

def log_message(message):
    """輸出帶時間戳的訊息"""
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] {message}")

def scrape_yahoo_finance():
    """爬取Yahoo Finance新聞"""
    log_message("Starting Yahoo Finance news scraping...")
    
    url = 'https://finance.yahoo.com/topic/stock-market-news'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200:
            log_message(f"HTTP Error: {response.status_code}")
            return []
            
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 尋找新聞連結
        news_items = []
        all_links = soup.find_all('a', href=True)
        
        for link in all_links:
            href = link.get('href')
            text = link.get_text(strip=True)
            
            # 過濾條件：有意義的文字且是新聞連結
            if (href and text and len(text) > 20 and 
                ('/news/' in href or 'finance.yahoo.com' in href) and
                not any(exclude in href.lower() for exclude in ['video', 'premium', 'quote'])):
                
                # 確保完整URL
                if href.startswith('/'):
                    href = 'https://finance.yahoo.com' + href
                
                news_items.append({
                    'title': text,
                    'link': href
                })
        
        # 去重和限制數量
        seen_urls = set()
        unique_news = []
        for item in news_items:
            if item['link'] not in seen_urls and len(unique_news) < 20:
                seen_urls.add(item['link'])
                unique_news.append(item)
        
        log_message(f"Found {len(unique_news)} unique news items")
        return unique_news
        
    except Exception as e:
        log_message(f"Scraping failed: {e}")
        return []

def generate_summary(title, content=""):
    """使用OpenAI生成摘要"""
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        log_message("Missing OpenAI API key")
        return f"AI摘要功能暫時無法使用。原標題：{title}"
    
    # 如果沒有內容，就用標題生成摘要
    input_text = content if content else title
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    data = {
        'model': 'gpt-3.5-turbo',
        'messages': [
            {
                'role': 'system',
                'content': '''你是專業的財經新聞編輯。請將以下新聞生成簡潔的繁體中文摘要：
1. 保持客觀中立
2. 重點突出關鍵資訊
3. 長度控制在80-120字
4. 適合投資人快速閱讀'''
            },
            {'role': 'user', 'content': f'請為這則財經新聞生成摘要：{input_text}'}
        ],
        'max_tokens': 200,
        'temperature': 0.3
    }
    
    try:
        response = requests.post('https://api.openai.com/v1/chat/completions', 
                               headers=headers, json=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            summary = result['choices'][0]['message']['content'].strip()
            return summary
        else:
            log_message(f"OpenAI API Error: {response.status_code}")
            return f"摘要生成失敗。原標題：{title}"
            
    except Exception as e:
        log_message(f"Summary generation failed: {e}")
        return f"摘要生成異常。原標題：{title}"

def is_article_processed(url):
    """檢查文章是否已處理過"""
    supabase_url = os.environ.get('SUPABASE_URL')
    supabase_key = os.environ.get('SUPABASE_SERVICE_KEY')
    
    if not supabase_url or not supabase_key:
        return False
    
    headers = {
        'apikey': supabase_key,
        'Authorization': f'Bearer {supabase_key}'
    }
    
    try:
        response = requests.get(
            f"{supabase_url}/rest/v1/news_articles",
            headers=headers,
            params={'original_url': f'eq.{url}', 'select': 'id'},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            return len(data) > 0
        else:
            return False
            
    except Exception as e:
        log_message(f"Error checking article: {e}")
        return False

def generate_tags_with_ai(title, summary):
    """使用AI為文章生成標籤"""
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        log_message("Missing OpenAI API key, using fallback tags")
        return generate_fallback_tags(title, summary)
    
    # 核心標籤庫
    core_tags = ["APPLE", "TSMC", "TESLA", "AI_TECH", "CRYPTO"]
    
    prompt = f"""
請為以下財經新聞分配標籤，從核心標籤庫中選擇最多3個相關標籤：

核心標籤庫: {core_tags}
- APPLE: 蘋果公司相關 (iPhone, Mac, 庫克, AAPL)
- TSMC: 台積電相關 (半導體, 晶圓, 晶片代工)  
- TESLA: 特斯拉相關 (電動車, 馬斯克, 自駕車)
- AI_TECH: AI科技相關 (人工智慧, ChatGPT, 機器學習)
- CRYPTO: 加密貨幣相關 (比特幣, 區塊鏈, 虛擬貨幣)

文章標題: {title}
文章摘要: {summary}

請返回JSON格式: {{"tags": ["TAG1", "TAG2"], "confidence": 0.95}}
如果完全不相關，返回: {{"tags": [], "confidence": 0}}
"""
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    data = {
        'model': 'gpt-3.5-turbo',
        'messages': [{'role': 'user', 'content': prompt}],
        'max_tokens': 150,
        'temperature': 0.1
    }
    
    try:
        response = requests.post('https://api.openai.com/v1/chat/completions', 
                               headers=headers, json=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            content = result['choices'][0]['message']['content']
            
            try:
                parsed = json.loads(content)
                tags = parsed.get('tags', [])
                confidence = parsed.get('confidence', 0)
                
                if confidence > 0.7:
                    log_message(f"  AI tags: {tags} (confidence: {confidence})")
                    return tags
                else:
                    log_message(f"  Low confidence ({confidence}), using fallback")
                    return generate_fallback_tags(title, summary)
                    
            except json.JSONDecodeError:
                log_message("  AI response parsing failed, using fallback")
                return generate_fallback_tags(title, summary)
        else:
            log_message(f"  AI API error: {response.status_code}")
            return generate_fallback_tags(title, summary)
            
    except Exception as e:
        log_message(f"  AI tagging error: {e}")
        return generate_fallback_tags(title, summary)

def generate_fallback_tags(title, summary):
    """備用規則式標籤生成"""
    text = f"{title} {summary}".lower()
    tags = []
    
    # 規則式匹配
    tag_keywords = {
        "APPLE": ["apple", "iphone", "mac", "aapl", "蘋果", "庫克"],
        "TSMC": ["tsmc", "taiwan semiconductor", "台積電", "晶圓", "半導體"],
        "TESLA": ["tesla", "tsla", "musk", "特斯拉", "馬斯克", "電動車"],
        "AI_TECH": ["ai", "artificial intelligence", "chatgpt", "openai", "人工智慧", "機器學習"],
        "CRYPTO": ["bitcoin", "cryptocurrency", "blockchain", "比特幣", "加密貨幣", "區塊鏈"]
    }
    
    for tag, keywords in tag_keywords.items():
        if any(keyword in text for keyword in keywords):
            tags.append(tag)
    
    return tags[:3]  # 最多3個標籤

def save_article(article_data):
    """儲存文章到資料庫（包含標籤）"""
    supabase_url = os.environ.get('SUPABASE_URL')
    supabase_key = os.environ.get('SUPABASE_SERVICE_KEY')
    
    if not supabase_url or not supabase_key:
        log_message("Missing Supabase credentials")
        return False
    
    headers = {
        'apikey': supabase_key,
        'Authorization': f'Bearer {supabase_key}',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.post(
            f"{supabase_url}/rest/v1/news_articles",
            headers=headers,
            json=article_data,
            timeout=10
        )
        
        if response.status_code in [200, 201]:
            return True
        else:
            log_message(f"Save failed: {response.status_code} - {response.text[:100]}")
            return False
            
    except Exception as e:
        log_message(f"Save error: {e}")
        return False

def main():
    """主要執行函數"""
    log_message("=== FinNews-Bot Crawler Started ===")
    
    # 1. 爬取新聞
    news_items = scrape_yahoo_finance()
    if not news_items:
        log_message("No news items found, exiting")
        return
    
    # 2. 處理每則新聞
    processed_count = 0
    skipped_count = 0
    
    for i, news in enumerate(news_items):
        log_message(f"Processing {i+1}/{len(news_items)}: {news['title'][:50]}...")
        
        # 檢查是否已處理
        if is_article_processed(news['link']):
            log_message("  Already processed, skipping")
            skipped_count += 1
            continue
        
        # 生成摘要
        summary = generate_summary(news['title'])
        
        # 生成AI標籤
        tags = generate_tags_with_ai(news['title'], summary)
        
        # 準備文章數據
        article_data = {
            'original_url': news['link'],
            'source': 'yahoo_finance',
            'title': news['title'],
            'summary': summary,
            'tags': tags,  # 新增AI標籤
            'published_at': time.strftime('%Y-%m-%dT%H:%M:%SZ')
        }
        
        # 儲存文章
        if save_article(article_data):
            log_message("  Saved successfully")
            processed_count += 1
        else:
            log_message("  Save failed")
        
        # 避免API限制
        time.sleep(1)
    
    log_message(f"=== Crawler Completed ===")
    log_message(f"Processed: {processed_count} new articles")
    log_message(f"Skipped: {skipped_count} existing articles")
    log_message(f"Total found: {len(news_items)} articles")

if __name__ == "__main__":
    main()