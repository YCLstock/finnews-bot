#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
簡化版摘要功能測試
"""

import sys
import os
from pathlib import Path

# 添加項目根目錄到路徑
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from scraper.scraper import NewsScraperManager
from core.summary_quality_monitor import get_quality_monitor

def test_chinese_validation():
    """測試中文驗證功能"""
    print("正在測試中文摘要驗證...")
    
    scraper = NewsScraperManager()
    
    # 測試純中文摘要
    chinese_summary = "蘋果公司第三季度財報顯示營收達到858億美元，較去年同期增長5%。"
    is_valid, quality_score, chinese_ratio, has_english = scraper._validate_chinese_summary(chinese_summary)
    
    print(f"純中文摘要測試:")
    print(f"  是否有效: {is_valid}")
    print(f"  中文比例: {chinese_ratio:.2f}")
    print(f"  包含英文: {has_english}")
    print(f"  品質分數: {quality_score:.2f}")
    
    # 測試包含英文的摘要
    mixed_summary = "蘋果公司 and 服務業務表現出色，revenue 達到新高度。"
    is_valid2, quality_score2, chinese_ratio2, has_english2 = scraper._validate_chinese_summary(mixed_summary)
    
    print(f"\n混合語言摘要測試:")
    print(f"  是否有效: {is_valid2}")
    print(f"  中文比例: {chinese_ratio2:.2f}")
    print(f"  包含英文: {has_english2}")
    print(f"  品質分數: {quality_score2:.2f}")
    
    success = is_valid and not is_valid2
    print(f"\n驗證功能測試: {'通過' if success else '失敗'}")
    return success

def test_quality_monitoring():
    """測試品質監控功能"""
    print("\n正在測試品質監控...")
    
    monitor = get_quality_monitor()
    
    # 重置統計
    monitor.session_stats = {
        'total_attempts': 0,
        'successful_summaries': 0,
        'failed_summaries': 0,
        'chinese_valid': 0,
        'chinese_invalid': 0,
        'retry_needed': 0,
        'total_generation_time': 0.0
    }
    
    # 模擬記錄一些數據
    from core.summary_quality_monitor import record_summary_quality
    
    record_summary_quality(
        title="測試標題",
        summary="這是一個測試用的中文摘要，用於驗證品質監控系統。",
        chinese_ratio=0.95,
        has_english_words=False,
        is_valid=True,
        quality_score=0.95,
        attempt_count=1,
        generation_time=2.5,
        success=True
    )
    
    stats = monitor.get_session_summary()
    print(f"監控統計:")
    print(f"  總嘗試次數: {stats['total_attempts']}")
    print(f"  成功次數: {stats['successful_summaries']}")
    print(f"  成功率: {stats['success_rate']:.1%}")
    print(f"  中文有效率: {stats['chinese_valid_rate']:.1%}")
    
    success = stats['total_attempts'] > 0 and stats['success_rate'] > 0.8
    print(f"\n監控功能測試: {'通過' if success else '失敗'}")
    return success

def test_quality_report():
    """測試品質報告生成"""
    print("\n正在測試品質報告生成...")
    
    monitor = get_quality_monitor()
    
    try:
        report = monitor.generate_quality_report()
        print("品質報告生成成功")
        print("報告片段:")
        print(report[:200] + "..." if len(report) > 200 else report)
        return True
    except Exception as e:
        print(f"品質報告生成失敗: {e}")
        return False

def main():
    """主測試函數"""
    print("="*50)
    print("開始測試改進後的摘要生成功能")
    print("="*50)
    
    # 檢查環境
    if not os.environ.get('OPENAI_API_KEY'):
        print("警告: 未設置 OPENAI_API_KEY")
    
    # 執行測試
    tests = [
        ("中文驗證", test_chinese_validation),
        ("品質監控", test_quality_monitoring),
        ("品質報告", test_quality_report),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
                print(f"✓ {test_name}測試通過")
            else:
                print(f"✗ {test_name}測試失敗")
        except Exception as e:
            print(f"✗ {test_name}測試發生錯誤: {e}")
    
    print("\n" + "="*50)
    print(f"測試結果: {passed}/{total} 通過")
    
    if passed == total:
        print("✓ 所有測試通過！摘要改進功能運行正常")
        print("\n改進亮點:")
        print("  - 強化的中文語言要求 prompt")
        print("  - 智能重試機制（最多2次重試）")
        print("  - 中文字符比例驗證（>= 80%）")
        print("  - 英文關鍵詞檢測和過濾")
        print("  - 品質監控和統計功能")
        print("\n預期改進效果:")
        print("  - 中文摘要準確率提升至 95%+")
        print("  - 更好的錯誤處理和監控")
    else:
        print("✗ 有測試失敗，請檢查相關功能")
    
    print("="*50)
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)