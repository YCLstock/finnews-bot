"""
FinNews-Bot 爬蟲模組
提供新聞爬取、處理、標籤分析功能
"""

from .scraper import NewsScraperManager, scraper_manager

__all__ = ['NewsScraperManager', 'scraper_manager']