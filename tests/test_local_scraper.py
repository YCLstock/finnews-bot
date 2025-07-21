#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
本地測試Selenium爬蟲功能
用於快速調試和問題定位
"""

import sys
import os
from pathlib import Path

# 設置編碼
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())

# 添加項目根目錄到 Python 路徑
project_root = Path(__file__).parent.parent  # 回到專案根目錄
sys.path.insert(0, str(project_root))

def test_scraper_step_by_step():
    """逐步測試爬蟲功能"""
    print("🔧 開始逐步測試Selenium爬蟲...")
    
    try:
        # 步驟1: 導入模組
        print("1️⃣ 導入scraper模組...")
        from scraper.scraper import NewsScraperManager
        print("   ✅ 模組導入成功")
        
        # 步驟2: 創建scraper實例
        print("2️⃣ 創建NewsScraperManager實例...")
        scraper = NewsScraperManager()
        print("   ✅ 實例創建成功")
        
        # 步驟3: 測試新聞列表抓取
        print("3️⃣ 測試Yahoo Finance新聞列表抓取...")
        news_list = scraper.scrape_yahoo_finance_list()
        if news_list:
            print(f"   ✅ 成功抓取 {len(news_list)} 則新聞")
            print(f"   📰 第一篇: {news_list[0]['title'][:50]}...")
        else:
            print("   ❌ 新聞列表抓取失敗")
            return False
        
        # 步驟4: 測試單篇文章內容抓取
        print("4️⃣ 測試單篇文章內容抓取...")
        test_url = news_list[0]['link']
        print(f"   🔗 測試URL: {test_url}")
        
        content = scraper.scrape_article_content(test_url)
        if content:
            print(f"   ✅ 文章內容抓取成功 ({len(content)} 字)")
            print(f"   📄 內容預覽: {content[:100]}...")
            return True
        else:
            print("   ❌ 文章內容抓取失敗")
            return False
            
    except Exception as e:
        print(f"❌ 測試過程中發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_ai_summary():
    """測試AI摘要功能"""
    print("\n🤖 測試AI摘要功能...")
    
    try:
        from core.utils import generate_summary_optimized
        
        # 測試文本
        test_content = """
        Apple Inc. reported strong quarterly earnings today, with revenue exceeding expectations.
        The company's iPhone sales drove much of the growth, while services revenue also showed
        significant improvement. CEO Tim Cook expressed optimism about the company's future
        prospects, particularly in emerging markets and new product categories.
        """
        
        print("   📝 測試文本準備完成")
        print("   🤖 調用OpenAI API生成摘要...")
        
        summary = generate_summary_optimized(test_content)
        
        if summary and "[摘要生成失敗" not in summary:
            print(f"   ✅ AI摘要生成成功")
            print(f"   📄 摘要: {summary}")
            return True
        else:
            print(f"   ❌ AI摘要生成失敗: {summary}")
            return False
            
    except Exception as e:
        print(f"❌ AI摘要測試失敗: {e}")
        return False

def test_environment_variables():
    """測試環境變數"""
    print("\n🔑 檢查環境變數...")
    
    required_vars = [
        'OPENAI_API_KEY',
        'SUPABASE_URL', 
        'SUPABASE_SERVICE_KEY'
    ]
    
    missing_vars = []
    for var in required_vars:
        if os.environ.get(var):
            print(f"   ✅ {var}: 已設置")
        else:
            print(f"   ❌ {var}: 未設置")
            missing_vars.append(var)
    
    if missing_vars:
        print(f"   ⚠️ 缺少環境變數: {', '.join(missing_vars)}")
        print("   💡 請檢查.env文件或設置環境變數")
        return False
    else:
        print("   ✅ 所有必要環境變數已設置")
        return True

def main():
    """主測試函數"""
    print("🚀 開始本地Selenium爬蟲測試")
    print("=" * 60)
    
    # 測試環境變數
    env_ok = test_environment_variables()
    
    # 測試爬蟲功能
    scraper_ok = test_scraper_step_by_step()
    
    # 測試AI摘要（如果有API key）
    ai_ok = test_ai_summary() if env_ok else False
    
    print("\n" + "=" * 60)
    print("📊 本地測試結果:")
    print(f"  - 環境變數: {'✅' if env_ok else '❌'}")
    print(f"  - Selenium爬蟲: {'✅' if scraper_ok else '❌'}")
    print(f"  - AI摘要: {'✅' if ai_ok else '❌'}")
    
    if scraper_ok and ai_ok:
        print("🎉 所有功能正常！可以部署到GitHub Actions")
    elif scraper_ok and not ai_ok:
        print("⚠️ 爬蟲正常但AI功能有問題，檢查API key")
    elif not scraper_ok:
        print("❌ Selenium爬蟲有問題，需要修復")
    
    print("\n💡 建議:")
    if not scraper_ok:
        print("  - 檢查Chrome是否安裝")
        print("  - 檢查網路連接")
        print("  - 嘗試更新Selenium版本")
    if not ai_ok and env_ok:
        print("  - 檢查OpenAI API key是否有效")
        print("  - 檢查API配額是否用完")

if __name__ == "__main__":
    main()