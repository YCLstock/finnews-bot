"""
AWS Lambda函數 - 新聞爬蟲
負責：定時爬取Yahoo Finance新聞並存入Supabase
"""
import json
import os
import sys
from pathlib import Path

# 設置編碼（Windows本地測試需要）
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())

# 添加專案根目錄到路徑
sys.path.append(str(Path(__file__).parent.parent.parent))

from core.database import db_manager
from scraper.scraper import NewsScraperManager
from core.utils import get_current_taiwan_time

def lambda_handler(event, context):
    """Lambda主入口函數"""
    
    print("🚀 AWS Lambda 新聞爬蟲開始執行")
    taiwan_time = get_current_taiwan_time()
    print(f"🕐 執行時間: {taiwan_time.strftime('%Y-%m-%d %H:%M:%S')} (台灣時間)")
    
    try:
        # 檢查環境變數
        required_vars = ['SUPABASE_URL', 'SUPABASE_SERVICE_KEY', 'OPENAI_API_KEY']
        for var in required_vars:
            if not os.environ.get(var):
                raise ValueError(f"缺少環境變數: {var}")
        
        # 初始化爬蟲
        scraper = NewsScraperManager()
        
        # 爬取新聞（AWS環境限制處理數量）
        limit = int(os.environ.get('CRAWLER_LIMIT', '10'))
        print(f"📰 開始爬取新聞，限制 {limit} 篇")
        
        # 獲取新聞列表
        news_list = scraper.scrape_yahoo_finance_list()
        if not news_list:
            return {
                'statusCode': 500,
                'body': json.dumps({'error': '無法獲取新聞列表'})
            }
        
        # 處理文章
        articles = []
        success_count = 0
        
        for i, news_item in enumerate(news_list[:limit]):
            # 檢查是否已處理
            if db_manager.is_article_processed(news_item['link']):
                continue
            
            print(f"🔄 處理文章 {i+1}/{limit}: {news_item['title'][:50]}...")
            
            # 爬取文章內容
            content = scraper.scrape_article_content(news_item['link'])
            if not content:
                continue
            
            # 生成摘要
            from core.utils import generate_summary_optimized
            summary = generate_summary_optimized(content)
            
            # 構建文章數據
            article_data = {
                'original_url': news_item['link'],
                'source': 'yahoo_finance',
                'title': news_item['title'],
                'summary': summary,
                'published_at': taiwan_time.isoformat()
            }
            
            # 保存到資料庫
            article_id = db_manager.save_new_article(article_data)
            if article_id:
                articles.append(article_data)
                success_count += 1
                print(f"✅ 文章處理成功")
            else:
                print(f"❌ 文章保存失敗")
        
        print(f"🎉 爬蟲任務完成！成功處理 {success_count} 篇文章")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': f'成功處理 {success_count} 篇文章',
                'articles_count': success_count,
                'execution_time': taiwan_time.isoformat()
            })
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
            })
        }