"""
AWS Lambda函數 - 簡化版新聞爬蟲
移除Supabase依賴，直接輸出結果用於測試
"""
import json
import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import pytz

def get_current_taiwan_time():
    """獲取台灣時間"""
    taiwan_tz = pytz.timezone('Asia/Taipei') 
    return datetime.now(taiwan_tz)

def scrape_yahoo_finance_news():
    """簡化版新聞爬蟲"""
    try:
        url = "https://finance.yahoo.com/topic/stock-market-news"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code != 200:
            return []
            
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # 尋找新聞文章
        articles = []
        news_items = soup.find_all('h3', class_='clamp')[:5]  # 限制5篇
        
        for item in news_items:
            link_elem = item.find('a')
            if link_elem:
                title = link_elem.get_text(strip=True)
                link = link_elem.get('href', '')
                if link and not link.startswith('http'):
                    link = 'https://finance.yahoo.com' + link
                
                articles.append({
                    'title': title,
                    'link': link
                })
        
        return articles
        
    except Exception as e:
        print(f"爬蟲錯誤: {str(e)}")
        return []

def generate_simple_summary(title):
    """簡化版摘要生成"""
    try:
        # 如果沒有OpenAI API，返回標題
        api_key = os.environ.get('OPENAI_API_KEY')
        if not api_key:
            return f"摘要：{title}"
            
        # 這裡可以加入OpenAI API調用
        return f"AI摘要：{title}"
        
    except Exception as e:
        return f"摘要生成失敗：{title}"

def lambda_handler(event, context):
    """Lambda主入口函數"""
    
    print("🚀 AWS Lambda 簡化版新聞爬蟲開始執行")
    taiwan_time = get_current_taiwan_time()
    print(f"🕐 執行時間: {taiwan_time.strftime('%Y-%m-%d %H:%M:%S')} (台灣時間)")
    
    try:
        # 爬取新聞
        print("📰 開始爬取Yahoo Finance新聞...")
        articles = scrape_yahoo_finance_news()
        
        if not articles:
            return {
                'statusCode': 500,
                'body': json.dumps({'error': '無法獲取新聞列表'}, ensure_ascii=False)
            }
        
        # 處理文章
        processed_articles = []
        for i, article in enumerate(articles):
            print(f"🔄 處理文章 {i+1}: {article['title'][:50]}...")
            
            summary = generate_simple_summary(article['title'])
            
            processed_article = {
                'title': article['title'],
                'link': article['link'],
                'summary': summary,
                'processed_at': taiwan_time.isoformat()
            }
            
            processed_articles.append(processed_article)
        
        print(f"🎉 爬蟲任務完成！成功處理 {len(processed_articles)} 篇文章")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': f'成功處理 {len(processed_articles)} 篇文章',
                'articles': processed_articles,
                'execution_time': taiwan_time.isoformat()
            }, ensure_ascii=False)
        }
        
    except Exception as e:
        print(f"❌ 爬蟲執行失敗: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'execution_time': taiwan_time.isoformat()
            }, ensure_ascii=False)
        }