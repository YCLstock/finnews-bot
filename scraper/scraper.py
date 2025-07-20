import os
import random
import time
from pathlib import Path
from typing import Union, List, Dict, Any
import requests
from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager

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
        
        print(f"📰 正在從 {url} 爬取新聞列表...")
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
            
            print(f"👍 成功爬取到 {len(result)} 則新聞標題。")
            return result
        except Exception as e:
            print(f"❌ 爬取新聞列表失敗: {e}")
            return []
    
    def scrape_article_content(self, url: str) -> Union[str, None]:
        """
        使用 Selenium 爬取單篇新聞的內文
        - 強化偽裝以應對反爬蟲機制
        - 使用複合選擇器以應對多種頁面版面
        """
        print(f"🦾 [Selenium] 正在啟動瀏覽器抓取完整 URL: {url}")
        
        # 導入必要模組
        import os
        import shutil
        import stat
        import platform
        from webdriver_manager.chrome import ChromeDriverManager
        
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
            # 清除舊的driver緩存
            cache_path = os.path.expanduser("~/.wdm")
            if os.path.exists(cache_path):
                try:
                    shutil.rmtree(cache_path)
                    print("🧹 已清除舊版ChromeDriver緩存")
                except:
                    pass
            
            # 下載並修復ChromeDriver路徑
            driver_path = ChromeDriverManager().install()
            
            # Linux環境特殊處理
            if platform.system() == "Linux":
                print(f"🔍 檢查ChromeDriver路徑: {driver_path}")
                
                # 檢查是否指向錯誤的文件或不可執行
                needs_fix = (
                    "THIRD_PARTY_NOTICES" in driver_path or 
                    not os.path.isfile(driver_path) or
                    not os.access(driver_path, os.X_OK)
                )
                
                if needs_fix:
                    print("⚠️ ChromeDriver路徑需要修復")
                    # 嘗試找到正確的chromedriver執行檔
                    driver_dir = os.path.dirname(driver_path)
                    base_dir = os.path.dirname(driver_dir)
                    
                    possible_paths = [
                        # 在同目錄下尋找
                        os.path.join(driver_dir, "chromedriver"),
                        # 在chromedriver-linux64子目錄中尋找
                        os.path.join(driver_dir, "chromedriver-linux64", "chromedriver"),
                        # 在父目錄中尋找
                        os.path.join(base_dir, "chromedriver"),
                        # 遞歸查找所有可能位置
                        os.path.join(base_dir, "chromedriver-linux64", "chromedriver"),
                    ]
                    
                    # 如果上述路徑都不存在，進行深度搜索
                    try:
                        for root, dirs, files in os.walk(base_dir):
                            if "chromedriver" in files:
                                candidate = os.path.join(root, "chromedriver")
                                if os.access(candidate, os.X_OK):
                                    possible_paths.append(candidate)
                    except Exception as e:
                        print(f"深度搜索失敗: {e}")
                    
                    # 嘗試每個可能的路徑
                    fixed = False
                    for path in possible_paths:
                        if os.path.isfile(path) and os.access(path, os.X_OK):
                            driver_path = path
                            print(f"🔧 修正ChromeDriver路徑: {driver_path}")
                            fixed = True
                            break
                    
                    if not fixed:
                        print("❌ 無法找到有效的ChromeDriver執行檔")
                        print(f"🔍 嘗試過的路徑: {possible_paths}")
                        return None
                
                # 確保執行權限
                if os.path.isfile(driver_path):
                    try:
                        current_permissions = os.stat(driver_path).st_mode
                        os.chmod(driver_path, current_permissions | stat.S_IEXEC)
                        print("✅ 已設置ChromeDriver執行權限")
                    except Exception as e:
                        print(f"⚠️ 設置執行權限失敗: {e}")
                        
                # 最終驗證
                if not os.access(driver_path, os.X_OK):
                    print("❌ ChromeDriver仍然不可執行")
                    return None
                else:
                    print(f"✅ ChromeDriver驗證通過: {driver_path}")
            
            service = Service(driver_path)
            driver = webdriver.Chrome(service=service, options=chrome_options)
            
            driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                'source': "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            })
            
            driver.set_page_load_timeout(settings.SCRAPER_TIMEOUT)
            
            # 監控記憶體使用
            try:
                import psutil
                process = psutil.Process()
                memory_before = process.memory_info().rss / 1024 / 1024  # MB
                print(f"💾 瀏覽器啟動前記憶體: {memory_before:.1f} MB")
            except ImportError:
                print("💾 psutil未安裝，跳過記憶體監控")
            
            print("正在訪問頁面...")
            driver.get(url)
            
            # 檢查瀏覽器是否仍然活著
            try:
                current_url = driver.current_url
                print(f"✅ 頁面載入成功: {current_url[:60]}...")
            except Exception as e:
                print(f"⚠️ 頁面載入後檢查失敗: {e}")
                return None

            # 處理同意視窗
            try:
                consent_button_locator = (By.CSS_SELECTOR, "button.consent-button[value='agree'], button[name='agree']")
                consent_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable(consent_button_locator)
                )
                print("🍪 發現同意按鈕，正在點擊...")
                driver.execute_script("arguments[0].click();", consent_button)
                time.sleep(random.uniform(1, 2))
            except TimeoutException:
                print("👍 未在10秒內發現或不需點擊同意按鈕，繼續執行。")

            # 等待並抓取主要內容
            print("⏳ 正在等待文章主要內容容器...")
            content_container_locator = (By.CSS_SELECTOR, '[data-testid="article-content-wrapper"], div.caas-body, div.atoms-wrapper, div.article-wrap.no-bb')
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located(content_container_locator)
            )
            print("✅ 內容容器已載入。")
            
            soup = BeautifulSoup(driver.page_source, "html.parser")
            body = soup.select_one('[data-testid="article-content-wrapper"], div.caas-body, div.atoms-wrapper, div.article-wrap.no-bb')

            if body:
                paragraphs = body.find_all("p")
                if not paragraphs:
                    print(f"⚠️ 找到容器 {body.get('class')}，但裡面沒有 <p> 標籤。")
                    return None
                
                content_text = "\n".join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))
                
                if content_text:
                    print(f"✅ 成功擷取文章內文，約 {len(content_text)} 字。")
                    return content_text
                else:
                    print("⚠️ 找到 <p> 標籤，但沒有有效文字內容。")
                    return None
            
            print("❌ 未能找到任何已知的內容容器 (data-testid, caas-body, atoms-wrapper, article-wrap)。")
            return None

        except TimeoutException as e:
            print(f"❌ 擷取內文時頁面加載或元素等待超時。錯誤訊息: {e.msg}")
            screenshot_path = self.debug_folder / f"TIMEOUT_FAIL_{url.split('/')[-1].replace('.html', '')}.png"
            if driver: 
                driver.save_screenshot(str(screenshot_path))
            print(f"📸 錯誤畫面已截圖: {screenshot_path}")
            return None
        except Exception as e:
            print(f"❌ 擷取內文時發生未預期錯誤: {e}")
            screenshot_path = self.debug_folder / f"GENERAL_FAIL_{url.split('/')[-1].replace('.html', '')}.png"
            if driver: 
                driver.save_screenshot(str(screenshot_path))
            print(f"📸 錯誤畫面已截圖: {screenshot_path}")
            return None
        finally:
            if driver:
                try:
                    # 強制清理瀏覽器資源
                    driver.quit()
                    print("🧹 瀏覽器已關閉。")
                except Exception as cleanup_error:
                    print(f"⚠️ 瀏覽器清理時發生錯誤: {cleanup_error}")
                    
                # 額外清理：強制垃圾回收
                import gc
                gc.collect()
                
                # 記憶體清理後檢查
                try:
                    import psutil
                    process = psutil.Process()
                    memory_after = process.memory_info().rss / 1024 / 1024  # MB
                    print(f"💾 清理後記憶體: {memory_after:.1f} MB")
                except ImportError:
                    pass
    
    def process_news_for_subscriptions(self) -> bool:
        """
        主執行函式 - 處理所有訂閱的新聞（批量版本）
        根據新的推送頻率和批量處理需求優化
        """
        print("🚀 開始執行智能新聞處理任務...")
        
        # 獲取符合推送條件的訂閱
        eligible_subscriptions = db_manager.get_eligible_subscriptions()
        if not eligible_subscriptions:
            print("🟡 目前沒有符合推送時間的訂閱任務，程式結束。")
            return False

        # 爬取新聞列表
        news_list = self.scrape_yahoo_finance_list()
        if not news_list:
            print("🟡 未能從 Yahoo Finance 爬取到任何新聞，程式結束。")
            return False

        # 處理每個符合條件的訂閱
        overall_success = False
        for subscription in eligible_subscriptions:
            print(f"\n--- ⚙️ 開始處理使用者 {subscription['user_id']} 的訂閱 ---")
            success = self._process_subscription_batch(subscription, news_list)
            if success:
                overall_success = True

        print(f"\n✅ 所有符合條件的訂閱任務處理完畢。")
        return overall_success
    
    def _process_subscription_batch(self, subscription: Dict[str, Any], news_list: List[Dict[str, str]]) -> bool:
        """處理單一訂閱任務 - 批量收集和推送版本"""
        user_id = subscription['user_id']
        frequency_type = subscription.get('push_frequency_type', 'daily')
        keywords = subscription.get("keywords", [])
        max_articles = db_manager.get_max_articles_for_frequency(frequency_type)
        
        print(f"🔍 為用戶 {user_id} 收集符合條件的新聞 (最多 {max_articles} 則)")
        
        # 收集符合條件的新聞
        collected_articles = []
        processed_count = 0
        failed_count = 0
        
        for news_item in news_list:
            # 檢查是否已達到最大數量
            if len(collected_articles) >= max_articles:
                print(f"📊 已收集到 {max_articles} 則新聞，停止收集")
                break
            
            # 檢查是否已處理
            if db_manager.is_article_processed(news_item['link']):
                continue
            
            # 檢查關鍵字匹配
            if keywords and not any(keyword.lower() in news_item['title'].lower() for keyword in keywords):
                continue
            
            print(f"👉 找到符合關鍵字的文章: {news_item['title'][:60]}...")
            processed_count += 1
            
            # 嘗試處理文章
            article_data = self._process_single_article(news_item)
            if article_data:
                collected_articles.append(article_data)
                print(f"✅ 文章處理成功 ({len(collected_articles)}/{max_articles})")
            else:
                failed_count += 1
                print(f"❌ 文章處理失敗")
                
            # 如果已收集足夠的文章，提前結束
            if len(collected_articles) >= max_articles:
                break
        
        # 推送結果統計
        print(f"\n📊 收集結果統計:")
        print(f"  - 嘗試處理: {processed_count} 篇")
        print(f"  - 成功收集: {len(collected_articles)} 篇")
        print(f"  - 處理失敗: {failed_count} 篇")
        
        if not collected_articles:
            print(f"ℹ️ 未找到適合用戶 {user_id} 的新文章")
            return False
        
        # 批量推送到 Discord
        print(f"\n📤 開始推送 {len(collected_articles)} 則新聞到 Discord...")
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
                    print(f"📝 已記錄推送歷史: {len(article_ids)} 篇文章")
                
                # 標記推送窗口為已完成
                db_manager.mark_push_window_completed(user_id, frequency_type)
                
                # 發送推送總結消息
                create_push_summary_message(
                    subscription['delivery_target'],
                    len(successful_articles),
                    len(collected_articles),
                    frequency_type
                )
                
                print(f"🎉 用戶 {user_id} 的推送任務完成: {len(successful_articles)} 則成功")
                return True
        
        print(f"❌ 用戶 {user_id} 的推送任務失敗")
        return False
    
    def _process_single_article(self, news_item: Dict[str, str]) -> Union[Dict[str, Any], None]:
        """處理單篇文章 - 爬取內容並生成摘要"""
        try:
            # 抓取內容
            content = self.scrape_article_content(news_item['link'])
            if not content:
                return None

            # 生成摘要
            summary = generate_summary_optimized(content)
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
                'published_at': published_at.isoformat()  # 轉換為 ISO 格式字符串
            }
            
            return article_data
            
        except Exception as e:
            print(f"❌ 處理文章時發生錯誤: {e}")
            return None

# Create a global scraper manager instance
scraper_manager = NewsScraperManager() 