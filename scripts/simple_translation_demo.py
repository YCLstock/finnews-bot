#!/usr/bin/env python3
"""
簡化版翻譯功能演示
避免編碼問題，專注展示功能
"""

import os
import sys

# 添加項目根目錄到路徑
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.translation_service import get_translation_service
from core.config import settings

def simple_demo():
    """簡單演示翻譯功能"""
    print("翻譯功能演示")
    print("=" * 50)
    
    # 檢查API設置
    if not settings.OPENAI_API_KEY:
        print("警告: 未找到 OpenAI API Key")
        print("將使用模擬演示")
        return
    
    service = get_translation_service()
    
    # 測試標題
    test_titles = [
        "Apple reports record quarterly revenue",
        "Tesla stock price surges on delivery news", 
        "Microsoft announces new AI features",
        "蘋果公司發布財報",  # 已是中文
        "Tesla 股價上漲"  # 中英混合
    ]
    
    print("\n測試中文檢測功能:")
    for title in test_titles:
        is_chinese = service._is_already_chinese(title)
        status = "已是中文" if is_chinese else "需要翻譯"
        print(f"'{title}' -> {status}")
    
    print("\n快取功能測試:")
    service.clear_cache()
    cache_info = service.get_cache_info()
    print(f"快取狀態: 命中={cache_info['hits']}, 未命中={cache_info['misses']}")
    
    print("\n翻譯功能準備就緒!")
    print("Phase 2 完成，等待資料庫欄位新增後可進行 Phase 3")

if __name__ == "__main__":
    simple_demo()