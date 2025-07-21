#!/usr/bin/env python3
"""
Simple test for keyword sync functionality
"""
import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from services.keyword_sync_service import keyword_sync_service

def test_keyword_conversion():
    """Test keyword conversion functionality"""
    print("Testing keyword conversion...")
    
    test_keywords = ["Apple", "TSMC", "AI", "Tesla"]
    
    try:
        result = keyword_sync_service.convert_keywords_to_tags(test_keywords)
        print(f"Input keywords: {test_keywords}")
        print(f"Output tags: {result}")
        return True
    except Exception as e:
        print(f"Test failed: {e}")
        return False

def test_database_connection():
    """Test database connection"""
    print("Testing database connection...")
    
    try:
        from core.database import db_manager
        subscriptions = db_manager.get_active_subscriptions()
        print(f"Found {len(subscriptions)} active subscriptions")
        return True
    except Exception as e:
        print(f"Database test failed: {e}")
        return False

def main():
    print("Keyword Sync Test Suite")
    print("=" * 40)
    
    tests = [
        ("Database Connection", test_database_connection),
        ("Keyword Conversion", test_keyword_conversion),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\nRunning: {test_name}")
        if test_func():
            print(f"PASS: {test_name}")
            passed += 1
        else:
            print(f"FAIL: {test_name}")
    
    print(f"\nResults: {passed}/{total} tests passed")
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)