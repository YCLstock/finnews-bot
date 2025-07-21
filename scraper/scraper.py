import os
import random
import time
from pathlib import Path
from typing import Union, List, Dict, Any
import requests
from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from core.config import settings
from core.database import db_manager
from core.utils import generate_summary_optimized, send_batch_to_discord, create_push_summary_message, parse_article_publish_time

class NewsScraperManager:
    """News scraper manager for FinNews-Bot"""
    
    def __init__(self):
        self.debug_folder = self._create_debug_folder()
    
    def _create_debug_folder(self) -> Path:
        """創建一個用於存放除錯截圖的資料夾"""
        path = Path("debug_pages")
        path.mkdir(exist_ok=True)
        return path
    
    def scrape_yahoo_finance_list(self, url: str = None) -> List[Dict[str, str]]:
        """使用 requests 爬取 Yahoo Finance 的新聞列表頁"""
        if url is None:
            url = settings.YAHOO_FINANCE_URL
        
        print(f"News: 正在從 {url} 爬取新聞列表...")
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
            
            print(f"OK: 成功爬取到 {len(result)} 則新聞標題。")
            return result
        except Exception as e:
            print(f"Error: 爬取新聞列表失敗: {e}")
            return []
    
    def scrape_article_content(self, url: str) -> Union[str, None]:
        """
        使用 Selenium 爬取單篇新聞的內文
        - 強化偽裝以應對反爬蟲機制
        - 使用複合選擇器以應對多種頁面版面
        """
        print(f"Selenium: [Selenium] 正在啟動瀏覽器抓取完整 URL: {url}")
        
        # 導入必要模組
        import os
        import shutil
        import stat
        import platform
        
        chrome_options = Options()
        
        # 記憶體優化的Chrome設定
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        
        # 記憶體限制設定
        chrome_options.add_argument("--memory-pressure-off")
        chrome_options.add_argument("--max_old_space_size=1024")  # 限制JS堆記憶體為1GB
        chrome_options.add_argument("--aggressive-cache-discard")
        chrome_options.add_argument("--disable-background-timer-throttling")
        chrome_options.add_argument("--disable-renderer-backgrounding")
        chrome_options.add_argument("--disable-backgrounding-occluded-windows")
        chrome_options.add_argument("--disable-background-networking")
        
        # 功能禁用（減少記憶體佔用）
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-plugins")
        chrome_options.add_argument("--disable-images")  # 禁用圖片載入
        chrome_options.add_argument("--disable-javascript")  # 禁用JavaScript（新聞內容通常在HTML中）
        chrome_options.add_argument("--disable-css")  # 禁用CSS
        chrome_options.add_argument("--disable-features=TranslateUI,VizDisplayCompositor")
        chrome_options.add_argument("--disable-ipc-flooding-protection")
        
        # 窗口和渲染設定
        chrome_options.add_argument("--window-size=1024,768")  # 減小窗口尺寸
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--ignore-certificate-errors")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        
        # GitHub Actions特殊設定
        if os.environ.get('GITHUB_ACTIONS'):
            chrome_options.add_argument("--single-process")  # 強制單進程模式
            chrome_options.add_argument("--disable-software-rasterizer")
            chrome_options.add_argument("--disable-background-networking")
            print("🔧 GitHub Actions環境：啟用記憶體優化模式")
            
        chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # 設定User-Agent
        chrome_options.add_argument("user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36")

        driver = None
        try:
            # 使用Selenium 4.6+內建的driver管理（不需要webdriver-manager）
            print("Using Selenium built-in ChromeDriver management...")
            
            # Selenium會自動下載適合的ChromeDriver版本
            # 不需要手動指定Service路徑
            driver = webdriver.Chrome(options=chrome_options)
            print("Success: Chrome瀏覽器啟動成功（Selenium自動管理驅動）")
            
            driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                'source': "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            })
            
            driver.set_page_load_timeout(settings.SCRAPER_TIMEOUT)
            
            # 監控記憶體使用
            try:
                import psutil
                process = psutil.Process()
                memory_before = process.memory_info().rss / 1024 / 1024  # MB
                print(f"Memory: 瀏覽器啟動前記憶體: {memory_before:.1f} MB")
            except ImportError:
                print("Memory: psutil未安裝，跳過記憶體監控")
            
            print("正在訪問頁面...")
            driver.get(url)
            
            # 檢查瀏覽器是否仍然活著
            try:
                current_url = driver.current_url
                print(f"Success: 頁面載入成功: {current_url[:60]}...")
            except Exception as e:
                print(f"Warning: 頁面載入後檢查失敗: {e}")
                return None

            # 處理同意視窗
            try:
                consent_button_locator = (By.CSS_SELECTOR, "button.consent-button[value='agree'], button[name='agree']")
                consent_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable(consent_button_locator)
                )
                print("Cookie: 發現同意按鈕，正在點擊...")
                driver.execute_script("arguments[0].click();", consent_button)
                time.sleep(random.uniform(1, 2))
            except TimeoutException:
                print("OK: 未在10秒內發現或不需點擊同意按鈕，繼續執行。")

            # 等待並抓取主要內容
            print("Waiting: 正在等待文章主要內容容器...")
            content_container_locator = (By.CSS_SELECTOR, '[data-testid="article-content-wrapper"], div.caas-body, div.atoms-wrapper, div.article-wrap.no-bb')
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located(content_container_locator)
            )
            print("Success: 內容容器已載入。")
            
            soup = BeautifulSoup(driver.page_source, "html.parser")
            body = soup.select_one('[data-testid="article-content-wrapper"], div.caas-body, div.atoms-wrapper, div.article-wrap.no-bb')

            if body:
                paragraphs = body.find_all("p")
                if not paragraphs:
                    print(f"Warning: 找到容器 {body.get('class')}，但裡面沒有 <p> 標籤。")
                    return None
                
                content_text = "\n".join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))
                
                if content_text:
                    print(f"Success: 成功擷取文章內文，約 {len(content_text)} 字。")
                    return content_text
                else:
                    print("Warning: 找到 <p> 標籤，但沒有有效文字內容。")
                    return None
            
            print("Error: 未能找到任何已知的內容容器 (data-testid, caas-body, atoms-wrapper, article-wrap)。")
            return None

        except TimeoutException as e:
            print(f"Error: 擷取內文時頁面加載或元素等待超時。錯誤訊息: {e.msg}")
            screenshot_path = self.debug_folder / f"TIMEOUT_FAIL_{url.split('/')[-1].replace('.html', '')}.png"
            if driver: 
                driver.save_screenshot(str(screenshot_path))
            print(f"Screenshot: 錯誤畫面已截圖: {screenshot_path}")
            return None
        except Exception as e:
            print(f"Error: 擷取內文時發生未預期錯誤: {e}")
            screenshot_path = self.debug_folder / f"GENERAL_FAIL_{url.split('/')[-1].replace('.html', '')}.png"
            if driver: 
                driver.save_screenshot(str(screenshot_path))
            print(f"Screenshot: 錯誤畫面已截圖: {screenshot_path}")
            return None
        finally:
            if driver:
                try:
                    # 強制清理瀏覽器資源
                    driver.quit()
                    print("Cleanup: 瀏覽器已關閉。")
                except Exception as cleanup_error:
                    print(f"Warning: 瀏覽器清理時發生錯誤: {cleanup_error}")
                    
                # 額外清理：強制垃圾回收
                import gc
                gc.collect()
                
                # 記憶體清理後檢查
                try:
                    import psutil
                    process = psutil.Process()
                    memory_after = process.memory_info().rss / 1024 / 1024  # MB
                    print(f"Memory: 清理後記憶體: {memory_after:.1f} MB")
                except ImportError:
                    pass
    
    def generate_summary_and_tags(self, title: str, content: str) -> tuple:
        """同時生成摘要和AI標籤，節省token使用"""
        import os
        import json
        import requests
        
        api_key = os.environ.get('OPENAI_API_KEY')
        if not api_key:
            print("Missing OpenAI API key, using fallback")
            return f"Summary generation failed. Title: {title}", self._generate_fallback_tags(title, content)
        
        # 核心標籤庫
        core_tags = ["APPLE", "TSMC", "TESLA", "AI_TECH", "CRYPTO"]
        
        prompt = f"""
請為以下財經新聞同時完成兩個任務：

新聞標題：{title}
新聞內容：{content[:1500]}

任務1 - 生成摘要：
- 使用繁體中文
- 80-120字之間
- 客觀中立，突出關鍵資訊
- 適合投資人快速閱讀

任務2 - 分配標籤：
從以下標籤庫選擇最相關的（最多3個）：
- APPLE: 蘋果公司 (iPhone, Mac, AAPL股票)
- TSMC: 台積電 (半導體, 晶圓代工)  
- TESLA: 特斯拉 (電動車, 馬斯克)
- AI_TECH: AI科技 (人工智慧, AI晶片)
- CRYPTO: 加密貨幣 (比特幣, 區塊鏈)

請返回JSON格式：
{{
  "summary": "這裡是摘要內容...",
  "tags": ["TAG1", "TAG2"],
  "confidence": 0.95
}}
"""
        
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        data = {
            'model': 'gpt-3.5-turbo',
            'messages': [{'role': 'user', 'content': prompt}],
            'max_tokens': 300,
            'temperature': 0.2
        }
        
        try:
            print("Generating summary and tags with AI...")
            response = requests.post('https://api.openai.com/v1/chat/completions', 
                                   headers=headers, json=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                content_result = result['choices'][0]['message']['content']
                
                try:
                    parsed = json.loads(content_result)
                    summary = parsed.get('summary', f"摘要解析失敗。原標題：{title}")
                    tags = parsed.get('tags', [])
                    confidence = parsed.get('confidence', 0)
                    
                    if confidence > 0.7:
                        print(f"AI processing successful: Summary({len(summary)} chars) + Tags{tags}")
                        return summary, tags
                    else:
                        print(f"Low confidence({confidence}), using fallback")
                        return summary, self._generate_fallback_tags(title, content)
                        
                except json.JSONDecodeError as e:
                    print(f"JSON parsing failed: {e}")
                    return f"Summary parsing failed. Title: {title}", self._generate_fallback_tags(title, content)
            else:
                print(f"OpenAI API error: {response.status_code}")
                return f"API error. Title: {title}", self._generate_fallback_tags(title, content)
                
        except Exception as e:
            print(f"Summary and tags generation failed: {e}")
            return f"Processing failed. Title: {title}", self._generate_fallback_tags(title, content)
    
    def _generate_fallback_tags(self, title: str, content: str) -> list:
        """備用規則式標籤生成"""
        text = f"{title} {content}".lower()
        tags = []
        
        # 規則式匹配
        tag_keywords = {
            "APPLE": ["apple", "iphone", "mac", "aapl", "蘋果", "庫克"],
            "TSMC": ["tsmc", "taiwan semiconductor", "台積電", "晶圓", "半導體", "2330"],
            "TESLA": ["tesla", "tsla", "musk", "特斯拉", "馬斯克", "電動車"],
            "AI_TECH": ["ai", "artificial intelligence", "chatgpt", "openai", "人工智慧", "機器學習", "ai晶片"],
            "CRYPTO": ["bitcoin", "cryptocurrency", "blockchain", "比特幣", "加密貨幣", "區塊鏈", "btc"]
        }
        
        for tag, keywords in tag_keywords.items():
            if any(keyword in text for keyword in keywords):
                tags.append(tag)
        
        result_tags = tags[:3]  # 最多3個標籤
        print(f"Fallback tags generated: {result_tags}")
        return result_tags
    
    def process_news_for_subscriptions(self) -> bool:
        """
        主執行函式 - 處理所有訂閱的新聞（批量版本）
        根據新的推送頻率和批量處理需求優化
        """
        print("Starting intelligent news processing task...")
        
        # 獲取符合推送條件的訂閱
        eligible_subscriptions = db_manager.get_eligible_subscriptions()
        if not eligible_subscriptions:
            print("No subscriptions eligible for current push time, exiting.")
            return False

        # 爬取新聞列表
        news_list = self.scrape_yahoo_finance_list()
        if not news_list:
            print("Could not fetch any news from Yahoo Finance, exiting.")
            return False

        # 處理每個符合條件的訂閱
        overall_success = False
        for subscription in eligible_subscriptions:
            print(f"\n--- Processing 開始處理使用者 {subscription['user_id']} 的訂閱 ---")
            success = self._process_subscription_batch(subscription, news_list)
            if success:
                overall_success = True

        print(f"\nSuccess: 所有符合條件的訂閱任務處理完畢。")
        return overall_success
    
    def _process_subscription_batch(self, subscription: Dict[str, Any], news_list: List[Dict[str, str]]) -> bool:
        """處理單一訂閱任務 - 批量收集和推送版本"""
        user_id = subscription['user_id']
        frequency_type = subscription.get('push_frequency_type', 'daily')
        keywords = subscription.get("keywords", [])
        max_articles = db_manager.get_max_articles_for_frequency(frequency_type)
        
        print(f"Checking: 為用戶 {user_id} 收集符合條件的新聞 (最多 {max_articles} 則)")
        
        # 收集符合條件的新聞
        collected_articles = []
        processed_count = 0
        failed_count = 0
        
        for news_item in news_list:
            # 檢查是否已達到最大數量
            if len(collected_articles) >= max_articles:
                print(f"Stats: 已收集到 {max_articles} 則新聞，停止收集")
                break
            
            # 檢查是否已處理
            if db_manager.is_article_processed(news_item['link']):
                continue
            
            # 檢查關鍵字匹配
            if keywords and not any(keyword.lower() in news_item['title'].lower() for keyword in keywords):
                continue
            
            print(f"Found: 找到符合關鍵字的文章: {news_item['title'][:60]}...")
            processed_count += 1
            
            # 嘗試處理文章
            article_data = self._process_single_article(news_item)
            if article_data:
                collected_articles.append(article_data)
                print(f"Success: 文章處理成功 ({len(collected_articles)}/{max_articles})")
            else:
                failed_count += 1
                print(f"Error: 文章處理失敗")
                
            # 如果已收集足夠的文章，提前結束
            if len(collected_articles) >= max_articles:
                break
        
        # 推送結果統計
        print(f"\nStats: 收集結果統計:")
        print(f"  - 嘗試處理: {processed_count} 篇")
        print(f"  - 成功收集: {len(collected_articles)} 篇")
        print(f"  - 處理失敗: {failed_count} 篇")
        
        if not collected_articles:
            print(f"[INFO] No suitable articles found for user {user_id}")
            return False
        
        # 批量推送到 Discord
        print(f"\nSending: 開始推送 {len(collected_articles)} 則新聞到 Discord...")
        success, failed_articles = send_batch_to_discord(
            subscription['delivery_target'], 
            collected_articles, 
            subscription
        )
        
        if success:
            # 儲存成功推送的文章並記錄歷史
            successful_articles = [article for article in collected_articles if article not in failed_articles]
            article_ids = []
            
            for article in successful_articles:
                article_id = db_manager.save_new_article(article)
                if article_id:
                    article_ids.append(article_id)
            
            if article_ids:
                # 記錄推送歷史（批量記錄）
                batch_success = db_manager.log_push_history(user_id, article_ids)
                if batch_success:
                    print(f"Logging 已記錄推送歷史: {len(article_ids)} 篇文章")
                
                # 標記推送窗口為已完成
                db_manager.mark_push_window_completed(user_id, frequency_type)
                
                # 發送推送總結消息
                create_push_summary_message(
                    subscription['delivery_target'],
                    len(successful_articles),
                    len(collected_articles),
                    frequency_type
                )
                
                print(f"Completed: 用戶 {user_id} 的推送任務完成: {len(successful_articles)} 則成功")
                return True
        
        print(f"Error: 用戶 {user_id} 的推送任務失敗")
        return False
    
    def _process_single_article(self, news_item: Dict[str, str]) -> Union[Dict[str, Any], None]:
        """處理單篇文章 - 爬取內容並生成摘要"""
        try:
            # 抓取內容
            content = self.scrape_article_content(news_item['link'])
            if not content:
                return None

            # 同時生成摘要和AI標籤（節省token）
            summary, tags = self.generate_summary_and_tags(news_item['title'], content)
            if "[摘要生成失敗" in summary:
                return None

            # 解析文章發布時間
            published_at = parse_article_publish_time()
            
            # 構建文章數據
            article_data = {
                'original_url': news_item['link'], 
                'source': 'yahoo_finance', 
                'title': news_item['title'], 
                'summary': summary,
                'tags': tags,  # 新增AI標籤
                'published_at': published_at.isoformat()  # 轉換為 ISO 格式字符串
            }
            
            return article_data
            
        except Exception as e:
            print(f"Error: 處理文章時發生錯誤: {e}")
            return None

# Create a global scraper manager instance
scraper_manager = NewsScraperManager() 