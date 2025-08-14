#!/usr/bin/env python3
"""
Simple test for balanced summary strategy
"""

import sys
from pathlib import Path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from scraper.scraper import NewsScraperManager
from core.summary_quality_monitor import validate_mixed_language_summary

def main():
    print("Testing Balanced Summary Language Strategy")
    print("=" * 50)
    
    # Test cases
    test_cases = [
        ("Apple公司Q3財報顯示GDP相關指標上升，CEO對AI發展樂觀。", True, "Mixed with tech terms"),
        ("TSMC營收創新高，受惠於5G和IoT需求，股價上漲3%。", True, "Professional terms"),
        ("蘋果公司 and 微軟 are leading the market.", False, "Too much English grammar"),
        ("純中文摘要測試，營收創歷史新高，表現優異。", True, "Pure Chinese"),
    ]
    
    print("Testing validation function:")
    passed = 0
    
    for i, (text, expected, desc) in enumerate(test_cases, 1):
        is_valid, ratio, has_forbidden, analysis = validate_mixed_language_summary(text)
        result = "PASS" if (is_valid == expected) else "FAIL"
        
        print(f"{i}. {result} - {desc}")
        print(f"   Valid: {is_valid}, Chinese: {ratio:.1%}")
        print(f"   Allowed: {analysis.get('allowed_words', [])}")
        print(f"   Forbidden: {analysis.get('forbidden_words', [])}")
        
        if is_valid == expected:
            passed += 1
        print()
    
    # Test scraper integration
    print("Testing scraper integration:")
    scraper = NewsScraperManager()
    
    test_summary = "Apple公司Q3財報顯示營收創新高，受惠於iPhone和AI服務成長。"
    is_valid, quality, ratio, forbidden, analysis = scraper._validate_chinese_summary(test_summary)
    
    print(f"Test summary: {test_summary}")
    print(f"Valid: {is_valid}, Quality: {quality:.2f}, Chinese: {ratio:.1%}")
    print(f"Professional terms used: {analysis.get('allowed_words', [])}")
    
    if is_valid:
        passed += 1
    
    total_tests = len(test_cases) + 1
    print(f"\nResults: {passed}/{total_tests} tests passed")
    
    if passed == total_tests:
        print("SUCCESS: Balanced language strategy working correctly!")
        print("Key features:")
        print("- Mixed Chinese/English validation")
        print("- Professional term whitelist")
        print("- Grammatical word filtering")
        print("- Quality scoring system")
    else:
        print("Some tests failed - check implementation")
    
    return passed == total_tests

if __name__ == "__main__":
    success = main()
    print(f"\nTest completed: {'PASSED' if success else 'FAILED'}")
    sys.exit(0 if success else 1)