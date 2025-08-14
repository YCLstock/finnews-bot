#!/usr/bin/env python3
"""
爬蟲翻譯整合測試
測試 Phase 3: 爬蟲整合翻譯功能
"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock
import time

# 添加項目根目錄到路徑
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scraper.scraper import NewsScraperManager
from core.translation_service import get_translation_service

class TestScraperTranslationIntegration(unittest.TestCase):
    """爬蟲翻譯整合測試類別"""
    
    def setUp(self):
        """測試前準備"""
        self.scraper = NewsScraperManager()
        self.translation_service = get_translation_service()
    
    def test_translation_import(self):
        """測試翻譯服務是否正確導入"""
        from scraper.scraper import translate_title_to_chinese
        self.assertTrue(callable(translate_title_to_chinese))
    
    @patch('scraper.scraper.translate_title_to_chinese')
    def test_process_article_with_translation_success(self, mock_translate):
        """測試文章處理包含成功翻譯"""
        # Mock 翻譯結果
        mock_translate.return_value = "蘋果公司發布財報"
        
        # Mock 其他依賴
        with patch.object(self.scraper, 'scrape_article_content') as mock_content, \
             patch.object(self.scraper, 'generate_summary_and_tags') as mock_summary:
            
            mock_content.return_value = "Sample article content about Apple earnings..."
            mock_summary.return_value = ("蘋果公司第三季財報表現強勁", ["APPLE", "EARNINGS"])
            
            # 測試文章處理
            news_item = {
                'title': 'Apple Reports Strong Q3 Earnings',
                'link': 'https://finance.yahoo.com/test-article'
            }
            
            result = self.scraper._process_single_article(news_item, 'TECH')
            
            # 驗證結果
            self.assertIsNotNone(result)
            self.assertEqual(result['title'], 'Apple Reports Strong Q3 Earnings')
            self.assertEqual(result['translated_title'], '蘋果公司發布財報')
            self.assertEqual(result['summary'], '蘋果公司第三季財報表現強勁')
            self.assertEqual(result['tags'], ['APPLE', 'EARNINGS'])
            
            # 驗證翻譯函數被調用
            mock_translate.assert_called_once_with('Apple Reports Strong Q3 Earnings')
    
    @patch('scraper.scraper.translate_title_to_chinese')
    def test_process_article_with_translation_failure(self, mock_translate):
        """測試翻譯失敗時的處理"""
        # Mock 翻譯失敗
        mock_translate.return_value = None
        
        # Mock 其他依賴
        with patch.object(self.scraper, 'scrape_article_content') as mock_content, \
             patch.object(self.scraper, 'generate_summary_and_tags') as mock_summary:
            
            mock_content.return_value = "Sample article content..."
            mock_summary.return_value = ("測試摘要", ["TEST"])
            
            # 測試文章處理
            news_item = {
                'title': 'Test Article Title',
                'link': 'https://finance.yahoo.com/test-article-2'
            }
            
            result = self.scraper._process_single_article(news_item, 'TEST')
            
            # 驗證結果：翻譯失敗但文章處理正常
            self.assertIsNotNone(result)
            self.assertEqual(result['title'], 'Test Article Title')
            self.assertIsNone(result['translated_title'])  # 翻譯失敗，應為 None
            self.assertEqual(result['summary'], '測試摘要')
    
    @patch('scraper.scraper.translate_title_to_chinese')
    def test_process_article_translation_exception(self, mock_translate):
        """測試翻譯過程發生異常時的處理"""
        # Mock 翻譯拋出異常
        mock_translate.side_effect = Exception("Translation service error")
        
        # Mock 其他依賴
        with patch.object(self.scraper, 'scrape_article_content') as mock_content, \
             patch.object(self.scraper, 'generate_summary_and_tags') as mock_summary:
            
            mock_content.return_value = "Sample article content..."
            mock_summary.return_value = ("測試摘要", ["TEST"])
            
            # 測試文章處理
            news_item = {
                'title': 'Test Article Exception',
                'link': 'https://finance.yahoo.com/test-article-3'
            }
            
            result = self.scraper._process_single_article(news_item, 'TEST')
            
            # 驗證結果：異常處理正確，文章處理不受影響
            self.assertIsNotNone(result)
            self.assertEqual(result['title'], 'Test Article Exception')
            self.assertIsNone(result['translated_title'])  # 異常時應為 None
            self.assertEqual(result['summary'], '測試摘要')
    
    def test_article_data_structure(self):
        """測試文章資料結構包含翻譯欄位"""
        # Mock 所有依賴
        with patch.object(self.scraper, 'scrape_article_content') as mock_content, \
             patch.object(self.scraper, 'generate_summary_and_tags') as mock_summary, \
             patch('scraper.scraper.translate_title_to_chinese') as mock_translate:
            
            mock_content.return_value = "Sample article content..."
            mock_summary.return_value = ("測試摘要", ["TEST"])
            mock_translate.return_value = "測試翻譯標題"
            
            news_item = {
                'title': 'Structure Test Article',
                'link': 'https://finance.yahoo.com/structure-test'
            }
            
            result = self.scraper._process_single_article(news_item, 'TEST')
            
            # 驗證資料結構
            required_fields = [
                'original_url', 'source', 'title', 'summary', 
                'translated_title', 'tags', 'topics', 'published_at'
            ]
            
            for field in required_fields:
                self.assertIn(field, result, f"Missing field: {field}")
            
            # 驗證翻譯欄位
            self.assertEqual(result['translated_title'], '測試翻譯標題')
    
    def test_chinese_title_handling(self):
        """測試已經是中文的標題處理"""
        with patch.object(self.scraper, 'scrape_article_content') as mock_content, \
             patch.object(self.scraper, 'generate_summary_and_tags') as mock_summary, \
             patch('scraper.scraper.translate_title_to_chinese') as mock_translate:
            
            mock_content.return_value = "測試文章內容..."
            mock_summary.return_value = ("這是測試摘要", ["TEST"])
            
            # 模擬中文標題（翻譯服務會返回原標題）
            chinese_title = "蘋果公司發布新產品"
            mock_translate.return_value = chinese_title
            
            news_item = {
                'title': chinese_title,
                'link': 'https://finance.yahoo.com/chinese-test'
            }
            
            result = self.scraper._process_single_article(news_item, 'TEST')
            
            # 驗證結果
            self.assertIsNotNone(result)
            self.assertEqual(result['title'], chinese_title)
            self.assertEqual(result['translated_title'], chinese_title)

class TestScraperTranslationReal(unittest.TestCase):
    """真實環境下的翻譯整合測試"""
    
    def setUp(self):
        """測試前準備"""
        from core.config import settings
        self.has_api_key = bool(settings.OPENAI_API_KEY)
    
    @unittest.skipUnless(os.getenv('RUN_REAL_SCRAPER_TESTS') == 'true', "需要設置 RUN_REAL_SCRAPER_TESTS=true")
    def test_real_translation_integration(self):
        """真實翻譯整合測試"""
        if not self.has_api_key:
            self.skipTest("需要 OpenAI API Key")
        
        from scraper.scraper import translate_title_to_chinese
        
        # 測試真實翻譯
        test_title = "Apple reports quarterly earnings beat"
        result = translate_title_to_chinese(test_title)
        
        print(f"\n真實翻譯測試:")
        print(f"原標題: {test_title}")
        print(f"翻譯結果: {result}")
        
        if result:
            self.assertIsInstance(result, str)
            self.assertNotEqual(result, test_title)  # 翻譯後應該不同

def run_scraper_translation_tests():
    """執行爬蟲翻譯整合測試"""
    # 建立測試套件
    suite = unittest.TestSuite()
    
    # 添加測試
    suite.addTest(unittest.makeSuite(TestScraperTranslationIntegration))
    suite.addTest(unittest.makeSuite(TestScraperTranslationReal))
    
    # 執行測試
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()

if __name__ == "__main__":
    print("開始爬蟲翻譯整合測試...")
    
    success = run_scraper_translation_tests()
    
    if success:
        print("\n所有爬蟲翻譯整合測試通過！")
        print("Phase 3 整合成功完成")
    else:
        print("\n部分測試失敗")
    
    # 如果想執行真實 API 測試，設置環境變數：
    # export RUN_REAL_SCRAPER_TESTS=true
    # python tests/test_scraper_translation.py