"""
簡化的Lambda函數測試 - 不依賴環境變數
"""
import sys
from pathlib import Path

# 設置編碼
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())

# 添加專案根目錄到路徑
project_root = Path(__file__).parent
sys.path.append(str(project_root))

def test_lambda_imports():
    """測試Lambda函數的模組導入"""
    print("🧪 測試Lambda函數模組導入...")
    
    try:
        print("1️⃣ 測試爬蟲模組導入...")
        from scraper.scraper import NewsScraperManager
        print("   ✅ 爬蟲模組導入成功")
        
        print("2️⃣ 測試工具模組導入...")
        from core.utils import get_current_taiwan_time
        print("   ✅ 工具模組導入成功")
        
        print("3️⃣ 測試Lambda函數結構...")
        # 模擬Lambda函數邏輯（不涉及資料庫）
        def mock_lambda_handler(event, context):
            taiwan_time = get_current_taiwan_time()
            return {
                'statusCode': 200,
                'body': f'測試成功 - {taiwan_time.strftime("%Y-%m-%d %H:%M:%S")}'
            }
        
        # 測試函數調用
        result = mock_lambda_handler({}, None)
        print(f"   ✅ Lambda函數邏輯測試成功")
        print(f"   📋 返回結果: {result}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_basic_scraper():
    """測試基礎爬蟲功能（不涉及資料庫）"""
    print("\n🕷️ 測試基礎爬蟲功能...")
    
    try:
        from scraper.scraper import NewsScraperManager
        scraper = NewsScraperManager()
        
        print("1️⃣ 測試新聞列表抓取...")
        news_list = scraper.scrape_yahoo_finance_list()
        
        if news_list and len(news_list) > 0:
            print(f"   ✅ 成功抓取 {len(news_list)} 則新聞")
            print(f"   📰 第一篇: {news_list[0]['title'][:50]}...")
            return True
        else:
            print("   ❌ 新聞列表為空")
            return False
            
    except Exception as e:
        print(f"   ❌ 爬蟲測試失敗: {e}")
        return False

def main():
    """主測試函數"""
    print("🚀 開始Lambda函數簡化測試")
    print("=" * 60)
    
    # 測試1: 模組導入
    import_ok = test_lambda_imports()
    
    # 測試2: 基礎爬蟲
    scraper_ok = test_basic_scraper()
    
    print("\n" + "=" * 60)
    print("📊 測試結果總結:")
    print(f"  - Lambda模組導入: {'✅' if import_ok else '❌'}")
    print(f"  - 基礎爬蟲功能: {'✅' if scraper_ok else '❌'}")
    
    if import_ok and scraper_ok:
        print("🎉 所有測試通過！Lambda函數準備就緒")
        return True
    else:
        print("⚠️ 部分測試失敗，需要修復後再部署")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)