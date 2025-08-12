#!/usr/bin/env python3
"""
智能推送器 - 基於已存儲文章的推送系統
不進行爬取，只從資料庫中選擇合適的文章進行推送
"""

import sys
import os
import logging
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
from core.logger_config import setup_logging

# 設定 logger
logger = logging.getLogger(__name__)

class SmartPusher:
    """智能推送器 - 基於已存儲文章"""

    def __init__(self):
        # 定義混合評分引擎的權重
        self.tag_weight = 0.7
        self.keyword_weight = 0.3
        self.match_threshold = 0.5 # 推送門檻分數

    def _get_user_interest_topics(self, keywords: List[str]) -> List[str]:
        """將用戶的原始關鍵字列表轉化為標準化的興趣主題列表"""
        if not keywords:
            return []
        
        mapped_results = topics_mapper.map_keywords_to_topics(keywords)
        
        interest_topics = list(set([result[0].upper() for result in mapped_results]))
        logger.info(f"用戶意圖分析: {keywords} -> {interest_topics}")
        return interest_topics

    def _calculate_hybrid_score(self, article: Dict[str, Any], user_keywords: List[str], interest_topics: List[str]) -> float:
        """計算單篇文章對於特定用戶偏好的混合關聯性分數"""
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

    def get_eligible_articles_for_user(self, subscription: Dict[str, Any], hours_limit: int = 6) -> List[Dict[str, Any]]:
        """為特定用戶獲取符合條件的文章"""
        user_id = subscription['user_id']
        keywords = subscription.get('keywords', [])
        frequency_type = subscription.get('push_frequency_type', 'daily')
        max_articles = db_manager.get_max_articles_for_frequency(frequency_type)

        logger.info(f"為用戶 {user_id[:8]}... 智能選擇文章 (最多 {max_articles} 篇)")

        try:
            cutoff_time = get_current_taiwan_time() - timedelta(hours=hours_limit)
            cutoff_iso = cutoff_time.isoformat()

            query_builder = db_manager.supabase.table("news_articles").select("*, tags")
            query_builder = query_builder.gte("published_at", cutoff_iso)
            query_builder = query_builder.order("published_at", desc=True)
            query_builder = query_builder.limit(max_articles * 5)

            result = query_builder.execute()
            all_articles = result.data if result.data else []

            logger.info(f"查詢到 {len(all_articles)} 篇最近 {hours_limit} 小時的文章")

            if not all_articles:
                logger.info(f"沒有找到最近 {hours_limit} 小時的文章")
                return []

            pushed_articles = self.get_user_pushed_articles(user_id, hours_limit * 2)
            pushed_urls = {article.get('news_articles', {}).get('original_url') for article in pushed_articles}

            unread_articles = [article for article in all_articles if article['original_url'] not in pushed_urls]

            logger.info(f"過濾後未推送文章: {len(unread_articles)} 篇")

            if not unread_articles:
                logger.info("沒有新的未推送文章")
                return []

            selected_articles = self.select_articles_by_preference(unread_articles, keywords, max_articles)

            logger.info(f"最終選擇文章: {len(selected_articles)} 篇")
            return selected_articles

        except Exception as e:
            logger.exception(f"獲取用戶文章時發生錯誤 for user {user_id[:8]}")
            return []

    def get_user_pushed_articles(self, user_id: str, hours_limit: int = 12) -> List[Dict[str, Any]]:
        """獲取用戶最近推送過的文章"""
        try:
            cutoff_time = get_current_taiwan_time() - timedelta(hours=hours_limit)
            cutoff_iso = cutoff_time.isoformat()

            result = db_manager.supabase.table("push_history").select(
                "*, news_articles(original_url)"
            ).eq("user_id", user_id).gte("pushed_at", cutoff_iso).execute()

            return result.data if result.data else []

        except Exception as e:
            logger.exception(f"獲取用戶推送歷史錯誤 for user {user_id[:8]}")
            return []

    def select_articles_by_preference(self, articles: List[Dict[str, Any]], keywords: List[str], max_count: int) -> List[Dict[str, Any]]:
        """根據用戶偏好，使用混合評分引擎選擇文章"""
        if not articles:
            return []

        if not keywords:
            logger.info(f"用戶無關鍵字，選擇最新 {max_count} 篇通用財經新聞")
            return articles[:max_count]

        logger.info(f"執行混合評分引擎，分析關鍵字: {', '.join(keywords)}")

        interest_topics = self._get_user_interest_topics(keywords)

        scored_articles = []
        for article in articles:
            score = self._calculate_hybrid_score(article, keywords, interest_topics)
            
            if score >= self.match_threshold:
                article_with_score = article.copy()
                article_with_score['relevance_score'] = score
                scored_articles.append(article_with_score)

        scored_articles.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        logger.info(f"評分完成: {len(scored_articles)} 篇文章分數高於門檻 {self.match_threshold}")
        for art in scored_articles[:5]:
             logger.info(f"   - [{art['relevance_score']:.2f}] {art['title'][:50]}...")

        return scored_articles[:max_count]

    def process_user_subscription(self, subscription: Dict[str, Any]) -> bool:
        """處理單個用戶的推送"""
        user_id = subscription['user_id']
        frequency_type = subscription.get('push_frequency_type', 'daily')

        logger.info(f"\n--- 處理用戶 {user_id[:8]}... 的推送 ({frequency_type}) ---")

        if not db_manager.should_push_now(subscription):
            logger.info(f"用戶 {user_id[:8]}... 不在推送時間窗口 (SKIP)")
            return False

        articles = self.get_eligible_articles_for_user(subscription, hours_limit=6)

        min_articles = 1
        if len(articles) < min_articles:
            logger.info(f"用戶 {user_id[:8]}... 沒有足夠的新文章 (需要至少 {min_articles} 篇)，跳過本次推送")
            return False

        delivery_platform = subscription.get('delivery_platform', 'discord')
        delivery_target = subscription['delivery_target']
        logger.info(f"開始推送 {len(articles)} 篇文章到 {delivery_platform}...")

        delivery_manager = get_delivery_manager()
        import asyncio
        success, failed_articles = asyncio.run(
            delivery_manager.send_to_platform(
                delivery_platform,
                delivery_target,
                articles,
                subscription
            )
        )

        if success:
            successful_articles = [article for article in articles if article not in failed_articles]

            article_ids = []
            for article in successful_articles:
                try:
                    result = db_manager.supabase.table("news_articles").select("id").eq(
                        "original_url", article['original_url']
                    ).execute()

                    if result.data:
                        article_ids.append(result.data[0]['id'])
                except Exception as e:
                    logger.warning(f"查找文章ID失敗: {e}")

            if article_ids:
                batch_success = db_manager.log_push_history(user_id, article_ids)
                if batch_success:
                    logger.info(f"已記錄推送歷史: {len(article_ids)} 篇文章")

                db_manager.mark_push_window_completed(user_id, frequency_type)

                asyncio.run(
                    delivery_manager.send_summary_message(
                        subscription.get('delivery_platform', 'discord'),
                        subscription['delivery_target'],
                        len(successful_articles),
                        len(articles),
                        frequency_type
                    )
                )

                logger.info(f"[SUCCESS] 用戶 {user_id[:8]}... 推送完成: {len(successful_articles)} 篇成功")
                return True

        logger.error(f"[FAIL] 用戶 {user_id[:8]}... 推送失敗")
        return False

    def run_smart_push(self) -> bool:
        """執行智能推送"""
        logger.info("=" * 60)
        logger.info("FinNews-Bot 智能推送器開始執行 (v2.0 - 混合評分引擎)")
        taiwan_time = get_current_taiwan_time()
        logger.info(f"執行時間: {format_taiwan_datetime(taiwan_time)}")
        logger.info("=" * 60)

        try:
            settings.validate()
            logger.info("[OK] 環境變數驗證成功")

            eligible_subscriptions = db_manager.get_eligible_subscriptions()

            if not eligible_subscriptions:
                logger.info("\n[INFO] 目前沒有符合推送時間的訂閱需要處理")
                logger.info("[INFO] 提示: 系統會在 08:00, 13:00, 20:00 (±30分鐘) 進行推送檢查")
                return True

            logger.info(f"\n[STATS] 本次推送分析:")
            logger.info(f"  - 符合推送條件的訂閱: {len(eligible_subscriptions)} 個")

            freq_stats = {}
            for sub in eligible_subscriptions:
                freq = sub.get('push_frequency_type', 'daily')
                freq_stats[freq] = freq_stats.get(freq, 0) + 1

            for freq, count in freq_stats.items():
                logger.info(f"    * {freq}: {count} 個訂閱")

            overall_success = False
            success_count = 0

            for subscription in eligible_subscriptions:
                success = self.process_user_subscription(subscription)
                if success:
                    overall_success = True
                    success_count += 1

            logger.info(f"\n[STATS] 推送結果統計:")
            logger.info(f"  - 處理訂閱: {len(eligible_subscriptions)} 個")
            logger.info(f"  - 推送成功: {success_count} 個")
            logger.info(f"  - 推送失敗: {len(eligible_subscriptions) - success_count} 個")

            if overall_success:
                logger.info(f"\n[SUCCESS] 智能推送任務完成！{success_count} 個用戶收到新聞")
            else:
                logger.warning(f"\n[WARN] 智能推送完成，但沒有成功推送任何內容")
                logger.info("[INFO] 可能原因: 沒有足夠的新文章，或用戶已在此時間窗口收到推送")

            return True

        except Exception as e:
            logger.critical("\n[ERROR] 智能推送任務失敗", exc_info=True)
            return False

        finally:
            logger.info("\n" + "=" * 60)
            logger.info("FinNews-Bot 智能推送器結束")
            taiwan_time = get_current_taiwan_time()
            logger.info(f"結束時間: {format_taiwan_datetime(taiwan_time)}")
            logger.info("=" * 60)

def main():
    """主執行函數"""
    setup_logging()
    pusher = SmartPusher()
    success = pusher.run_smart_push()
    return 0 if success else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
