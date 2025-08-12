import sys
from pathlib import Path
import logging
import asyncio
from typing import Dict, Any

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.logger_config import setup_logging
from scripts.run_smart_pusher import SmartPusher
from core.database import db_manager
from core.delivery_manager import get_delivery_manager

# Get a logger for this script
logger = logging.getLogger(__name__)

def get_subscription_by_email(email: str):
    """Fetches a specific user subscription from Supabase by email."""
    try:
        logger.info(f"正在從資料庫查詢 '{email}' 的訂閱設定...")
        result = db_manager.supabase.table("subscriptions").select("*").eq("delivery_target", email).eq("delivery_platform", "email").limit(1).execute()
        
        if result.data:
            logger.info("成功找到訂閱設定。")
            return result.data[0]
        else:
            logger.error(f"在資料庫中找不到 '{email}' 的 Email 訂閱設定。")
            return None
    except Exception:
        logger.exception("查詢訂閱設定時發生資料庫錯誤。")
        return None

def force_process_subscription(pusher: SmartPusher, subscription: Dict[str, Any]) -> bool:
    """
    A special version of process_user_subscription that BYPASSES the time window check.
    This is for testing purposes only.
    """
    user_id = subscription['user_id']
    frequency_type = subscription.get('push_frequency_type', 'daily')

    logger.info(f"--- 執行強制推送給用戶 {user_id[:8]}... (繞過時間檢查) ---")

    # The 'if not db_manager.should_push_now(subscription):' check is intentionally removed for this test.

    # Use a wider window for testing to increase chances of finding articles
    articles = pusher.get_eligible_articles_for_user(subscription, hours_limit=24)

    min_articles = 1
    if len(articles) < min_articles:
        logger.warning(f"用戶 {user_id[:8]}... 在過去24小時內沒有足夠的新文章 (需要至少 {min_articles} 篇)")
        return False

    delivery_platform = subscription.get('delivery_platform', 'discord')
    delivery_target = subscription['delivery_target']
    logger.info(f"準備強制推送 {len(articles)} 篇文章到 {delivery_platform}...")

    delivery_manager = get_delivery_manager()
    
    async def send_async():
        return await delivery_manager.send_to_platform(
            delivery_platform,
            delivery_target,
            articles,
            subscription
        )
    
    success, failed_articles = asyncio.run(send_async())

    if success:
        successful_articles = [article for article in articles if article not in failed_articles]
        article_ids = [article['id'] for article in successful_articles if 'id' in article]

        if article_ids:
            batch_success = db_manager.log_push_history(user_id, article_ids)
            if batch_success:
                logger.info(f"已記錄推送歷史: {len(article_ids)} 篇文章")

            # In a real scenario, we would mark the push window, but we skip it here
            # to allow repeated testing.
            logger.info("測試模式：跳過更新 `last_pushed_at` 時間戳。")

            async def send_summary_async():
                await delivery_manager.send_summary_message(
                    subscription.get('delivery_platform', 'discord'),
                    subscription['delivery_target'],
                    len(successful_articles),
                    len(articles),
                    frequency_type
                )
            # asyncio.run(send_summary_async()) # Summary message might be annoying for tests

            logger.info(f"用戶 {user_id[:8]}... 強制推送完成: {len(successful_articles)} 篇成功")
            return True

    logger.error(f"用戶 {user_id[:8]}... 強制推送失敗")
    return False


def main():
    """
    Main function to run a real push test for a single user, with force option.
    """
    setup_logging()
    logger.info("🚀 Starting Real Email Push Test (with Force Logic)...")

    target_email = "kiyouneko@gmail.com"
    subscription = get_subscription_by_email(target_email)

    if not subscription:
        logger.error("測試無法繼續，因為找不到對應的訂閱資料。")
        return

    pusher = SmartPusher()
    
    # Call the new FORCE function
    success = force_process_subscription(pusher, subscription)

    if not success:
        logger.warning("⚠️ 初次強制推送未發送任何內容，嘗試使用備用主題進行強制推送...")
        fallback_subscription = subscription.copy()
        fallback_keywords = ["AI_TECH","CRYPTO"]
        fallback_subscription['keywords'] = fallback_keywords
        logger.info(f"使用備用關鍵字進行推送: {fallback_keywords}")

        success_fallback = force_process_subscription(pusher, fallback_subscription)
        
        if success_fallback:
            logger.info("✅ 備用推送成功。請檢查收件匣。")
        else:
            logger.error("❌ 備用推送也失敗了。可能近期沒有任何相關主題的文章。")
    else:
        logger.info("✅ 初始推送成功。請檢查收件匣。")
        
    logger.info("🏁 Real Email Push Test Finished.")


if __name__ == "__main__":
    main()