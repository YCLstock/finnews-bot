#!/usr/bin/env python3
"""
新聞收集器 - 混合策略實作
定期爬取新聞並存儲到資料庫，供後續推送使用
採用：核心財經新聞 + 用戶關鍵字相關新聞
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Set

# 添加項目根目錄到 Python 路徑
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from scraper.scraper import NewsScraperManager
from core.config import settings
from core.database import db_manager
from core.utils import get_current_taiwan_time, format_taiwan_datetime, parse_article_publish_time, generate_summary_optimized

class NewsCollector:
    """混合策略新聞收集器"""
    
    def __init__(self):
        self.scraper = NewsScraperManager()
        
    def get_all_user_keywords(self) -> Set[str]:
        """獲取所有活躍用戶的關鍵字"""
        try:
            subscriptions = db_manager.get_active_subscriptions()
            all_keywords = set()
            
            for sub in subscriptions:
                keywords = sub.get('keywords', [])
                if keywords:
                    all_keywords.update([kw.lower().strip() for kw in keywords])
            
            print(f"📋 收集到用戶關鍵字: {len(all_keywords)} 個")
            return all_keywords
            
        except Exception as e:
            print(f"❌ 獲取用戶關鍵字失敗: {e}")
            return set()
    
    def collect_core_articles(self, limit: int = 20) -> List[dict]:
        """收集核心財經新聞（前N篇，保證基礎內容）"""
        print(f"\n📰 開始收集核心財經新聞 (前 {limit} 篇)...")
        
        news_list = self.scraper.scrape_yahoo_finance_list()
        if not news_list:
            print("❌ 未能爬取到新聞列表")
            return []
        
        core_articles = []
        processed_count = 0
        
        for news_item in news_list[:limit]:  # 只處理前N篇
            # 檢查是否已處理過
            if db_manager.is_article_processed(news_item['link']):
                continue
                
            processed_count += 1
            print(f"🔄 處理核心新聞 ({processed_count}/{limit}): {news_item['title'][:50]}...")
            
            article_data = self._process_single_article(news_item, article_type="core")
            if article_data:
                core_articles.append(article_data)
                print(f"✅ 核心新聞處理成功")
            else:
                print(f"❌ 核心新聞處理失敗")
                
            # 如果已收集足夠的核心文章，提前結束
            if len(core_articles) >= limit // 2:  # 至少成功一半
                break
        
        print(f"📊 核心新聞收集完成: {len(core_articles)} 篇成功")
        return core_articles
    
    def collect_keyword_articles(self, keywords: Set[str], limit: int = 30) -> List[dict]:
        """收集關鍵字相關文章"""
        if not keywords:
            print("📋 沒有用戶關鍵字，跳過關鍵字文章收集")
            return []
            
        print(f"\n🔍 開始收集關鍵字相關文章 (關鍵字: {len(keywords)} 個，最多 {limit} 篇)...")
        print(f"🏷️ 關鍵字: {', '.join(list(keywords)[:5])}{'...' if len(keywords) > 5 else ''}")
        
        news_list = self.scraper.scrape_yahoo_finance_list()
        if not news_list:
            return []
        
        keyword_articles = []
        processed_count = 0
        
        for news_item in news_list:
            # 檢查是否已處理過
            if db_manager.is_article_processed(news_item['link']):
                continue
            
            # 檢查關鍵字匹配
            title_lower = news_item['title'].lower()
            matched_keywords = [kw for kw in keywords if kw in title_lower]
            
            if not matched_keywords:
                continue
                
            processed_count += 1
            print(f"🎯 處理關鍵字文章 ({processed_count}): {news_item['title'][:50]}...")
            print(f"   匹配關鍵字: {', '.join(matched_keywords)}")
            
            article_data = self._process_single_article(news_item, article_type="keyword", matched_keywords=matched_keywords)
            if article_data:
                keyword_articles.append(article_data)
                print(f"✅ 關鍵字文章處理成功")
            else:
                print(f"❌ 關鍵字文章處理失敗")
                
            # 如果已收集足夠的關鍵字文章，結束
            if len(keyword_articles) >= limit:
                break
        
        print(f"📊 關鍵字文章收集完成: {len(keyword_articles)} 篇成功")
        return keyword_articles
    
    def _process_single_article(self, news_item: dict, article_type: str = "core", matched_keywords: List[str] = None) -> dict:
        """處理單篇文章"""
        try:
            # 爬取文章內容
            print(f"  📥 開始爬取文章內容...")
            content = self.scraper.scrape_article_content(news_item['link'])
            if not content:
                print(f"  ❌ 文章內容爬取失敗")
                return None
            
            print(f"  ✅ 文章內容爬取成功 ({len(content)} 字)")
            
            # 生成摘要
            print(f"  🤖 開始生成AI摘要...")
            summary = generate_summary_optimized(content)
            if "[摘要生成失敗" in summary:
                print(f"  ❌ AI摘要生成失敗")
                return None
            
            print(f"  ✅ AI摘要生成成功")
            
            # 解析發布時間
            published_at = parse_article_publish_time()
            
            # 構建文章數據
            article_data = {
                'original_url': news_item['link'],
                'source': 'yahoo_finance',
                'title': news_item['title'],
                'summary': summary,
                'published_at': published_at.isoformat(),
                # 添加元數據用於後續推送邏輯
                'collection_type': article_type,
                'matched_keywords': matched_keywords or []
            }
            
            return article_data
            
        except Exception as e:
            print(f"❌ 處理文章時發生錯誤: {e}")
            return None
    
    def save_articles_to_database(self, articles: List[dict]) -> int:
        """將文章批量保存到資料庫"""
        if not articles:
            return 0
            
        print(f"\n💾 開始保存 {len(articles)} 篇文章到資料庫...")
        success_count = 0
        
        for article in articles:
            # 移除元數據（資料庫不需要）
            db_article = {k: v for k, v in article.items() 
                         if k not in ['collection_type', 'matched_keywords']}
            
            article_id = db_manager.save_new_article(db_article)
            if article_id:
                success_count += 1
        
        print(f"✅ 成功保存 {success_count} 篇文章到資料庫")
        return success_count
    
    def run_collection(self) -> bool:
        """執行混合策略新聞收集"""
        print("=" * 60)
        print("📰 FinNews-Bot 新聞收集器開始執行")
        taiwan_time = get_current_taiwan_time()
        print(f"🕐 執行時間: {format_taiwan_datetime(taiwan_time)}")
        print("=" * 60)
        
        try:
            # 驗證環境變數
            settings.validate()
            print("✅ 環境變數驗證成功")
            
            # 1. 收集核心財經新聞
            core_articles = self.collect_core_articles(limit=20)
            
            # 2. 收集用戶關鍵字相關文章
            user_keywords = self.get_all_user_keywords()
            keyword_articles = self.collect_keyword_articles(user_keywords, limit=30)
            
            # 3. 合併去重
            all_articles = []
            seen_urls = set()
            
            # 優先添加關鍵字文章（用戶更感興趣）
            for article in keyword_articles:
                if article['original_url'] not in seen_urls:
                    all_articles.append(article)
                    seen_urls.add(article['original_url'])
            
            # 添加核心文章
            for article in core_articles:
                if article['original_url'] not in seen_urls:
                    all_articles.append(article)
                    seen_urls.add(article['original_url'])
            
            print(f"\n📊 收集總結:")
            print(f"  - 核心文章: {len(core_articles)} 篇")
            print(f"  - 關鍵字文章: {len(keyword_articles)} 篇")
            print(f"  - 去重後總計: {len(all_articles)} 篇")
            
            # 4. 保存到資料庫
            if all_articles:
                saved_count = self.save_articles_to_database(all_articles)
                
                if saved_count > 0:
                    print(f"\n🎉 新聞收集任務完成！共收集 {saved_count} 篇新文章")
                    return True
                else:
                    print(f"\n⚠️ 新聞收集完成，但未能保存任何文章")
                    return False
            else:
                print(f"\n📭 本次收集未獲得新文章（可能都已存在於資料庫）")
                return False
                
        except Exception as e:
            print(f"\n❌ 新聞收集任務失敗: {e}")
            import traceback
            traceback.print_exc()
            return False
            
        finally:
            print("\n" + "=" * 60)
            print("🏁 FinNews-Bot 新聞收集器結束")
            taiwan_time = get_current_taiwan_time()
            print(f"⏰ 結束時間: {format_taiwan_datetime(taiwan_time)}")
            print("=" * 60)

def main():
    """主執行函數"""
    collector = NewsCollector()
    success = collector.run_collection()
    return 0 if success else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)