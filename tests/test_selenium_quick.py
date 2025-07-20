#!/usr/bin/env python3
"""
快速測試Selenium ChromeDriver是否正常工作
用於診斷GitHub Actions環境問題
"""

import sys
import os
from pathlib import Path

# 添加項目根目錄到 Python 路徑
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_chrome_basic():
    """測試最基本的Chrome啟動"""
    print("🧪 測試基本Chrome啟動...")
    
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        
        # 最簡化的Chrome選項
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        
        print("1️⃣ 正在啟動Chrome...")
        
        # 使用Selenium內建管理
        driver = webdriver.Chrome(options=options)
        
        print("2️⃣ Chrome啟動成功！")
        
        # 測試基本導航
        print("3️⃣ 測試導航到Google...")
        driver.get("https://www.google.com")
        
        title = driver.title
        print(f"4️⃣ 頁面標題: {title}")
        
        # 清理
        driver.quit()
        print("5️⃣ 測試完成，Chrome已關閉")
        
        return True
        
    except Exception as e:
        print(f"❌ Chrome測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_yahoo_fetch():
    """測試Yahoo Finance基本抓取"""
    print("\n📰 測試Yahoo Finance連接...")
    
    try:
        import requests
        from bs4 import BeautifulSoup
        
        url = "https://finance.yahoo.com/topic/latest-news/"
        headers = {'User-Agent': 'Mozilla/5.0 (Linux; U; Android 4.2.2; he-il; NEO-X5-116A Build/JDQ39) AppleWebKit/534.30 (KHTML, like Gecko) Version/4.0 Mobile Safari/534.30'}
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        items = soup.select("li.stream-item")
        
        print(f"✅ 成功抓取到 {len(items)} 個新聞項目")
        
        if items:
            first_item = items[0]
            a_tag = first_item.select_one('a[href*="/news/"]')
            title_tag = first_item.select_one('h3')
            
            if a_tag and title_tag:
                print(f"📰 第一篇新聞: {title_tag.get_text(strip=True)[:50]}...")
                return True
        
        return False
        
    except Exception as e:
        print(f"❌ Yahoo Finance測試失敗: {e}")
        return False

def main():
    """主測試函數"""
    print("🚀 開始快速Selenium診斷測試")
    print("=" * 50)
    
    # 測試1: Chrome基本功能
    chrome_ok = test_chrome_basic()
    
    # 測試2: Yahoo Finance連接
    yahoo_ok = test_yahoo_fetch()
    
    print("\n" + "=" * 50)
    print(f"📊 測試結果:")
    print(f"  - Chrome啟動: {'✅' if chrome_ok else '❌'}")
    print(f"  - Yahoo連接: {'✅' if yahoo_ok else '❌'}")
    
    if chrome_ok and yahoo_ok:
        print("🎉 基礎功能正常，問題可能在複雜的爬蟲邏輯中")
    elif chrome_ok and not yahoo_ok:
        print("⚠️ Chrome正常但Yahoo連接有問題")
    elif not chrome_ok and yahoo_ok:
        print("⚠️ Selenium/Chrome有問題但網路正常")
    else:
        print("❌ 基礎環境有嚴重問題")

if __name__ == "__main__":
    main()