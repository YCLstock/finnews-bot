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
        chrome_options = Options()
        
        # 強化偽裝與穩定性的選項
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("window-size=1920x1080")
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument('--ignore-ssl-errors')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36")

        driver = None
        try:
            # 強制重新下載最新版ChromeDriver
            from webdriver_manager.chrome import ChromeDriverManager
            import os
            import shutil
            
            # 清除舊的driver緩存
            cache_path = os.path.expanduser("~/.wdm")
            if os.path.exists(cache_path):
                try:
                    shutil.rmtree(cache_path)
                    print("🧹 已清除舊版ChromeDriver緩存")
                except:
                    pass
            
            driver_path = ChromeDriverManager().install()
            service = Service(driver_path)
            driver = webdriver.Chrome(service=service, options=chrome_options)
            
            driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                'source': "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            })
            
            driver.set_page_load_timeout(settings.SCRAPER_TIMEOUT)
            
            print("正在訪問頁面...")
            driver.get(url)

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
                driver.quit()
                print("🧹 瀏覽器已關閉。")
    
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