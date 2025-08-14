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
from core.summary_quality_monitor import record_summary_quality, validate_chinese_text, validate_mixed_language_summary, get_quality_monitor

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

    def print_quality_report(self):
        """列印摘要品質報告"""
        try:
            monitor = get_quality_monitor()
            report = monitor.generate_quality_report()
            print("\n" + "="*60)
            print(report)
            print("="*60)
        except Exception as e:
            logger.error(f"產生品質報告失敗: {e}")
    
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

        # 在完成時列印品質報告
        if articles_to_save:
            logger.info("📊 正在產生摘要品質報告...")
            self.print_quality_report()
        
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
    
    def _validate_chinese_summary(self, summary: str) -> tuple[bool, float, float, bool, dict]:
        """驗證混合語言摘要的品質"""
        is_valid, chinese_ratio, has_forbidden_words, analysis = validate_mixed_language_summary(summary)
        
        # 計算品質分數
        quality_score = chinese_ratio
        
        # 如果包含禁用詞彙，大幅降低分數
        if has_forbidden_words:
            quality_score *= 0.3  # 嚴重懲罰禁用詞彙
        
        # 如果有未知英文詞彙，輕微降低分數
        if analysis.get('unknown_words'):
            unknown_count = len(analysis['unknown_words'])
            quality_score *= max(0.7, 1.0 - unknown_count * 0.1)  # 每個未知詞降低10%
        
        # 如果包含允許的專業術語，輕微提高分數（鼓勵專業性）
        if analysis.get('allowed_words'):
            allowed_count = len(analysis['allowed_words'])
            quality_score *= min(1.0, 1.0 + allowed_count * 0.02)  # 每個專業術語加分2%
        
        logger.debug(f"摘要語言驗證: 中文比例={chinese_ratio:.2f}, 禁用詞彙={has_forbidden_words}, 有效={is_valid}, 分數={quality_score:.2f}")
        logger.debug(f"詳細分析: {analysis}")
        
        return is_valid, quality_score, chinese_ratio, has_forbidden_words, analysis

    def generate_summary_and_tags(self, title: str, content: str) -> tuple:
        """同時生成摘要和AI標籤 - 增強版（確保中文輸出）"""
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
        
        # 新的平衡策略 Prompt - 英文指令框架配中文內容
        prompt = f'''You are a professional Taiwan financial news summarizer. Please complete the following tasks for this financial news:

News Title: {title}
News Content: {content[:1500]}

TASK 1 - Generate Summary:
- LANGUAGE: Must use Traditional Chinese (繁體中文) as primary language
- LENGTH: 80-120 characters
- CONTENT: Objective, neutral, highlight key financial data and insights
- PROPER NOUNS: For English company names, person names, or technical terms, you may keep them in English if they are commonly used in Taiwan financial media (e.g., Apple, Tesla, TSMC, GDP, AI, CEO, IPO)
- AVOID: English grammatical words (the, and, with, but, in, on, at, etc.)
- STYLE: Natural mix that Taiwanese readers would expect in financial news

TASK 2 - Assign Tags:
Select most relevant tags (max 3) from: {core_tags}

OUTPUT FORMAT (strictly follow JSON):
{{
  "summary": "主要使用繁體中文，可適當保留專業英文術語如Apple、GDP等",
  "tags": ["TAG1", "TAG2"],
  "confidence": 0.9
}}

CRITICAL: The summary should be primarily Traditional Chinese with appropriate English technical terms/company names where natural for Taiwan financial readers. Avoid English grammatical words completely.'''
        
        headers = {'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'}
        # 優化模型參數：提高 temperature 增加創造性，增加 max_tokens
        data = {'model': 'gpt-3.5-turbo', 'messages': [{'role': 'user', 'content': prompt}], 'max_tokens': 350, 'temperature': 0.4}
        
        import json
        import time
        max_retries = 2
        start_time = time.time()
        
        for attempt in range(max_retries + 1):
            try:
                logger.info(f"🤖 嘗試生成摘要 (第 {attempt + 1}/{max_retries + 1} 次): {title[:50]}...")
                
                response = requests.post('https://api.openai.com/v1/chat/completions', headers=headers, json=data, timeout=30)
                if response.status_code == 200:
                    result = response.json()['choices'][0]['message']['content']
                    
                    try:
                        parsed = json.loads(result)
                        summary = parsed.get('summary', f"摘要解析失敗。原標題：{title}")
                        tags = parsed.get('tags', [])
                        
                        if not isinstance(tags, list):
                            tags = []
                        
                        # 驗證混合語言摘要品質
                        is_valid_summary, quality_score, chinese_ratio, has_forbidden_words, analysis = self._validate_chinese_summary(summary)
                        generation_time = time.time() - start_time
                        
                        # 記錄品質指標（包含詳細分析）
                        record_summary_quality(
                            title=title,
                            summary=summary,
                            chinese_ratio=chinese_ratio,
                            has_english_words=has_forbidden_words,  # 這裡指的是禁用詞彙
                            is_valid=is_valid_summary,
                            quality_score=quality_score,
                            attempt_count=attempt + 1,
                            generation_time=generation_time,
                            success=is_valid_summary,
                            detailed_analysis=analysis
                        )
                        
                        if is_valid_summary:
                            allowed_terms = ', '.join(analysis.get('allowed_words', [])) if analysis.get('allowed_words') else '無'
                            logger.info(f"✅ 摘要生成成功 (品質: {quality_score:.2f}, 專業術語: {allowed_terms}): {summary[:50]}...")
                            return summary, tags
                        else:
                            # 提供詳細的失敗原因
                            failure_reasons = []
                            if chinese_ratio < 0.6:
                                failure_reasons.append(f"中文比例過低({chinese_ratio:.1%})")
                            if has_forbidden_words:
                                forbidden_list = ', '.join(analysis.get('forbidden_words', []))
                                failure_reasons.append(f"包含禁用詞彙({forbidden_list})")
                            
                            reason_text = '; '.join(failure_reasons)
                            logger.warning(f"⚠️ 摘要不合格 (分數: {quality_score:.2f}): {reason_text}")
                            
                            if attempt < max_retries:
                                logger.info(f"🔄 將重新嘗試生成改進版摘要...")
                                # 根據具體問題加強提示
                                retry_hints = []
                                if chinese_ratio < 0.6:
                                    retry_hints.append("Use MORE Traditional Chinese characters")
                                if has_forbidden_words:
                                    forbidden_list = ', '.join(analysis.get('forbidden_words', []))
                                    retry_hints.append(f"AVOID these English words: {forbidden_list}")
                                
                                retry_prompt = prompt + f"\n\n**RETRY INSTRUCTIONS**: {'; '.join(retry_hints)}. Focus on natural Traditional Chinese with appropriate technical terms only."
                                data['messages'][0]['content'] = retry_prompt
                                continue
                            else:
                                logger.error(f"❌ 多次重試後仍無法生成合格摘要: {reason_text}")
                                
                                # 記錄最終失敗（已在上面記錄過）
                                return f"摘要品質驗證失敗: {reason_text}。原標題：{title}", tags
                                
                    except json.JSONDecodeError as e:
                        logger.error(f"JSON 解析失敗 (第 {attempt + 1} 次)。原始回應: {result[:200]}...")
                        if attempt >= max_retries:
                            # 記錄 JSON 解析失敗
                            record_summary_quality(
                                title=title,
                                summary="",
                                chinese_ratio=0.0,
                                has_english_words=False,
                                is_valid=False,
                                quality_score=0.0,
                                attempt_count=attempt + 1,
                                generation_time=time.time() - start_time,
                                success=False,
                                error_message=f"JSON解析失敗: {str(e)}"
                            )
                            return f"JSON 解析失敗。原標題：{title}", []
                        continue
                        
                else:
                    logger.error(f"OpenAI API 錯誤 (第 {attempt + 1} 次)。狀態碼: {response.status_code}, 回應: {response.text[:200]}")
                    if attempt >= max_retries:
                        # 記錄 API 錯誤
                        record_summary_quality(
                            title=title,
                            summary="",
                            chinese_ratio=0.0,
                            has_english_words=False,
                            is_valid=False,
                            quality_score=0.0,
                            attempt_count=attempt + 1,
                            generation_time=time.time() - start_time,
                            success=False,
                            error_message=f"API錯誤: {response.status_code}"
                        )
                        return f"API error. Title: {title}", []
                    continue
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"請求 OpenAI API 失敗 (第 {attempt + 1} 次): {e}")
                if attempt >= max_retries:
                    # 記錄網路錯誤
                    record_summary_quality(
                        title=title,
                        summary="",
                        chinese_ratio=0.0,
                        has_english_words=False,
                        is_valid=False,
                        quality_score=0.0,
                        attempt_count=attempt + 1,
                        generation_time=time.time() - start_time,
                        success=False,
                        error_message=f"網路請求失敗: {str(e)}"
                    )
                    return f"請求失敗。原標題：{title}", []
                continue
                
            except Exception as e:
                logger.error(f"處理 OpenAI 回應時發生未知錯誤 (第 {attempt + 1} 次): {e}")
                if attempt >= max_retries:
                    # 記錄未知錯誤
                    record_summary_quality(
                        title=title,
                        summary="",
                        chinese_ratio=0.0,
                        has_english_words=False,
                        is_valid=False,
                        quality_score=0.0,
                        attempt_count=attempt + 1,
                        generation_time=time.time() - start_time,
                        success=False,
                        error_message=f"未知錯誤: {str(e)}"
                    )
                    return f"處理失敗。原標題：{title}", []
                continue
        
        # 如果所有重試都失敗了
        logger.error(f"❌ 經過 {max_retries + 1} 次嘗試後，摘要生成完全失敗")
        
        # 記錄最終失敗
        record_summary_quality(
            title=title,
            summary="",
            chinese_ratio=0.0,
            has_english_words=False,
            is_valid=False,
            quality_score=0.0,
            attempt_count=max_retries + 1,
            generation_time=time.time() - start_time,
            success=False,
            error_message="所有重試尝試均失敗"
        )
        
        return f"[摘要生成失敗] 原標題：{title}", []

# Setup logging
setup_logging()

# Create a global scraper manager instance
scraper_manager = NewsScraperManager()