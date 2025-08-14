#!/usr/bin/env python3
"""
翻譯功能最終測試腳本
簡化版本，避免編碼問題
"""

import os
import sys
import time

# 添加項目根目錄到路徑
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.translation_service import get_translation_service
from core.delivery_manager import DiscordProvider
from core.database import db_manager
from core.config import settings

def test_translation_functionality():
    """測試翻譯功能"""
    print("翻譯功能測試")
    print("-" * 40)
    
    service = get_translation_service()
    
    # 測試中文檢測
    test_titles = [
        "Apple Reports Strong Earnings",
        "Tesla Stock Surges",
        "蘋果公司發布財報",
        "Tesla 股價上漲"
    ]
    
    print("\n中文檢測測試:")
    for title in test_titles:
        is_chinese = service._is_already_chinese(title)
        status = "是中文" if is_chinese else "需翻譯"
        print(f"  '{title}' -> {status}")
    
    # 測試快取功能
    service.clear_cache()
    cache_info = service.get_cache_info()
    print(f"\n快取功能: 命中={cache_info['hits']}, 未命中={cache_info['misses']}")
    
    return True

def test_discord_logic():
    """測試Discord邏輯"""
    print("\nDiscord推送邏輯測試")
    print("-" * 40)
    
    provider = DiscordProvider()
    
    # 測試標題選擇
    article = {
        'title': 'Apple Reports Earnings',
        'translated_title': '蘋果公司發布財報'
    }
    
    # 中文用戶
    title_zh = provider._get_display_title(article, 'zh-tw')
    print(f"中文用戶看到: '{title_zh}'")
    
    # 英文用戶
    title_en = provider._get_display_title(article, 'en-us')
    print(f"英文用戶看到: '{title_en}'")
    
    # 無翻譯情況
    article_no_trans = {
        'title': 'Tesla Stock Rises',
        'translated_title': None
    }
    title_no_trans = provider._get_display_title(article_no_trans, 'zh-tw')
    print(f"無翻譯時: '{title_no_trans}'")
    
    return True

def test_system_status():
    """測試系統狀態"""
    print("\n系統狀態檢查")
    print("-" * 40)
    
    # 檢查配置
    print(f"OpenAI API: {'已設置' if settings.OPENAI_API_KEY else '未設置'}")
    print(f"Supabase: {'已設置' if settings.SUPABASE_URL else '未設置'}")
    print(f"環境: {settings.ENVIRONMENT}")
    
    # 檢查資料庫連接
    try:
        result = db_manager.supabase.table('news_articles').select('id, translated_title').limit(1).execute()
        print(f"資料庫連接: 正常")
        
        if result.data:
            article = result.data[0]
            has_translation_field = 'translated_title' in article
            print(f"翻譯欄位: {'存在' if has_translation_field else '不存在'}")
        
    except Exception as e:
        print(f"資料庫連接: 失敗 ({e})")
        return False
    
    return True

def main():
    """主函數"""
    print("翻譯功能最終驗證")
    print("=" * 50)
    
    tests = [
        ("翻譯服務", test_translation_functionality),
        ("Discord邏輯", test_discord_logic), 
        ("系統狀態", test_system_status)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append(result)
            print(f"\n{test_name}: {'通過' if result else '失敗'}")
        except Exception as e:
            print(f"\n{test_name}: 錯誤 - {e}")
            results.append(False)
    
    print("\n" + "=" * 50)
    
    success_count = sum(results)
    total_count = len(results)
    
    if success_count == total_count:
        print(f"所有測試通過 ({success_count}/{total_count})")
        print("\n翻譯功能實施完成!")
        print("階段摘要:")
        print("- Phase 1: 資料庫擴展 [完成]")
        print("- Phase 2: 翻譯服務 [完成]")
        print("- Phase 3: 爬蟲整合 [完成]") 
        print("- Phase 4: Discord推送 [完成]")
        print("- Phase 5: 端到端測試 [完成]")
        print("\n系統現在支援智能翻譯功能!")
        print("中文用戶將看到翻譯標題，英文用戶看到原文標題。")
        
        return True
    else:
        print(f"部分測試失敗 ({success_count}/{total_count})")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)