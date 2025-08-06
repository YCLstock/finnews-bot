import time
import schedule
import sys
from pathlib import Path

# 添加項目根目錄到 Python 路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 引入您的主程式
from scripts.run_news_collector import main as run_collector
from scripts.run_smart_pusher import main as run_pusher
from core.utils import setup_logger

# 設定主循環的 logger
logger = setup_logger('local_loop', 'local_loop.log')

def job_collector():
    logger.info("====== [JOB START] 執行新聞收集任務 ======")
    try:
        run_collector()
        logger.info("====== [JOB END] 新聞收集任務完成 ======")
    except Exception as e:
        logger.error(f"新聞收集任務執行失敗: {e}", exc_info=True)

def job_pusher():
    logger.info("====== [JOB START] 執行智能推送任務 ======")
    try:
        run_pusher()
        logger.info("====== [JOB END] 智能推送任務完成 ======")
    except Exception as e:
        logger.error(f"智能推送任務執行失敗: {e}", exc_info=True)

if __name__ == "__main__":
    logger.info("############################################################")
    logger.info("### FinNews-Bot 本地端主循環程式已啟動 ###")
    logger.info("############################################################")

    # --- 設定排程 ---
    # 爬蟲任務：每小時的 0 分時執行
    schedule.every().hour.at(":00").do(job_collector)

    # 推送任務：每天的 08:00, 13:00, 20:00 執行
    schedule.every().day.at("08:00").do(job_pusher)
    schedule.every().day.at("13:00").do(job_pusher)
    schedule.every().day.at("20:00").do(job_pusher)

    logger.info("排程已設定完成：")
    for job in schedule.get_jobs():
        logger.info(f"- {job}")

    # 立即執行一次，以便快速看到效果
    logger.info("程式啟動，立即執行一次新聞收集和推送...")
    job_collector()
    job_pusher()

    logger.info("首次任務執行完畢，進入定時循環模式。請保持此視窗開啟。")

    # --- 進入主循環 ---
    while True:
        schedule.run_pending()
        time.sleep(1)
