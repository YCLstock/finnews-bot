# main_bot.py
import os
import random
import time
from pathlib import Path
from typing import Union
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from supabase import create_client, Client
import openai

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager

# --- 初始化 ---
print("🚀 開始執行客製化新聞 Bot (最終點擊版)...")
load_dotenv()

supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_SERVICE_KEY")
if not supabase_url or not supabase_key:
    print("❌ 錯誤：SUPABASE 環境變數未設置")
    exit()
supabase: Client = create_client(supabase_url, supabase_key)
print("✅ Supabase client 初始化成功！")

openai.api_key = os.environ.get("OPENAI_API_KEY")
if openai.api_key:
    print("✅ OpenAI API Key 讀取成功！")
else:
    print("⚠️ 警告：OPENAI_API_KEY 未設置，摘要功能將無法使用。")

# --- 核心功能 ---
def get_active_subscriptions():
    """從 Supabase 讀取所有活躍的訂閱任務"""
    try:
        data = supabase.table("subscriptions").select("*").eq("is_active", True).execute()
        print(f"🗂️ 從資料庫讀取到 {len(data.data)} 個活躍的訂閱任務。")
        return data.data
    except Exception as e:
        print(f"❌ 讀取訂閱任務錯誤: {e}")
        return []

def scrape_yahoo_finance_list(url: str) -> list:
    """使用 requests 爬取 Yahoo Finance 的新聞列表頁"""
    print(f"📰 正在從 {url} 爬取新聞列表...")
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36'}
    try:
        r = requests.get(url, headers=headers, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, 'html.parser')
        items = soup.select("li.stream-item")
        result = []
        seen_links = set()
        for i in items:
            a_tag = i.select_one('a[href*="/news/"]')
            title_tag = i.select_one('h3')
            if a_tag and title_tag:
                link = requests.compat.urljoin(url, a_tag['href'])
                if link not in seen_links:
                    seen_links.add(link)
                    result.append({'title': title_tag.get_text(strip=True), 'link': link})
        print(f"👍 成功爬取到 {len(result)} 則新聞標題。")
        return result
    except Exception as e:
        print(f"❌ 爬取新聞列表失敗: {e}")
        return []

def create_debug_folder():
    """創建一個用於存放除錯截圖的資料夾"""
    path = Path("debug_pages")
    path.mkdir(exist_ok=True)
    return path

def scrape_article_content(url: str) -> Union[str, None]:
    """
    【最終優化版】
    使用 Selenium 爬取單篇新聞的內文。
    - 強化偽裝以應對反爬蟲機制。
    - 使用複合選擇器以應對多種頁面版面。
    """
    print(f"  - 🦾 [Selenium] 正在啟動瀏覽器抓取完整 URL: {url}")
    chrome_options = Options()
    
    # --- 強化偽裝與穩定性的選項 ---
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
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        })
        
        driver.set_page_load_timeout(40)
        
        print("    - 正在訪問頁面...")
        driver.get(url)

        # --- 處理同意視窗 ---
        try:
            consent_button_locator = (By.CSS_SELECTOR, "button.consent-button[value='agree'], button[name='agree']")
            consent_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable(consent_button_locator)
            )
            print("    - 🍪 發現同意按鈕，正在點擊...")
            driver.execute_script("arguments[0].click();", consent_button)
            time.sleep(random.uniform(1, 2))
        except TimeoutException:
            print("    - 👍 未在10秒內發現或不需點擊同意按鈕，繼續執行。")

        # --- 等待並抓取主要內容 ---
        print("    - ⏳ 正在等待文章主要內容容器...")
        # 【關鍵修改】使用複合選擇器，應對多種已知的頁面版面
        content_container_locator = (By.CSS_SELECTOR, "div.caas-body, div.atoms-wrapper, div.article-wrap.no-bb")
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located(content_container_locator)
        )
        print("    - ✅ 內容容器已載入。")
        
        soup = BeautifulSoup(driver.page_source, "html.parser")
        
        # 【關鍵修改】再次使用複合選擇器進行解析
        body = soup.select_one("div.caas-body, div.atoms-wrapper, div.article-wrap.no-bb")

        if body:
            paragraphs = body.find_all("p")
            if not paragraphs:
                print(f"    - ⚠️ 找到容器 {body.get('class')}，但裡面沒有 <p> 標籤。")
                return None
            
            content_text = "\n".join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))
            
            if content_text:
                print(f"    - ✅ 成功擷取文章內文，約 {len(content_text)} 字。")
                return content_text
            else:
                print("    - ⚠️ 找到 <p> 標籤，但沒有有效文字內容。")
                return None
        
        print("    - ❌ 未能找到任何已知的內容容器 (caas-body, body, aoms-wrapper)。")
        return None

    except TimeoutException as e:
        print(f"    - ❌ 擷取內文時頁面加載或元素等待超時。錯誤訊息: {e.msg}")
        screenshot_path = create_debug_folder() / f"TIMEOUT_FAIL_{url.split('/')[-1].replace('.html', '')}.png"
        if driver: driver.save_screenshot(str(screenshot_path))
        print(f"    - 📸 錯誤畫面已截圖: {screenshot_path}")
        return None
    except Exception as e:
        print(f"    - ❌ 擷取內文時發生未預期錯誤: {e}")
        screenshot_path = create_debug_folder() / f"GENERAL_FAIL_{url.split('/')[-1].replace('.html', '')}.png"
        if driver: driver.save_screenshot(str(screenshot_path))
        print(f"    - 📸 錯誤畫面已截圖: {screenshot_path}")
        return None
    finally:
        if driver:
            driver.quit()
            print("    - 🧹 瀏覽器已關閉。")


def is_article_processed(url: str) -> bool:
    """檢查文章是否已經被處理並儲存過"""
    try:
        result = supabase.table('news_articles').select('id', count='exact').eq('original_url', url).execute()
        return result.count > 0
    except Exception as e:
        print(f"❌ 檢查文章是否重複錯誤: {e}")
        return True # 發生錯誤時，當作已處理以避免重複發送

import openai

def generate_summary_optimized(content: str) -> str:
    """使用 OpenAI API 生成金融新聞摘要 (優化版)"""
    print("    - 🧠 正在生成摘要 (使用 gpt-3.5-turbo)...")
    if not openai.api_key:
        return "[摘要生成失敗：API Key 未設定]"

    # 優化後的 Prompt，更具體地指導模型
    system_prompt = """
    你是一位專業的財經新聞編輯。你的任務是為以下文章生成一段專業、客觀且精簡的摘要。

    請遵循以下指示：
    1.  **風格**：語氣必須中立、客觀，專注於事實陳述，避免任何猜測或情緒性用語。
    2.  **核心要素**：摘要內容應涵蓋新聞的幾個關鍵要素：
        -   **事件主角**：涉及的主要公司、人物或機構。
        -   **核心事件**：發生了什麼關鍵決策、發布或變化。
        -   **關鍵數據**：提及任何重要的財務數據、百分比或市場指標。
        -   **市場影響**：簡述此事件對相關產業、股價或市場的潛在影響。
    3.  **格式要求**：
        -   使用繁體中文。
        -   摘要長度嚴格控制在 50 到 150 字之間。
        -   摘要應是一段完整的段落，語意連貫。
    4.  **目標讀者**：此摘要是為了讓沒有時間閱讀全文的投資人能快速掌握新聞重點。
    """

    try:
        response = openai.chat.completions.create(
            # 1. 模型更換為更具成本效益的 gpt-3.5-turbo
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": content}
            ],
            temperature=0.3,  # 對於摘要任務，較低的溫度可以讓輸出更穩定、更專注於事實
            max_tokens=600  # 稍微增加 token 限制以確保摘要能完整生成
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"    - ❌ 摘要失敗: {e}")
        return "[摘要生成失敗]"

def save_new_article(data: dict) -> Union[int, None]:
    """將新處理的文章儲存到 Supabase"""
    try:
        r = supabase.table("news_articles").insert(data).execute()
        print(f"  - ✅ 儲存成功: {data['title']}")
        return r.data[0]['id']
    except Exception as e:
        print(f"❌ 儲存新文章時錯誤: {e}")
        return None

def send_to_discord(webhook: str, articles: list, sub: dict):
    """將格式化後的新聞摘要發送到 Discord Webhook"""
    if not webhook.startswith("https://discord.com/api/webhooks/"):
        print(f"    - ❌ Webhook 不正確：{webhook}")
        return
    
    fields = [{
        "name": f"**{i+1}. {a['title']}**",
        "value": f"{a['summary']}\n[點此閱讀原文]({a['original_url']})",
        "inline": False
    } for i, a in enumerate(articles)]
    
    payload = {
        "embeds": [{
            "title": f"您訂閱的新聞",
            "color": 3447003, # Discord 藍色
            "fields": fields,
            "footer": {"text": f"發送時間: {time.strftime('%Y-%m-%d %H:%M:%S')}"}
        }]
    }
    try:
        r = requests.post(webhook, json=payload, timeout=10)
        r.raise_for_status()
        print("    - ✅ 成功推送到 Discord")
    except Exception as e:
        print(f"    - ❌ 推送失敗: {e}")

def log_push_history(user_id: str, article_ids: list):
    """記錄推送歷史到 Supabase"""
    records = [{"user_id": user_id, "article_id": i} for i in article_ids]
    try:
        supabase.table("push_history").insert(records).execute()
        print(f"    - 📝 已紀錄推播歷史 {len(article_ids)} 筆")
    except Exception as e:
        print(f"    - ❌ 紀錄推播歷史失敗: {e}")

# --- 主程式 ---
def main():
    """
    【最終優化版】
    主執行函式。
    - 修正了原先處理完一則新聞就退出的邏輯錯誤。
    """
    subscriptions = get_active_subscriptions()
    if not subscriptions:
        print("🟡 沒有任何活躍的訂閱任務，程式結束。")
        return

    news = scrape_yahoo_finance_list("https://finance.yahoo.com/topic/latest-news/")
    if not news:
        print("🟡 未能從 Yahoo Finance 爬取到任何新聞，程式結束。")
        return

    for sub in subscriptions:
        print(f"\n--- ⚙️ 開始處理使用者 {sub['user_id']} 的訂閱 ---")
        keywords = sub.get("keywords", [])
        found_news_for_this_user = False

        for item in news:
            if is_article_processed(item['link']):
                continue
            
            if not keywords or any(k.lower() in item['title'].lower() for k in keywords):
                print(f"  - 👉 找到符合關鍵字的文章，嘗試處理: {item['title']}")
                
                content = scrape_article_content(item['link'])
                if not content:
                    print("  - ❌ 內容獲取失敗，繼續尋找下一篇。")
                    continue

                summary = generate_summary_optimized(content)
                if "[摘要生成失敗" in summary:
                    print("  - ❌ 摘要生成失敗，繼續尋找下一篇。")
                    continue

                article = {'original_url': item['link'], 'source': 'yahoo_finance', 'title': item['title'], 'summary': summary}
                
                new_id = save_new_article(article)
                if new_id:
                    send_to_discord(sub['delivery_target'], [article], sub)
                    log_push_history(sub['user_id'], [new_id])
                    print(f"  - ✅ 成功為使用者 {sub['user_id']} 推送新聞。")
                    found_news_for_this_user = True
                    # 【關鍵修改】使用 break 跳出新聞迴圈，開始處理下一個使用者
                    break 
        
        if not found_news_for_this_user:
            print(f"  - ℹ️ 本輪未找到適合使用者 {sub['user_id']} 的新文章。")

    print("\n✅ 所有訂閱任務處理完畢。")


if __name__ == "__main__":
    main()