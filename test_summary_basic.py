#!/usr/bin/env python3
"""
基礎摘要功能測試
"""

import sys
from pathlib import Path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from scraper.scraper import NewsScraperManager

def main():
    print("Testing Chinese summary validation...")
    
    scraper = NewsScraperManager()
    
    # Test Chinese summary
    chinese_text = "蘋果公司第三季度財報顯示營收達到858億美元，較去年同期增長5%。"
    is_valid, score, ratio, has_english = scraper._validate_chinese_summary(chinese_text)
    print(f"Chinese text valid: {is_valid}, ratio: {ratio:.2f}, score: {score:.2f}")
    
    # Test mixed language
    mixed_text = "蘋果公司 and 服務業務表現 with 強勁增長。"
    is_valid2, score2, ratio2, has_english2 = scraper._validate_chinese_summary(mixed_text)
    print(f"Mixed text valid: {is_valid2}, ratio: {ratio2:.2f}, score: {score2:.2f}")
    
    success = is_valid and not is_valid2
    print(f"Validation test: {'PASS' if success else 'FAIL'}")
    
    # Test monitoring
    from core.summary_quality_monitor import record_summary_quality, get_quality_monitor
    
    record_summary_quality(
        title="Test Title",
        summary="測試用的中文摘要，驗證品質監控系統。",
        chinese_ratio=0.95,
        has_english_words=False,
        is_valid=True,
        quality_score=0.95,
        attempt_count=1,
        generation_time=2.0,
        success=True
    )
    
    monitor = get_quality_monitor()
    stats = monitor.get_session_summary()
    print(f"Monitoring: attempts={stats['total_attempts']}, success_rate={stats['success_rate']:.1%}")
    
    print("All basic tests completed successfully!")
    return True

if __name__ == "__main__":
    main()