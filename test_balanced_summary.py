#!/usr/bin/env python3
"""
測試新的平衡語言摘要策略
"""

import sys
from pathlib import Path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from scraper.scraper import NewsScraperManager
from core.summary_quality_monitor import validate_mixed_language_summary, ALLOWED_ENGLISH_TERMS

def test_mixed_language_validation():
    """測試混合語言驗證功能"""
    print("Testing mixed language validation...")
    
    test_cases = [
        # 理想案例：主要中文 + 合理英文術語
        ("Apple公司第三季度財報顯示GDP相關指標上升，CEO表示對AI技術發展樂觀。", True, "理想混合"),
        
        # 可接受案例：包含專業術語
        ("TSMC台積電營收創新高，受惠於5G和IoT市場需求強勁，股價上漲3%。", True, "專業術語適中"),
        
        # 不佳案例：包含語法性英文詞彙  
        ("蘋果公司 and 微軟公司 are leading the market with strong performance.", False, "語法性英文過多"),
        
        # 不佳案例：中文比例過低
        ("Apple, Microsoft, Google and Tesla are the leading tech companies in the market.", False, "中文比例不足"),
        
        # 邊界案例：剛好符合標準
        ("Tesla電動車銷量創新高，受惠於EV市場擴張和政府ESG政策支持，市佔率持續提升。", True, "邊界合格案例"),
        
        # 不合格案例：純英文
        ("The company reported strong earnings with significant revenue growth.", False, "純英文"),
        
        # 合格案例：純中文
        ("蘋果公司第三季度財報表現亮眼，營收創下歷史新高，獲利能力持續提升。", True, "純中文")
    ]
    
    print(f"Testing {len(test_cases)} cases:")
    print("-" * 80)
    
    passed = 0
    for i, (text, expected_valid, description) in enumerate(test_cases, 1):
        is_valid, chinese_ratio, has_forbidden, analysis = validate_mixed_language_summary(text)
        
        result = "✓ PASS" if (is_valid == expected_valid) else "✗ FAIL"
        if is_valid != expected_valid:
            print(f"{i}. {result} - {description}")
            print(f"   Text: {text[:60]}...")
            print(f"   Expected: {expected_valid}, Got: {is_valid}")
            print(f"   Chinese ratio: {chinese_ratio:.1%}")
            print(f"   Forbidden words: {analysis.get('forbidden_words', [])}")
            print(f"   Allowed words: {analysis.get('allowed_words', [])}")
            print()
        else:
            passed += 1
            print(f"{i}. {result} - {description} (Chinese: {chinese_ratio:.1%})")
    
    print("-" * 80)
    print(f"Test Results: {passed}/{len(test_cases)} passed")
    return passed == len(test_cases)

def test_whitelist_coverage():
    """測試白名單覆蓋範圍"""
    print("\nTesting whitelist coverage...")
    
    # 測試各類別的術語
    company_terms = ['Apple', 'Tesla', 'TSMC', 'Microsoft']
    finance_terms = ['GDP', 'IPO', 'CEO', 'AI', 'ESG'] 
    tech_terms = ['5G', 'IoT', 'API', 'EV']
    
    all_allowed = set()
    for category in ALLOWED_ENGLISH_TERMS.values():
        all_allowed.update(term.lower() for term in category)
    
    print(f"Total allowed terms: {len(all_allowed)}")
    print("Sample terms by category:")
    print(f"  Companies: {company_terms}")
    print(f"  Finance: {finance_terms}")
    print(f"  Tech: {tech_terms}")
    
    # 檢查覆蓋率
    test_terms = company_terms + finance_terms + tech_terms
    covered = sum(1 for term in test_terms if term.lower() in all_allowed)
    coverage = covered / len(test_terms)
    
    print(f"Coverage: {covered}/{len(test_terms)} ({coverage:.1%})")
    
    return coverage >= 0.8  # 期望80%以上覆蓋率

def test_scraper_integration():
    """測試爬蟲集成"""
    print("\nTesting scraper integration...")
    
    scraper = NewsScraperManager()
    
    # 測試驗證函數
    test_summary = "Apple公司第三季度財報顯示，受惠於iPhone銷量增長和服務業務擴張，營收達到新高。"
    is_valid, quality_score, chinese_ratio, has_forbidden, analysis = scraper._validate_chinese_summary(test_summary)
    
    print(f"Test summary: {test_summary}")
    print(f"Validation result:")
    print(f"  Valid: {is_valid}")
    print(f"  Quality score: {quality_score:.2f}")
    print(f"  Chinese ratio: {chinese_ratio:.1%}")
    print(f"  Has forbidden words: {has_forbidden}")
    print(f"  Allowed words: {analysis.get('allowed_words', [])}")
    
    expected_valid = True  # 這個摘要應該是合格的
    return is_valid == expected_valid

def main():
    """主測試函數"""
    print("="*60)
    print("🧪 Testing Balanced Summary Language Strategy")
    print("="*60)
    
    tests = [
        ("Mixed Language Validation", test_mixed_language_validation),
        ("Whitelist Coverage", test_whitelist_coverage),
        ("Scraper Integration", test_scraper_integration),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            print(f"\n--- {test_name} ---")
            if test_func():
                print(f"✅ {test_name} PASSED")
                passed += 1
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"❌ {test_name} ERROR: {e}")
    
    print("\n" + "="*60)
    print(f"📊 Test Summary: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All tests passed! Balanced language strategy is working correctly.")
        print("\n🚀 Key improvements:")
        print("  - Mixed language validation with smart filtering")
        print("  - Professional term whitelist (companies, finance, tech)")
        print("  - Forbidden grammatical words detection")
        print("  - Flexible Chinese ratio requirement (≥70%)")
        print("  - Quality scoring with professional term bonus")
    else:
        print("⚠️ Some tests failed. Please check the implementation.")
    
    print("="*60)
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)