#!/usr/bin/env python3
"""
Test AI tagging functionality in scraper
"""
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from scraper.scraper import NewsScraperManager

def test_ai_tagging():
    """Test AI tagging with sample content"""
    print("Testing AI summary and tagging generation...")
    
    scraper = NewsScraperManager()
    
    # Sample financial news
    title = "Apple Reports Strong Q3 Earnings, iPhone Sales Beat Expectations"
    content = """
    Apple Inc. announced its financial results for the third quarter, 
    showing stronger than expected performance across all product categories.
    iPhone sales increased by 15% year-over-year, while services revenue 
    grew by 8%. The company's AI initiatives and new chip technology 
    contributed to the positive results. CEO Tim Cook highlighted 
    the company's focus on artificial intelligence and machine learning.
    """
    
    try:
        summary, tags = scraper.generate_summary_and_tags(title, content)
        
        print(f"Title: {title}")
        print(f"Summary: {summary}")
        print(f"Generated Tags: {tags}")
        
        # Check if we got reasonable results
        if len(summary) > 20 and isinstance(tags, list):
            print("SUCCESS: AI tagging working correctly")
            return True
        else:
            print("FAIL: Invalid results from AI tagging")
            return False
            
    except Exception as e:
        print(f"FAIL: AI tagging failed with error: {e}")
        return False

def test_fallback_tagging():
    """Test fallback tagging when AI is not available"""
    print("\nTesting fallback tagging...")
    
    scraper = NewsScraperManager()
    
    title = "Taiwan Semiconductor Manufacturing Company Reports Strong Quarter"
    content = "TSMC semiconductor wafer technology artificial intelligence chips"
    
    try:
        tags = scraper._generate_fallback_tags(title, content)
        print(f"Fallback tags: {tags}")
        
        if "TSMC" in tags or "AI_TECH" in tags:
            print("SUCCESS: Fallback tagging working")
            return True
        else:
            print("FAIL: Fallback tagging not working properly")
            return False
            
    except Exception as e:
        print(f"FAIL: Fallback tagging failed: {e}")
        return False

def main():
    print("AI Tagging Test Suite")
    print("=" * 40)
    
    tests = [
        test_ai_tagging,
        test_fallback_tagging,
    ]
    
    passed = 0
    for test in tests:
        if test():
            passed += 1
    
    print(f"\nResults: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("\nAll AI tagging tests PASSED!")
        return True
    else:
        print("\nSome tests FAILED")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)