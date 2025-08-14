#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Final validation test for balanced summary strategy
"""

import sys
from pathlib import Path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from core.summary_quality_monitor import validate_mixed_language_summary

def main():
    print("Final Validation Test")
    print("=" * 40)
    
    # Test the validation logic
    print("1. Testing English text with allowed terms:")
    text1 = "Apple CEO reports AI growth"
    valid1, ratio1, forbidden1, analysis1 = validate_mixed_language_summary(text1)
    print(f"   Text: {text1}")
    print(f"   Valid: {valid1}, Ratio: {ratio1:.1%}")
    print(f"   Allowed: {analysis1.get('allowed_words', [])}")
    print(f"   Forbidden: {analysis1.get('forbidden_words', [])}")
    
    print("\n2. Testing English text with forbidden words:")
    text2 = "The company and its CEO are optimistic"
    valid2, ratio2, forbidden2, analysis2 = validate_mixed_language_summary(text2)
    print(f"   Text: {text2}")
    print(f"   Valid: {valid2}, Ratio: {ratio2:.1%}")
    print(f"   Forbidden: {analysis2.get('forbidden_words', [])}")
    
    print("\n3. Testing Chinese text (should pass):")
    # Using simple characters to avoid encoding issues
    text3 = "公司第三季度财报表现优秀营收创新高"  # Simplified Chinese
    valid3, ratio3, forbidden3, analysis3 = validate_mixed_language_summary(text3)
    print(f"   Text: {text3}")
    print(f"   Valid: {valid3}, Ratio: {ratio3:.1%}")
    
    print("\n4. Testing mixed text (ideal case):")
    text4 = "Apple财报显示GDP增长CEO对AI乐观"  # Mixed
    valid4, ratio4, forbidden4, analysis4 = validate_mixed_language_summary(text4)
    print(f"   Text: {text4}")
    print(f"   Valid: {valid4}, Ratio: {ratio4:.1%}")
    print(f"   Allowed: {analysis4.get('allowed_words', [])}")
    
    # Summary
    tests = [
        (valid1, False, "English with allowed terms should fail (low Chinese ratio)"),
        (valid2, False, "English with forbidden words should fail"),
        (valid3, True, "Pure Chinese should pass"),
        (valid4, True, "Mixed with good Chinese ratio should pass"),
    ]
    
    print("\n" + "=" * 40)
    print("Test Results:")
    passed = 0
    for i, (result, expected, desc) in enumerate(tests, 1):
        status = "PASS" if result == expected else "FAIL"
        print(f"{i}. {status} - {desc}")
        if result == expected:
            passed += 1
    
    print(f"\nOverall: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("\nSUCCESS: Validation logic working correctly!")
        print("Features confirmed:")
        print("- Professional term whitelist recognition")
        print("- Forbidden word detection")
        print("- Chinese ratio calculation")
        print("- Mixed language validation")
    else:
        print("\nSome issues found - check implementation")
    
    return passed == len(tests)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)