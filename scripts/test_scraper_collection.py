#!/usr/bin/env python3
"""
臨時測試腳本：驗證 scraper.py 的 collect_news_from_topics 方法
"""

import sys
from pathlib import Path

# 添加項目根目錄到 Python 路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scraper.scraper import scraper_manager
from core.database import db_manager

def main():
    print("=" * 60)
    print("臨時測試腳本：驗證 scraper.py 的 collect_news_from_topics")
    print("=" * 60)

    # 硬編碼一個小的目標列表，用於測試
    test_targets = [
        {"topic_code": "TECH", "url": "https://finance.yahoo.com/topic/tech"},
        # {"topic_code": "CRYPTO", "url": "https://finance.yahoo.com/topic/crypto"},
    ]

    articles_limit_per_topic = 2 # 每個主題只處理2篇文章

    print(f"[INFO] 將對以下 {len(test_targets)} 個主題進行測試爬取，每個主題最多處理 {articles_limit_per_topic} 篇文章：")
    for target in test_targets:
        print(f"  - 主題: {target['topic_code']}, URL: {target['url']}")

    try:
        # 直接呼叫 scraper_manager 的新方法，並傳遞限制參數
        success, stats = scraper_manager.collect_news_from_topics(test_targets, articles_limit_per_topic)

        if success:
            print("\n[SUCCESS] collect_news_from_topics 測試執行成功！")
            print(f"  - 總共處理: {stats['total_processed']} 篇文章")
            print(f"  - 新增文章: {stats['newly_added']} 篇")
            print(f"  - 重複文章: {stats['duplicates']} 篇")
            print(f"  - 處理失敗: {stats['failed']} 篇")
        else:
            print("\n[WARN] collect_news_from_topics 測試執行完成，但可能存在問題。")

    except Exception as e:
        print(f"\n[ERROR] 測試腳本執行失敗: {e}")
        import traceback
        traceback.print_exc()

    finally:
        print("\n" + "=" * 60)
        print("測試腳本結束")
        print("=" * 60)

if __name__ == "__main__":
    main()
