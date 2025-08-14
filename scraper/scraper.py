import os
import random
import time
import logging
from pathlib import Path
from typing import Union, List, Dict, Any, Tuple
import requests
from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from scraper.scraper_v2 import ScraperV2
from core.config import settings
from core.database import db_manager
from core.utils import parse_article_publish_time
from core.translation_service import translate_title_to_chinese
from core.logger_config import setup_logging

# Initialize logger
logger = logging.getLogger(__name__)

class NewsScraperManager:
    """News scraper manager for FinNews-Bot"""
    
    def __init__(self, use_v2_scraper: bool = False):
        self.debug_folder = self._create_debug_folder()
        self.use_v2_scraper = use_v2_scraper
        if self.use_v2_scraper:
            self.scraper_v2 = ScraperV2()
    
    def _create_debug_folder(self) -> Path:
        path = Path("debug_pages")
        path.mkdir(exist_ok=True)
        return path

    def collect_news_from_topics(self, targets: List[Dict[str, str]], max_articles_to_process: int = None) -> Tuple[bool, Dict[str, int]]:
        """新的主執行函式 - 根據目標主題列表收集新聞"""
        stats = {
            'total_processed': 0,
            'newly_added': 0,
            'duplicates': 0,
            'failed': 0
        }
        articles_to_save = []
        processed_urls_in_run = set() # 新增: 用於追蹤本次運行中已處理的URL

        for target in targets:
            topic_code = target['topic_code']
            url = target['url']
            logger.info(f"--- 開始處理主題: {topic_code} ---")
            
            news_list = self.scrape_yahoo_finance_list(url)
            if not news_list:
                logger.warning(f"未能從 {url} 爬取到任何新聞列表。")
                continue

            processed_for_topic = 0
            for news_item in news_list:
                # 新增檢查: 如果此URL在本輪運行中已處理，則跳過
                if news_item['link'] in processed_urls_in_run:
                    logger.info(f"文章在本輪已處理 (SKIP): {news_item['title'][:50]}...")
                    continue

                if max_articles_to_process is not None and processed_for_topic >= max_articles_to_process:
                    logger.info(f"已達到主題 {topic_code} 的處理上限 ({max_articles_to_process} 篇文章)，跳過剩餘文章。")
                    break

                stats['total_processed'] += 1
                
                if db_manager.is_article_processed(news_item['link']):
                    logger.info(f"文章已在資料庫中 (SKIP): {news_item['title'][:50]}...")
                    stats['duplicates'] += 1
                    processed_urls_in_run.add(news_item['link']) # 也將其加入，避免重複處理
                    continue

                logger.info(f"正在處理新文章: {news_item['title'][:50]}...")
                article_data = self._process_single_article(news_item, topic_code)
                
                if article_data:
                    articles_to_save.append(article_data)
                    processed_urls_in_run.add(news_item['link']) # 新增: 記錄已處理的URL
                    processed_for_topic += 1
                else:
                    stats['failed'] += 1

        if articles_to_save:
            logger.info(f"準備將 {len(articles_to_save)} 篇文章進行批次儲存...")
            success, count = db_manager.save_new_articles_batch(articles_to_save)
            if success:
                stats['newly_added'] = count
                if count < len(articles_to_save):
                    stats['failed'] += (len(articles_to_save) - count)
            else:
                stats['failed'] += len(articles_to_save)

        return True, stats

    def scrape_yahoo_finance_list(self, url: str) -> List[Dict[str, str]]:
        """使用 requests 爬取 Yahoo Finance 的新聞列表頁"""
        logger.info(f"正在從 {url} 爬取新聞列表...")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36'
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            items = soup.select("li.stream-item")
            result = []
            seen_links = set()
            
            for item in items:
                a_tag = item.select_one('a[href*="/news/"]')
                title_tag = item.select_one('h3')
                if a_tag and title_tag:
                    link = requests.compat.urljoin(url, a_tag['href'])
                    if link not in seen_links:
                        seen_links.add(link)
                        result.append({
                            'title': title_tag.get_text(strip=True), 
                            'link': link
                        })
            
            logger.info(f"成功爬取到 {len(result)} 則新聞標題。")
            return result
        except Exception as e:
            logger.exception(f"爬取新聞列表失敗: {url}")
            return []
    
    def _process_single_article(self, news_item: Dict[str, str], topic_code: str) -> Union[Dict[str, Any], None]:
        """處理單篇文章 - 爬取內容、生成摘要/標籤，並附上來源主題"""
        try:
            content = self.scrape_article_content(news_item['link'])
            if not content:
                return None

            summary, tags = self.generate_summary_and_tags(news_item['title'], content)
            if "[摘要生成失敗" in summary:
                return None

            # 🌍 新增翻譯功能：翻譯標題為中文
            translated_title = None
            try:
                logger.info(f"🌍 開始翻譯標題: {news_item['title'][:50]}...")
                translated_title = translate_title_to_chinese(news_item['title'])
                
                if translated_title:
                    logger.info(f"✅ 翻譯成功: {translated_title[:50]}...")
                else:
                    logger.info("ℹ️ 標題無需翻譯或翻譯失敗，將儲存原標題")
                    
            except Exception as e:
                logger.warning(f"⚠️ 翻譯過程發生錯誤，但不影響文章處理: {e}")
                translated_title = None

            published_at = parse_article_publish_time()
            
            logger.debug(f"Inside _process_single_article - Type of news_item['link']: {type(news_item['link'])}")
            logger.debug(f"Inside _process_single_article - Type of tags: {type(tags)}")

            article_data = {
                'original_url': news_item['link'], 
                'source': 'yahoo_finance', 
                'title': news_item['title'], 
                'summary': summary,
                'translated_title': translated_title,  # 🌍 新增翻譯標題欄位
                'tags': tags,
                'topics': [topic_code],
                'published_at': published_at.isoformat()
            }
            
            return article_data
            
        except Exception as e:
            logger.exception(f"處理文章時發生錯誤: {news_item.get('link', 'N/A')}")
            return None

    def scrape_article_content(self, url: str) -> Union[str, None]:
        if self.use_v2_scraper:
            logger.info(f"使用 ScraperV2 抓取: {url[:70]}...")
            result = self.scraper_v2._scrape_single_article(url)
            if result['success']:
                return result['content']
            else:
                logger.error(f"ScraperV2 抓取失敗: {result['error']} for url: {url}")
                return None
        else:
            logger.info(f"使用 Selenium 正在啟動瀏覽器抓取: {url[:70]}...")
            
            chrome_options = Options()
            chrome_options.add_argument("--headless=new")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1024,768")
            chrome_options.add_argument("user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36")

            driver = None
            try:
                driver = webdriver.Chrome(options=chrome_options)
                driver.set_page_load_timeout(settings.SCRAPER_TIMEOUT)
                driver.get(url)

                try:
                    consent_button_locator = (By.CSS_SELECTOR, "button.consent-button[value='agree'], button[name='agree']")
                    consent_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable(consent_button_locator)
                    )
                    driver.execute_script("arguments[0].click();", consent_button)
                    time.sleep(random.uniform(1, 2))
                except TimeoutException:
                    logger.debug("No consent button found.")
                    pass

                content_container_locator = (By.CSS_SELECTOR, '[data-testid="article-content-wrapper"], div.caas-body')
                WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located(content_container_locator)
                )
                
                soup = BeautifulSoup(driver.page_source, "html.parser")
                body = soup.select_one('[data-testid="article-content-wrapper"], div.caas-body')

                if body:
                    content_text = "\n".join(p.get_text(strip=True) for p in body.find_all("p") if p.get_text(strip=True))
                    if content_text:
                        logger.info(f"成功擷取文章內文，約 {len(content_text)} 字。")
                        return content_text
                
                logger.warning(f"未找到主要內文容器 for url: {url}")
                return None

            except Exception as e:
                logger.exception(f"使用 Selenium 擷取內文時發生錯誤: {url}")
                return None
            finally:
                if driver:
                    driver.quit()
    
    def generate_summary_and_tags(self, title: str, content: str) -> tuple:
        """同時生成摘要和AI標籤"""
        api_key = os.environ.get('OPENAI_API_KEY')
        if not api_key:
            logger.error("OPENAI_API_KEY not found, cannot generate summary and tags.")
            return f"Summary generation failed. Title: {title}", []
        
        # 使用統一標籤管理系統
        try:
            from scripts.dynamic_tags import get_tags_for_scraper
            core_tags = get_tags_for_scraper()
        except Exception as e:
            logger.warning(f"Failed to load dynamic tags, using fallback: {e}")
            # 降級到硬編碼標籤作為備用
            core_tags = [
                "APPLE", "TSMC", "TESLA", "AI_TECH", "CRYPTO",
                "STOCK_MARKET", "ECONOMIES", "LATEST", "EARNINGS", 
                "TECH", "ELECTRIC_VEHICLES", "FEDERAL_RESERVE",
                "HOUSING", "ENERGY", "HEALTHCARE", "FINANCE",
                "TARIFFS", "TRADE", "COMMODITIES", "BONDS"
            ]
        
        prompt = f'''
請為以下財經新聞同時完成兩個任務：
新聞標題：{title}
新聞內容：{content[:1500]}
任務1 - 生成摘要：
- 使用繁體中文, 80-120字之間, 客觀中立, 突出關鍵資訊
任務2 - 分配標籤：
從以下標籤庫選擇最相關的（最多3個）：{core_tags}
請返回JSON格式：
{{
  "summary": "摘要內容...",
  "tags": ["TAG1", "TAG2"],
  "confidence": 0.9
}}
'''
        headers = {'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'}
        data = {'model': 'gpt-3.5-turbo', 'messages': [{'role': 'user', 'content': prompt}], 'max_tokens': 300, 'temperature': 0.2}
        
        import json
        try:
            response = requests.post('https://api.openai.com/v1/chat/completions', headers=headers, json=data, timeout=30)
            if response.status_code == 200:
                result = response.json()['choices'][0]['message']['content']
                try:
                    parsed = json.loads(result)
                    summary = parsed.get('summary', f"摘要解析失敗。原標題：{title}")
                    tags = parsed.get('tags', [])
                    if not isinstance(tags, list):
                        tags = []
                    return summary, tags
                except json.JSONDecodeError:
                    logger.error(f"JSON 解析失敗。原始回應: {result}")
                    return f"JSON 解析失敗。原標題：{title}", []
            else:
                logger.error(f"OpenAI API 錯誤。狀態碼: {response.status_code}, 回應: {response.text}")
                return f"API error. Title: {title}", []
        except requests.exceptions.RequestException as e:
            logger.exception("請求 OpenAI API 失敗")
            return f"請求失敗。原標題：{title}", []
        except Exception as e:
            logger.exception("處理 OpenAI 回應時發生未知錯誤")
            return f"處理失敗。原標題：{title}", []

# Setup logging
setup_logging()

# Create a global scraper manager instance
scraper_manager = NewsScraperManager()