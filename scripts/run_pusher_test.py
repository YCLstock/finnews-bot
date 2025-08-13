#!/usr/bin/env python3
"""
智能推送器測試腳本 (Pusher Test Script)
- 用於安全地測試推送引擎的評分和篩選邏輯，不會執行任何真實的推送。
- 移除了所有時間限制，以便處理歷史文章。
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any

# 添加項目根目錄到 Python 路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.config import settings
from core.database import db_manager
from core.utils import get_current_taiwan_time, format_taiwan_datetime, create_push_summary_message
from core.delivery_manager import get_delivery_manager
from core.topics_mapper import topics_mapper

class SmartPusherTest:
    """智能推送器測試版本 - 基於已存儲文章，僅記錄不推送"""

    def __init__(self):
        self.tag_weight = 0.5
        self.keyword_weight = 0.5
        self.match_threshold = 0.2 # 降低門檻以提高匹配率

    def _get_user_interest_topics(self, keywords: List[str]) -> List[str]:
        if not keywords:
            return []
        
        # 使用統一標籤管理系統
        try:
            from scripts.dynamic_tags import convert_keywords_to_tags
            interest_topics = convert_keywords_to_tags(keywords)
        except Exception as e:
            print(f"[WARNING] Failed to use unified tag system, fallback to topics_mapper: {e}")
            # 降級到原有的topics_mapper
            mapped_results = topics_mapper.map_keywords_to_topics(keywords)
            interest_topics = list(set([result[0].upper() for result in mapped_results]))
        
        print(f"[INFO] 用戶意圖分析: {keywords} -> {interest_topics}")
        return interest_topics

    def _calculate_hybrid_score(self, article: Dict[str, Any], user_keywords: List[str], interest_topics: List[str]) -> float:
        tag_score = 0.0
        article_tags = [tag.upper() for tag in article.get('tags', []) if tag]
        if interest_topics and article_tags:
            matching_tags = set(interest_topics).intersection(set(article_tags))
            tag_score = len(matching_tags) / len(interest_topics)

        keyword_score = 0.0
        if user_keywords:
            title_lower = article.get('title', '').lower()
            summary_lower = article.get('summary', '').lower()
            content_to_check = f"{title_lower} {summary_lower}"
            if any(kw.lower().strip() in content_to_check for kw in user_keywords):
                keyword_score = 1.0

        final_score = (tag_score * self.tag_weight) + (keyword_score * self.keyword_weight)
        return round(final_score, 4)

    def get_eligible_articles_for_user(self, subscription: Dict[str, Any], hours_limit: int = 9999) -> List[Dict[str, Any]]: # 擴大時間範圍
        user_id = subscription['user_id']
        keywords = subscription.get('keywords', [])
        frequency_type = subscription.get('push_frequency_type', 'daily')
        max_articles = db_manager.get_max_articles_for_frequency(frequency_type)

        print(f"[INFO] 為用戶 {user_id[:8]}... 智能選擇文章 (最多 {max_articles} 篇)")

        try:
            query_builder = db_manager.supabase.table("news_articles").select("*", "tags")
            # REMOVED: 時間過濾被移除
            query_builder = query_builder.order("published_at", desc=True)
            query_builder = query_builder.limit(100) # 獲取足夠多的文章來測試

            result = query_builder.execute()
            all_articles = result.data if result.data else []

            print(f"[DB] 查詢到 {len(all_articles)} 篇歷史文章用於測試")

            if not all_articles:
                print(f"[INFO] 資料庫中沒有文章可供測試")
                return []

            # 在測試模式下，我們不過濾已推送的文章，以便重複測試
            unread_articles = all_articles
            print(f"[FILTER] 在測試模式下，使用所有 {len(unread_articles)} 篇文章")

            selected_articles = self.select_articles_by_preference(unread_articles, keywords, max_articles)

            print(f"[SUCCESS] 最終選擇文章: {len(selected_articles)} 篇")
            return selected_articles

        except Exception as e:
            print(f"[ERROR] 獲取用戶文章時發生錯誤: {e}")
            import traceback
            traceback.print_exc()
            return []

    def select_articles_by_preference(self, articles: List[Dict[str, Any]], keywords: List[str], max_count: int) -> List[Dict[str, Any]]:
        if not articles:
            return []

        if not keywords:
            print(f"[INFO] 用戶無關鍵字，選擇最新 {max_count} 篇通用財經新聞")
            return articles[:max_count]

        print(f"[INFO] 執行混合評分引擎，分析關鍵字: {', '.join(keywords)}")

        interest_topics = self._get_user_interest_topics(keywords)

        scored_articles = []
        for article in articles:
            score = self._calculate_hybrid_score(article, keywords, interest_topics)
            
            if score >= self.match_threshold:
                article_with_score = article.copy()
                article_with_score['relevance_score'] = score
                scored_articles.append(article_with_score)

        scored_articles.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        print(f"[STATS] 評分完成: {len(scored_articles)} 篇文章分數高於門檻 {self.match_threshold}")
        for art in scored_articles[:10]: # 顯示前10名的分數
             print(f"   - [{art['relevance_score']:.2f}] {art['title'][:60]}...")

        return scored_articles[:max_count]

    def process_user_subscription(self, subscription: Dict[str, Any]) -> bool:
        user_id = subscription['user_id']
        frequency_type = subscription.get('push_frequency_type', 'daily')

        print(f"\n--- [INFO] 測試處理用戶 {user_id[:8]}... 的推送 ({frequency_type}) ---")

        # REMOVED: 時間窗口檢查被移除

        articles = self.get_eligible_articles_for_user(subscription)

        if not articles:
            print(f"[SKIP] 用戶 {user_id[:8]}... 在測試中沒有篩選出任何文章")
            return False

        # DRY RUN: 不執行真實推送，只記錄日誌
        print(f"\n--- [DRY RUN] ---")
        print(f"模擬推送 {len(articles)} 篇文章給用戶 {user_id[:8]}...")
        for article in articles:
            print(f"  - [SCORE: {article.get('relevance_score', 0):.2f}] {article['title']}")
        print(f"--- [END DRY RUN] ---")
        
        # 模擬成功，但不記錄歷史或更新時間戳
        return True

    def run_test(self) -> bool:
        """執行測試"""
        print("=" * 60)
        print("FinNews-Bot 推送引擎測試腳本")
        print("=" * 60)

        try:
            settings.validate()
            print("[OK] 環境變數驗證成功")

            # FOR TEST: 獲取所有活躍的訂閱
            result = db_manager.supabase.table("subscriptions").select("*").eq("is_active", True).execute()
            all_subscriptions = result.data if result.data else []

            if not all_subscriptions:
                print("\n[INFO] 資料庫中沒有活躍的訂閱可供測試")
                return True

            print(f"\n[STATS] 找到 {len(all_subscriptions)} 個活躍訂閱進行測試")

            for subscription in all_subscriptions:
                self.process_user_subscription(subscription)

            print(f"\n[SUCCESS] 所有用戶測試完成！")
            return True

        except Exception as e:
            print(f"\n[ERROR] 測試腳本執行失敗: {e}")
            import traceback
            traceback.print_exc()
            return False

        finally:
            print("\n" + "=" * 60)
            print("測試腳本結束")
            print("=" * 60)

def main():
    pusher_test = SmartPusherTest()
    success = pusher_test.run_test()
    return 0 if success else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
