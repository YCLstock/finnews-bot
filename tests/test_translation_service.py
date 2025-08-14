#!/usr/bin/env python3
"""
翻譯服務單元測試
測試 core/translation_service.py 的各項功能
"""

import unittest
import sys
import os
import time
from unittest.mock import patch, MagicMock

# 添加項目根目錄到路徑
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.translation_service import TranslationService, get_translation_service, translate_title_to_chinese

class TestTranslationService(unittest.TestCase):
    """翻譯服務測試類別"""
    
    def setUp(self):
        """測試前準備"""
        self.service = TranslationService()
        
    def test_is_already_chinese(self):
        """測試中文檢測功能"""
        # 純中文標題（應該不需要翻譯）
        self.assertTrue(self.service._is_already_chinese("蘋果公司第三季度財報"))
        self.assertTrue(self.service._is_already_chinese("微軟股價創新高"))
        self.assertTrue(self.service._is_already_chinese("台積電營收創新高紀錄"))
        
        # 中英混合（中文比例不足，需要翻譯） 
        self.assertFalse(self.service._is_already_chinese("Tesla 股價上漲"))
        self.assertFalse(self.service._is_already_chinese("蘋果 iPhone 銷量上升"))
        self.assertFalse(self.service._is_already_chinese("Apple 新產品發布"))
        
        # 英文標題  
        self.assertFalse(self.service._is_already_chinese("Apple Inc. Q3 Earnings Report"))
        self.assertFalse(self.service._is_already_chinese("Tesla Stock Rises"))
        
        # 邊界情況
        self.assertFalse(self.service._is_already_chinese(""))
        self.assertFalse(self.service._is_already_chinese("123456"))
    
    def test_generate_cache_key(self):
        """測試快取鍵值生成"""
        title1 = "Test Title"
        title2 = "Different Title"
        title3 = "Test Title"  # 與 title1 相同
        
        key1 = self.service._generate_cache_key(title1)
        key2 = self.service._generate_cache_key(title2)
        key3 = self.service._generate_cache_key(title3)
        
        # 相同標題應產生相同鍵值
        self.assertEqual(key1, key3)
        # 不同標題應產生不同鍵值
        self.assertNotEqual(key1, key2)
        # 鍵值長度應為12
        self.assertEqual(len(key1), 12)
    
    def test_validate_translation(self):
        """測試翻譯品質驗證"""
        original = "Apple reports strong Q3 earnings"
        
        # 有效翻譯
        valid_translation = "蘋果公司公佈強勁第三季財報"
        is_valid, confidence = self.service._validate_translation(original, valid_translation)
        self.assertTrue(is_valid)
        self.assertGreaterEqual(confidence, self.service.min_confidence)
        
        # 無效翻譯：空字符串
        is_valid, confidence = self.service._validate_translation(original, "")
        self.assertFalse(is_valid)
        self.assertEqual(confidence, 0.0)
        
        # 無效翻譯：包含原文
        invalid_translation = "Apple 公司財報 strong earnings"
        is_valid, confidence = self.service._validate_translation(original, invalid_translation)
        self.assertFalse(is_valid)
        
        # 無效翻譯：沒有中文
        english_only = "Company reports good results"
        is_valid, confidence = self.service._validate_translation(original, english_only)
        self.assertFalse(is_valid)
        
        # 無效翻譯：過長
        too_long = "蘋果公司" * 20  # 人為創造過長翻譯
        is_valid, confidence = self.service._validate_translation(original, too_long)
        self.assertFalse(is_valid)
    
    def test_singleton_pattern(self):
        """測試單例模式"""
        service1 = get_translation_service()
        service2 = get_translation_service()
        
        # 應該返回同一個實例
        self.assertIs(service1, service2)
    
    def test_convenience_function(self):
        """測試便利函數"""
        with patch.object(TranslationService, 'translate_title_to_chinese') as mock_translate:
            mock_translate.return_value = "測試翻譯結果"
            
            result = translate_title_to_chinese("Test Title")
            
            mock_translate.assert_called_once_with("Test Title")
            self.assertEqual(result, "測試翻譯結果")
    
    def test_cache_functions(self):
        """測試快取功能"""
        # 清除快取
        self.service.clear_cache()
        
        # 檢查快取資訊
        cache_info = self.service.get_cache_info()
        self.assertIsInstance(cache_info, dict)
        self.assertIn('hits', cache_info)
        self.assertIn('misses', cache_info)
        self.assertIn('current_size', cache_info)
        self.assertIn('max_size', cache_info)
        self.assertIn('hit_rate', cache_info)

class TestTranslationServiceIntegration(unittest.TestCase):
    """翻譯服務整合測試（需要真實 API）"""
    
    def setUp(self):
        """測試前準備"""
        self.service = TranslationService()
        
        # 檢查是否有 OpenAI API Key
        from core.config import settings
        self.has_api_key = bool(settings.OPENAI_API_KEY)
        
    def test_translation_with_mock(self):
        """使用 Mock 測試翻譯功能"""
        
        # Mock OpenAI 回應
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "蘋果公司第三季財報表現強勁"
        
        with patch.object(self.service.openai_client.chat.completions, 'create', return_value=mock_response):
            
            # 測試翻譯功能
            result = self.service.translate_title_to_chinese("Apple reports strong Q3 earnings")
            
            self.assertIsNotNone(result)
            self.assertIsInstance(result, str)
            self.assertIn("蘋果", result)
    
    def test_already_chinese_title(self):
        """測試已經是中文的標題"""
        chinese_title = "蘋果公司發布新產品"
        
        # 不應該進行翻譯
        result = self.service.translate_title_to_chinese(chinese_title)
        self.assertEqual(result, chinese_title)
    
    def test_empty_title_handling(self):
        """測試空標題處理"""
        self.assertIsNone(self.service.translate_title_to_chinese(""))
        self.assertIsNone(self.service.translate_title_to_chinese(None))
        self.assertIsNone(self.service.translate_title_to_chinese("   "))
    
    def test_translate_with_details(self):
        """測試詳細翻譯資訊"""
        
        # Mock OpenAI 回應
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "微軟股價創新高"
        
        with patch.object(self.service.openai_client.chat.completions, 'create', return_value=mock_response):
            
            result = self.service.translate_title_with_details("Microsoft stock hits new high")
            
            self.assertIsInstance(result, dict)
            self.assertIn('translated_title', result)
            self.assertIn('confidence', result)
            self.assertIn('method', result)
            self.assertIn('processing_time', result)
            self.assertIn('error', result)
            
            # 檢查結果
            self.assertEqual(result['translated_title'], "微軟股價創新高")
            self.assertGreaterEqual(result['confidence'], 0)
            self.assertLessEqual(result['confidence'], 1.0)
            self.assertIsNone(result['error'])
    
    def test_batch_translation_mock(self):
        """測試批次翻譯（使用 Mock）"""
        
        titles = [
            "Apple earnings beat expectations",
            "Google announces new AI features",
            "Tesla stock price surges"
        ]
        
        mock_translations = [
            "蘋果財報超越預期",
            "Google 宣布新 AI 功能", 
            "Tesla 股價飆升"
        ]
        
        # Mock 翻譯方法
        with patch.object(self.service, 'translate_title_to_chinese') as mock_translate:
            mock_translate.side_effect = mock_translations
            
            results = self.service.batch_translate(titles)
            
            self.assertEqual(len(results), 3)
            self.assertEqual(results[titles[0]], mock_translations[0])
            self.assertEqual(results[titles[1]], mock_translations[1])
            self.assertEqual(results[titles[2]], mock_translations[2])
    
    @unittest.skipUnless(os.getenv('RUN_REAL_API_TESTS') == 'true', "需要設置 RUN_REAL_API_TESTS=true 來執行真實 API 測試")
    def test_real_translation(self):
        """真實 API 翻譯測試（僅在明確啟用時執行）"""
        if not self.has_api_key:
            self.skip("需要 OpenAI API Key")
        
        # 測試英文標題翻譯
        english_title = "Apple reports record quarterly revenue"
        result = self.service.translate_title_to_chinese(english_title)
        
        print(f"\n真實翻譯測試:")
        print(f"原文: {english_title}")
        print(f"翻譯: {result}")
        
        if result:
            self.assertIsInstance(result, str)
            self.assertTrue(len(result) > 0)
            # 檢查是否包含中文字符
            import re
            chinese_chars = re.findall(r'[\u4e00-\u9fff]', result)
            self.assertGreater(len(chinese_chars), 0, "翻譯結果應包含中文字符")

def run_translation_tests():
    """執行翻譯服務測試"""
    # 建立測試套件
    suite = unittest.TestSuite()
    
    # 添加單元測試
    suite.addTest(unittest.makeSuite(TestTranslationService))
    suite.addTest(unittest.makeSuite(TestTranslationServiceIntegration))
    
    # 執行測試
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 返回測試結果
    return result.wasSuccessful()

if __name__ == "__main__":
    print("開始翻譯服務測試...")
    
    success = run_translation_tests()
    
    if success:
        print("\n所有翻譯服務測試通過！")
    else:
        print("\n部分翻譯服務測試失敗")
    
    # 如果想執行真實 API 測試，設置環境變數：
    # export RUN_REAL_API_TESTS=true
    # python tests/test_translation_service.py