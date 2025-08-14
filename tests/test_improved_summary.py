#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試改進後的摘要生成功能
驗證中文摘要品質、重試機制和監控功能
"""

import sys
import os
from pathlib import Path

# 添加項目根目錄到路徑
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

import unittest
from unittest.mock import patch, MagicMock
import json

from scraper.scraper import NewsScraperManager
from core.summary_quality_monitor import get_quality_monitor
from core.config import settings

class TestImprovedSummary(unittest.TestCase):
    """測試改進的摘要生成功能"""
    
    def setUp(self):
        """測試前準備"""
        self.scraper = NewsScraperManager()
        
        # 測試數據
        self.test_title = "Apple Inc. Reports Strong Q3 2024 Earnings with Record Revenue"
        self.test_content = """
        Apple Inc. (NASDAQ: AAPL) today announced financial results for its fiscal 2024 third quarter ended June 29, 2024. The company posted quarterly revenue of $85.8 billion, up 5% year over year, and quarterly earnings per diluted share of $1.40, up 11% year over year. Apple's services revenue reached $24.2 billion, setting a new all-time record.
        
        "We are very pleased with our Q3 results and the continued strength in our Services business," said Tim Cook, Apple's CEO. "Our teams continue to innovate and deliver products and services that enrich people's lives, and we remain committed to our long-term investments."
        
        iPhone revenue was $39.3 billion, down 1% year over year. Mac revenue was $7.0 billion, up 2% year over year. iPad revenue was $7.2 billion, down 2% year over year. Wearables, Home and Accessories revenue was $8.1 billion, down 2% year over year.
        """
    
    def test_chinese_summary_validation(self):
        """測試中文摘要驗證功能"""
        # 測試純中文摘要（應該通過）
        chinese_summary = "蘋果公司第三季度財報顯示營收達到858億美元，較去年同期增長5%，每股收益1.40美元，增長11%，服務業務創下歷史新高。"
        is_valid, quality_score, chinese_ratio, has_english = self.scraper._validate_chinese_summary(chinese_summary)
        
        self.assertTrue(is_valid, "純中文摘要應該通過驗證")
        self.assertGreaterEqual(chinese_ratio, 0.8, "中文字符比例應該>= 80%")
        self.assertFalse(has_english, "純中文摘要不應包含英文單詞")
        self.assertGreater(quality_score, 0.8, "品質分數應該較高")
        
        # 測試包含英文單詞的摘要（應該不通過）
        mixed_summary = "蘋果公司 and 服務業務表現出色，revenue 達到新高度 with 強勁的增長動力。"
        is_valid, quality_score, chinese_ratio, has_english = self.scraper._validate_chinese_summary(mixed_summary)
        
        self.assertFalse(is_valid, "包含英文單詞的摘要不應通過驗證")
        self.assertTrue(has_english, "應該檢測到英文單詞")
        self.assertLess(quality_score, 0.6, "品質分數應該較低")
        
        print("✅ 中文摘要驗證測試通過")
    
    @patch('scraper.scraper.requests.post')
    def test_summary_generation_success(self, mock_post):
        """測試摘要生成成功案例"""
        # Mock 成功的 API 回應
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'choices': [{
                'message': {
                    'content': json.dumps({
                        'summary': '蘋果公司公布2024年第三季度財報，營收858億美元，年增5%，每股收益1.40美元，年增11%。服務業務表現亮眼，創下242億美元的歷史新高紀錄。',
                        'tags': ['APPLE', 'EARNINGS', 'TECH'],
                        'confidence': 0.9
                    }, ensure_ascii=False)
                }
            }]
        }
        mock_post.return_value = mock_response
        
        # 測試摘要生成
        summary, tags = self.scraper.generate_summary_and_tags(self.test_title, self.test_content)
        
        self.assertIsInstance(summary, str)
        self.assertIsInstance(tags, list)
        self.assertNotIn("[摘要生成失敗", summary)
        self.assertGreater(len(summary), 50, "摘要長度應該合理")
        self.assertIn("蘋果", summary, "摘要應包含關鍵信息")
        
        # 檢查是否正確驗證為中文
        is_valid, _, chinese_ratio, has_english = self.scraper._validate_chinese_summary(summary)
        self.assertTrue(is_valid, "生成的摘要應該通過中文驗證")
        
        print("✅ 摘要生成成功測試通過")
        print(f"    摘要: {summary}")
        print(f"    標籤: {tags}")
    
    @patch('scraper.scraper.requests.post')
    def test_summary_retry_mechanism(self, mock_post):
        """測試摘要重試機制"""
        # Mock 第一次回應包含英文（需要重試）
        first_response = MagicMock()
        first_response.status_code = 200
        first_response.json.return_value = {
            'choices': [{
                'message': {
                    'content': json.dumps({
                        'summary': 'Apple company reports strong financial results with revenue growth and impressive earnings.',
                        'tags': ['APPLE', 'EARNINGS'],
                        'confidence': 0.8
                    })
                }
            }]
        }
        
        # Mock 第二次回應是純中文（應該成功）
        second_response = MagicMock()
        second_response.status_code = 200
        second_response.json.return_value = {
            'choices': [{
                'message': {
                    'content': json.dumps({
                        'summary': '蘋果公司財報表現強勁，營收增長顯著，獲利表現令人印象深刻，持續展現優異的營運能力。',
                        'tags': ['APPLE', 'EARNINGS'],
                        'confidence': 0.9
                    }, ensure_ascii=False)
                }
            }]
        }
        
        # 設置 mock 依序返回不同回應
        mock_post.side_effect = [first_response, second_response]
        
        # 測試重試機制
        summary, tags = self.scraper.generate_summary_and_tags(self.test_title, self.test_content)
        
        # 驗證最終結果是中文
        self.assertIn("蘋果", summary, "重試後應該得到中文摘要")
        self.assertNotIn("Apple", summary, "重試後不應包含英文")
        
        # 驗證調用了兩次 API（第一次失敗，第二次成功）
        self.assertEqual(mock_post.call_count, 2, "應該調用兩次 API（重試一次）")
        
        print("✅ 重試機制測試通過")
        print(f"    最終摘要: {summary}")
    
    @patch('scraper.scraper.requests.post')
    def test_quality_monitoring(self, mock_post):
        """測試品質監控功能"""
        # 清除之前的統計
        monitor = get_quality_monitor()
        monitor.session_stats = {
            'total_attempts': 0,
            'successful_summaries': 0,
            'failed_summaries': 0,
            'chinese_valid': 0,
            'chinese_invalid': 0,
            'retry_needed': 0,
            'total_generation_time': 0.0
        }
        
        # Mock 成功的 API 回應
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'choices': [{
                'message': {
                    'content': json.dumps({
                        'summary': '測試用的中文摘要，用於驗證品質監控系統是否正常運作，並確保統計數據正確記錄。',
                        'tags': ['TEST'],
                        'confidence': 0.9
                    }, ensure_ascii=False)
                }
            }]
        }
        mock_post.return_value = mock_response
        
        # 執行摘要生成
        test_title = "測試標題"
        test_content = "測試內容"
        summary, tags = self.scraper.generate_summary_and_tags(test_title, test_content)
        
        # 檢查監控統計
        stats = monitor.get_session_summary()
        
        self.assertGreater(stats['total_attempts'], 0, "應該記錄嘗試次數")
        self.assertGreater(stats['successful_summaries'], 0, "應該記錄成功次數")
        self.assertGreater(stats['chinese_valid'], 0, "應該記錄中文有效次數")
        self.assertGreater(stats['success_rate'], 0.8, "成功率應該較高")
        self.assertGreater(stats['chinese_valid_rate'], 0.8, "中文有效率應該較高")
        
        print("✅ 品質監控測試通過")
        print(f"    統計數據: {stats}")
    
    def test_quality_report_generation(self):
        """測試品質報告生成"""
        monitor = get_quality_monitor()
        
        try:
            report = monitor.generate_quality_report()
            
            self.assertIsInstance(report, str)
            self.assertIn("摘要品質監控報告", report)
            self.assertIn("當前會話統計", report)
            
            print("✅ 品質報告生成測試通過")
            print("\n--- 品質報告樣例 ---")
            print(report[:300] + "..." if len(report) > 300 else report)
            
        except Exception as e:
            self.fail(f"品質報告生成失敗: {e}")
    
    def test_english_keyword_detection(self):
        """測試英文關鍵詞檢測功能"""
        test_cases = [
            ("這是純中文摘要，不包含任何英文詞彙。", False),
            ("這個摘要包含 the 英文詞彙。", True),
            ("Some text with English and 中文混合。", True),
            ("蘋果公司的營收 for 這個季度表現優異。", True),
            ("完全沒有問題的繁體中文摘要內容。", False),
        ]
        
        for text, expected_has_english in test_cases:
            _, _, _, has_english = self.scraper._validate_chinese_summary(text)
            self.assertEqual(has_english, expected_has_english, 
                           f"英文檢測錯誤: '{text}' -> 預期 {expected_has_english}, 實際 {has_english}")
        
        print("✅ 英文關鍵詞檢測測試通過")

def run_improved_summary_tests():
    """執行改進摘要功能測試"""
    print("\n" + "="*60)
    print("🧪 開始測試改進後的摘要生成功能")
    print("="*60)
    
    # 檢查環境
    if not os.environ.get('OPENAI_API_KEY'):
        print("⚠️ 警告: 未設置 OPENAI_API_KEY，部分測試會被模擬")
    
    # 執行測試
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestImprovedSummary)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 測試結果總結
    print("\n" + "="*60)
    if result.wasSuccessful():
        print("🎉 所有測試通過！摘要改進功能運行正常")
        print("\n📈 改進亮點:")
        print("  - ✅ 強化的中文語言要求 prompt")
        print("  - ✅ 智能重試機制（最多2次重試）")
        print("  - ✅ 中文字符比例驗證（>= 80%）")
        print("  - ✅ 英文關鍵詞檢測和過濾")
        print("  - ✅ 品質監控和統計功能")
        print("  - ✅ 詳細的錯誤記錄和分析")
        print("\n🚀 預期改進效果:")
        print("  - 中文摘要準確率提升至 95%+")
        print("  - 更好的錯誤處理和監控")
        print("  - 提供品質統計和趨勢分析")
    else:
        print(f"❌ 有 {len(result.failures + result.errors)} 個測試失敗")
        for test, error in result.failures + result.errors:
            print(f"   - {test}: {error.splitlines()[-1] if error else '未知錯誤'}")
    print("="*60)
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_improved_summary_tests()
    sys.exit(0 if success else 1)