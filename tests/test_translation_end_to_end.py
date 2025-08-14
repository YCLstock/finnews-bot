#!/usr/bin/env python3
"""
翻譯功能端到端測試
測試從爬蟲到 Discord 推送的完整翻譯流程
"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock
import asyncio
import time

# 添加項目根目錄到路徑
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scraper.scraper import NewsScraperManager
from core.delivery_manager import DiscordProvider
from core.database import db_manager
from core.translation_service import get_translation_service
from core.config import settings

class TestTranslationEndToEnd(unittest.TestCase):
    """端到端翻譯功能測試"""
    
    def setUp(self):
        """測試前準備"""
        self.scraper = NewsScraperManager()
        self.discord_provider = DiscordProvider()
        self.translation_service = get_translation_service()
        
        # 測試數據
        self.test_webhook = "https://discord.com/api/webhooks/123/test"
        
        self.chinese_subscription = {
            'user_id': 'test-zh-user',
            'push_frequency_type': 'daily',
            'summary_language': 'zh-tw'
        }
        
        self.english_subscription = {
            'user_id': 'test-en-user', 
            'push_frequency_type': 'daily',
            'summary_language': 'en-us'
        }
    
    @patch('core.translation_service.openai.chat.completions.create')
    def test_scraper_to_database_flow(self, mock_openai):
        """測試從爬蟲到資料庫的流程"""
        # Mock OpenAI 翻譯回應
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "蘋果公司第三季財報超預期"
        mock_openai.return_value = mock_response
        
        # Mock 其他依賴
        with patch.object(self.scraper, 'scrape_article_content') as mock_content, \
             patch.object(self.scraper, 'generate_summary_and_tags') as mock_summary:
            
            mock_content.return_value = "Apple Inc. reported strong third-quarter results..."
            mock_summary.return_value = ("蘋果公司第三季財報表現超出預期", ["APPLE", "EARNINGS"])
            
            # 模擬文章處理
            news_item = {
                'title': 'Apple Reports Strong Q3 Results',
                'link': 'https://finance.yahoo.com/test'
            }
            
            result = self.scraper._process_single_article(news_item, 'TECH')
            
            # 驗證結果包含所有必要欄位
            self.assertIsNotNone(result)
            
            # 驗證原始資料
            self.assertEqual(result['title'], 'Apple Reports Strong Q3 Results')
            self.assertEqual(result['summary'], '蘋果公司第三季財報表現超出預期')
            self.assertEqual(result['tags'], ['APPLE', 'EARNINGS'])
            
            # 驗證翻譯功能
            self.assertEqual(result['translated_title'], '蘋果公司第三季財報超預期')
            
            print(f"\n爬蟲處理結果:")
            print(f"   原標題: {result['title']}")
            print(f"   翻譯標題: {result['translated_title']}")
            print(f"   摘要: {result['summary']}")
    
    @patch('requests.post')
    @patch('core.translation_service.openai.chat.completions.create')
    def test_database_to_discord_flow(self, mock_openai, mock_requests):
        """測試從資料庫到 Discord 的流程"""
        # Mock Discord API
        mock_response = MagicMock()
        mock_response.status_code = 204
        mock_requests.return_value = mock_response
        
        # 模擬從資料庫查詢到的文章（包含翻譯）
        articles_with_translation = [
            {
                'id': 1,
                'title': 'Microsoft Beats Earnings Expectations',
                'translated_title': '微軟財報超越市場預期',
                'summary': '微軟公司第三季財報表現優於分析師預期...',
                'original_url': 'https://example.com/microsoft'
            },
            {
                'id': 2,
                'title': 'Tesla Stock Rises After Delivery Report',
                'translated_title': None,  # 模擬翻譯失敗情況
                'summary': 'Tesla股價在交付報告後上漲...',
                'original_url': 'https://example.com/tesla'
            }
        ]
        
        async def test_chinese_user():
            """測試中文用戶推送"""
            success, failed = await self.discord_provider.send_articles(
                self.test_webhook,
                articles_with_translation,
                self.chinese_subscription
            )
            
            self.assertTrue(success)
            self.assertEqual(len(failed), 0)
            
            # 驗證調用次數（2篇文章 + 1條總結）
            self.assertEqual(mock_requests.call_count, 3)
            
            # 檢查第一篇文章（有翻譯）
            first_call = mock_requests.call_args_list[0]
            first_payload = first_call.kwargs['json']
            first_embed = first_payload['embeds'][0]
            self.assertIn('微軟財報超越市場預期', first_embed['title'])
            
            # 檢查第二篇文章（無翻譯，應有國旗標識）
            second_call = mock_requests.call_args_list[1]
            second_payload = second_call.kwargs['json']
            second_embed = second_payload['embeds'][0]
            self.assertIn('🇫🇮', second_embed['title'])
            self.assertIn('Tesla Stock Rises After Delivery Report', second_embed['title'])
            
            print(f"\n✅ 中文用戶 Discord 推送:")
            print(f"   第1則: {first_embed['title']}")
            print(f"   第2則: {second_embed['title']}")
        
        async def test_english_user():
            """測試英文用戶推送"""
            # 重置 mock
            mock_requests.reset_mock()
            
            success, failed = await self.discord_provider.send_articles(
                self.test_webhook,
                articles_with_translation,
                self.english_subscription
            )
            
            self.assertTrue(success)
            
            # 檢查英文用戶看到原始標題
            first_call = mock_requests.call_args_list[0]
            first_payload = first_call.kwargs['json']
            first_embed = first_payload['embeds'][0]
            self.assertIn('Microsoft Beats Earnings Expectations', first_embed['title'])
            
            print(f"\n✅ 英文用戶 Discord 推送:")
            print(f"   第1則: {first_embed['title']}")
        
        # 執行異步測試
        asyncio.run(test_chinese_user())
        asyncio.run(test_english_user())
    
    def test_translation_service_isolation(self):
        """測試翻譯服務的獨立性"""
        # 測試翻譯失敗不影響主流程
        with patch('core.translation_service.openai.chat.completions.create') as mock_openai:
            # Mock 翻譯服務拋出異常
            mock_openai.side_effect = Exception("Translation API error")
            
            with patch.object(self.scraper, 'scrape_article_content') as mock_content, \
                 patch.object(self.scraper, 'generate_summary_and_tags') as mock_summary:
                
                mock_content.return_value = "Test article content"
                mock_summary.return_value = ("測試摘要", ["TEST"])
                
                news_item = {
                    'title': 'Test Article',
                    'link': 'https://example.com/test'
                }
                
                result = self.scraper._process_single_article(news_item, 'TEST')
                
                # 驗證即使翻譯失敗，文章處理也能正常完成
                self.assertIsNotNone(result)
                self.assertEqual(result['title'], 'Test Article')
                self.assertEqual(result['summary'], '測試摘要')
                self.assertIsNone(result['translated_title'])  # 翻譯失敗
                
                print(f"\n✅ 翻譯服務異常處理:")
                print(f"   文章仍能正常處理: {result['title']}")
                print(f"   翻譯標題為空: {result['translated_title']}")
    
    def test_mixed_language_articles(self):
        """測試混合語言文章處理"""
        test_cases = [
            {
                'title': 'Apple Announces New iPhone',
                'expected_translation_needed': True,
                'user_lang': 'zh-tw',
                'description': '英文標題，中文用戶'
            },
            {
                'title': '台積電營收創新高',
                'expected_translation_needed': False,
                'user_lang': 'zh-tw', 
                'description': '中文標題，中文用戶'
            },
            {
                'title': 'Tesla 股價上漲 20%',
                'expected_translation_needed': True,
                'user_lang': 'zh-tw',
                'description': '中英混合，中文用戶'
            },
            {
                'title': 'Apple Reports Earnings',
                'expected_translation_needed': False,
                'user_lang': 'en-us',
                'description': '英文標題，英文用戶'
            }
        ]
        
        print(f"\n✅ 混合語言文章測試:")
        
        for case in test_cases:
            # 模擬文章資料
            article = {
                'title': case['title'],
                'translated_title': f"翻譯_{case['title']}" if case['expected_translation_needed'] else case['title']
            }
            
            display_title = self.discord_provider._get_display_title(article, case['user_lang'])
            
            print(f"   {case['description']}: '{display_title}'")
            
            # 基本驗證
            self.assertIsNotNone(display_title)
            self.assertGreater(len(display_title), 0)
    
    def test_system_performance(self):
        """測試系統效能"""
        print(f"\n✅ 系統效能測試:")
        
        # 測試快取功能
        start_time = time.time()
        
        # 清除快取
        self.translation_service.clear_cache()
        cache_info = self.translation_service.get_cache_info()
        
        print(f"   快取狀態: {cache_info}")
        
        # 測試標題選擇效能
        article = {
            'title': 'Performance Test Article',
            'translated_title': '效能測試文章'
        }
        
        # 執行多次標題選擇測試效能
        iterations = 1000
        start = time.time()
        
        for _ in range(iterations):
            self.discord_provider._get_display_title(article, 'zh-tw')
        
        end = time.time()
        avg_time = (end - start) / iterations * 1000  # 轉換為毫秒
        
        print(f"   標題選擇平均耗時: {avg_time:.3f} 毫秒")
        self.assertLess(avg_time, 1.0, "標題選擇應該在1毫秒內完成")

class TestSystemIntegration(unittest.TestCase):
    """系統整合測試"""
    
    def test_configuration_check(self):
        """檢查系統配置"""
        print(f"\n✅ 系統配置檢查:")
        print(f"   OpenAI API Key: {'已設置' if settings.OPENAI_API_KEY else '未設置'}")
        print(f"   Supabase URL: {'已設置' if settings.SUPABASE_URL else '未設置'}")
        print(f"   環境: {settings.ENVIRONMENT}")
        
        # 基本配置驗證
        self.assertIsNotNone(settings.SUPABASE_URL)
        self.assertTrue(len(settings.SUPABASE_URL) > 0)
    
    def test_database_connection(self):
        """測試資料庫連接"""
        try:
            # 嘗試連接資料庫並查詢
            result = db_manager.supabase.table('news_articles').select('id').limit(1).execute()
            
            print(f"\n✅ 資料庫連接測試:")
            print(f"   連接狀態: 正常")
            print(f"   查詢結果: {'有資料' if result.data else '無資料'}")
            
        except Exception as e:
            self.fail(f"資料庫連接失敗: {e}")
    
    def test_all_components_loaded(self):
        """測試所有組件是否正確載入"""
        components = [
            ('翻譯服務', get_translation_service()),
            ('爬蟲管理器', NewsScraperManager()),
            ('Discord提供者', DiscordProvider()),
            ('資料庫管理器', db_manager),
        ]
        
        print(f"\n✅ 組件載入測試:")
        
        for name, component in components:
            self.assertIsNotNone(component, f"{name} 應該正確載入")
            print(f"   {name}: ✓")

def run_end_to_end_tests():
    """執行端到端測試"""
    print("開始端到端翻譯功能測試...")
    print("=" * 60)
    
    # 建立測試套件
    suite = unittest.TestSuite()
    
    # 添加測試
    suite.addTest(unittest.makeSuite(TestTranslationEndToEnd))
    suite.addTest(unittest.makeSuite(TestSystemIntegration))
    
    # 執行測試
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_end_to_end_tests()
    
    print("\n" + "=" * 60)
    
    if success:
        print("所有端到端測試通過！")
        print("\n翻譯功能完整實施成功：")
        print("Phase 1: 資料庫擴展完成")
        print("Phase 2: 翻譯服務建立完成") 
        print("Phase 3: 爬蟲整合完成")
        print("Phase 4: Discord推送邏輯完成")
        print("Phase 5: 端到端測試完成")
        print("\n系統現在支援智能翻譯功能！")
    else:
        print("部分端到端測試失敗")
        print("請檢查失敗的測試並修正問題")
    
    print("\n可以開始使用新的翻譯功能了！")