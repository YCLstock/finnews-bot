import asyncio
import sys
from pathlib import Path
import logging

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.logger_config import setup_logging
from core.delivery_manager import get_delivery_manager

# Get a logger for this script
logger = logging.getLogger(__name__)

async def main():
    """
    Main function to run the email delivery test.
    """
    logger.info("🚀 Starting Email Delivery Test...")

    # 1. Define the recipient email address
    recipient_email = "limyuha27@gmail.com"
    logger.info(f"📬 Test recipient: {recipient_email}")

    # 2. Create mock subscription data
    mock_subscription = {
        "user_id": "test-user-123",
        "delivery_platform": "email",
        "delivery_target": recipient_email,
        "push_frequency_type": "daily",
        "summary_language": "zh-tw" # or 'en' to test the English template
    }
    logger.info("📄 Created mock subscription data.")

    # 3. Create mock article data to test the template
    mock_articles = [
        {
            "title": "【測試新聞】AI 科技取得重大突破",
            "summary": "這是一則測試用的新聞摘要。科學家今日宣布在人工智能領域取得了一項革命性的進展，預計將對多個行業產生深遠影響。這項新技術的核心是一種更高效的神經網絡模型。",
            "original_url": "https://example.com/news/ai-breakthrough"
        },
        {
            "title": "[Test News] Global Markets Respond to New Tech Policies",
            "summary": "This is a test summary for a second news article. Global stock markets showed a mixed response to the newly announced technology regulations. Investors are cautiously optimistic about the long-term outlook.",
            "original_url": "https://example.com/news/market-response"
        }
    ]
    logger.info(f"📰 Created {len(mock_articles)} mock articles for the test email.")

    # 4. Get the delivery manager
    delivery_manager = get_delivery_manager()
    logger.info("🚚 Fetched the delivery manager.")

    # 5. Attempt to send the email
    logger.info("✉️ Attempting to send the test email via delivery manager...")
    logger.info("   (This will use the SMTP settings from your environment variables)")

    try:
        # The send_to_platform is an async function
        success, failed_articles = await delivery_manager.send_to_platform(
            platform='email',
            target=recipient_email,
            articles=mock_articles,
            subscription=mock_subscription
        )

        if success:
            logger.info("✅ The email sending process was completed successfully by the delivery manager.")
            logger.info(f"   Please check the inbox of {recipient_email} (and the spam folder).")
        else:
            logger.error("❌ The delivery manager reported a failure in the sending process.")
            if failed_articles:
                logger.error(f"   Details: {len(failed_articles)} articles failed to send.")

    except Exception as e:
        logger.critical("An unexpected error occurred during the test.", exc_info=True)
        logger.error("   Please ensure your SMTP settings (SMTP_SERVER, SMTP_PORT, SMTP_USER, SMTP_PASSWORD) in your .env file are correct.")

    logger.info("🏁 Email Delivery Test Finished.")


if __name__ == "__main__":
    # Setup centralized logging
    setup_logging()
    # Run the async main function
    asyncio.run(main())
