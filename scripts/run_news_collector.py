#!/usr/bin/env python3
"""
新聞內容收集器 (News Collector)
- 定期執行，分析所有用戶的興趣，並智能地爬取最相關的主題新聞。
- 將爬取與推送徹底解耦，專職為資料庫填充高質量的候選文章。
"""

import sys
from pathlib import Path
from collections import Counter

# 添加項目根目錄到 Python 路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scraper.scraper import scraper_manager
from core.database import db_manager
from core.topics_mapper import topics_mapper
from core.utils import get_current_taiwan_time, format_taiwan_datetime

class NewsCollector:
    """
    需求驅動的新聞收集器
    """
    def __init__(self, top_n_topics: int = 3):
        """
        初始化收集器
        Args:
            top_n_topics: 每次執行時，要爬取的最熱門主題數量。
        """
        self.top_n_topics = top_n_topics
        self.YAHOO_TOPIC_URL_BASE = "https://finance.yahoo.com/topic/"

    def _analyze_user_demands(self) -> list:
        """
        分析所有活躍用戶的關鍵字，生成一個帶權重的「主題熱度」列表。
        """
        print("[INFO] 正在分析全體用戶的訂閱需求...")
        try:
            result = db_manager.supabase.table("subscriptions").select("keywords").eq("is_active", True).execute()
            all_subscriptions = result.data if result.data else []

            if not all_subscriptions:
                print("[WARN] 資料庫中沒有活躍的訂閱，無法進行需求分析。" )
                return []

            # 1. 匯總所有用戶的關鍵字
            all_keywords = []
            for sub in all_subscriptions:
                keywords = sub.get("keywords")
                if keywords and isinstance(keywords, list):
                    all_keywords.extend(keywords)
            
            if not all_keywords:
                print("[WARN] 活躍用戶沒有設定任何關鍵字。" )
                return []

            print(f"[STATS] 找到 {len(all_keywords)} 個關鍵字，來自 {len(all_subscriptions)} 個活躍訂閱。" )

            # 2. 使用 topics_mapper 將關鍵字映射到主題
            # 這裡我們假設 map_keywords_to_topics 能夠處理大量關鍵字並返回所有匹配項
            # 我們需要一個更全面的映射結果，而不僅僅是 top N
            mapped_topics = topics_mapper.map_keywords_to_topics(all_keywords)

            # 3. 計算每個主題的熱度分數
            topic_heatmap = Counter()
            for topic, score in mapped_topics:
                topic_heatmap[topic] += score
            
            # 4. 選出最熱門的 N 個主題
            most_common_topics = topic_heatmap.most_common(self.top_n_topics)
            
            print(f"[SUCCESS] 需求分析完成。最熱門的 {self.top_n_topics} 個主題是: {most_common_topics}")
            return most_common_topics

        except Exception as e:
            print(f"[ERROR] 用戶需求分析失敗: {e}")
            return []

    def run_collection(self):
        """
        執行完整的新聞收集流程
        """
        print("=" * 60)
        print("FinNews-Bot 新聞內容收集器開始執行")
        taiwan_time = get_current_taiwan_time()
        print(f"執行時間: {format_taiwan_datetime(taiwan_time)}")
        print("=" * 60)

        # 1. 分析用戶需求，確定爬取目標
        hot_topics = self._analyze_user_demands()

        if not hot_topics:
            print("[INFO] 未能確定熱門主題，本次收集任務跳過。" )
            return

        # 2. 根據熱門主題，構建爬取 URL 列表
        target_urls = []
        for topic_code, score in hot_topics:
            # 將主題代碼轉換為小寫以構建 URL
            url = f"{self.YAHOO_TOPIC_URL_BASE}{topic_code.lower()}"
            target_urls.append({"topic_code": topic_code, "url": url})

        print(f"\n[INFO] 本次爬取目標 ({len(target_urls)} 個):")
        for target in target_urls:
            print(f"  - 主題: {target['topic_code']}, URL: {target['url']}")

        

        # 3. 呼叫 scraper_manager 執行批量、定向的內容收集
        # (這一步驟假設 scraper_manager 中已經有了 collect_news_from_topics 方法)
        logger.info("[INFO] 開始執行定向新聞爬取與處理...")
        try:
            success, stats = scraper_manager.collect_news_from_topics(target_urls)
            
            if success:
                print("\n[SUCCESS] 新聞收集任務成功完成。" )
                print(f"  - 總共處理: {stats['total_processed']} 篇文章")
                print(f"  - 新增文章: {stats['newly_added']} 篇")
                print(f"  - 重複文章: {stats['duplicates']} 篇")
                print(f"  - 處理失敗: {stats['failed']} 篇")
            else:
                print("\n[WARN] 新聞收集任務執行完成，但可能存在問題。" )

        except AttributeError:
            print("\n[ERROR] scraper.scraper.NewsScraperManager 中缺少 'collect_news_from_topics' 方法。" )
            print("請先完成對 scraper 模組的改造。" )
        except Exception as e:
            print(f"\n[ERROR] 新聞收集過程中發生未知錯誤: {e}")

        finally:
            print("\n" + "=" * 60)
            print("新聞內容收集器結束")
            taiwan_time = get_current_taiwan_time()
            print(f"結束時間: {format_taiwan_datetime(taiwan_time)}")
            print("=" * 60)


def main(args=None):
    use_v2_scraper = False
    if args and "--scraper=v2" in args:
        use_v2_scraper = True
        print("[INFO] 啟用 ScraperV2 模式")

    # 根據參數初始化 scraper_manager
    # 注意：這裡直接修改了全局的 scraper_manager 實例
    global scraper_manager
    scraper_manager = NewsScraperManager(use_v2_scraper=use_v2_scraper)

    collector = NewsCollector(top_n_topics=3)
    collector.run_collection()
    return 0

if __name__ == "__main__":
    # 從 sys.argv 獲取參數，並傳遞給 main 函式
    exit_code = main(sys.argv[1:])
    sys.exit(exit_code)
