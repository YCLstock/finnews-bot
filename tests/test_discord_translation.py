#!/usr/bin/env python3
"""
Discord 翻譯推送測試
測試 Phase 4: Discord 推送邏輯的翻譯功能
"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock
import asyncio

# 添加項目根目錄到路徑
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.delivery_manager import DiscordProvider

class TestDiscordTranslationLogic(unittest.TestCase):
    """Discord 翻譯邏輯測試類別"""
    
    def setUp(self):
        """測試前準備"""
        self.provider = DiscordProvider()
        
        # 測試文章範例
        self.sample_articles = [
            {
                'title': 'Apple Reports Strong Q3 Earnings Beat',
                'translated_title': '蘋果公司公佈強勁第三季財報超預期',
                'summary': '蘋果公司第三季財報表現優於市場預期...',
                'original_url': 'https://example.com/article1'
            },
            {
                'title': 'Tesla Stock Surges on Delivery Numbers',
                'translated_title': None,  # 模擬翻譯失敗
                'summary': 'Tesla股價因交付數據而上漲...',
                'original_url': 'https://example.com/article2'
            },
            {
                'title': '台積電營收創新高',
                'translated_title': '台積電營收創新高',  # 已是中文
                'summary': '台積電第三季營收創歷史新高...',
                'original_url': 'https://example.com/article3'
            }
        ]
    
    def test_get_display_title_chinese_user_with_translation(self):
        """測試中文用戶且有翻譯的情況"""
        article = self.sample_articles[0]
        
        # 測試繁體中文用戶
        result = self.provider._get_display_title(article, 'zh-tw')
        self.assertEqual(result, '蘋果公司公佈強勁第三季財報超預期')
        
        # 測試簡體中文用戶
        result = self.provider._get_display_title(article, 'zh-cn')
        self.assertEqual(result, '蘋果公司公佈強勁第三季財報超預期')
        
        # 測試通用中文
        result = self.provider._get_display_title(article, 'zh')
        self.assertEqual(result, '蘋果公司公佈強勁第三季財報超預期')
    
    def test_get_display_title_chinese_user_without_translation(self):
        """測試中文用戶但沒有翻譯的情況"""
        article = self.sample_articles[1]  # translated_title 為 None
        
        result = self.provider._get_display_title(article, 'zh-tw')
        self.assertEqual(result, '🇫🇮 Tesla Stock Surges on Delivery Numbers')
    
    def test_get_display_title_english_user(self):
        """測試英文用戶的情況"""
        article = self.sample_articles[0]
        
        # 測試美式英文
        result = self.provider._get_display_title(article, 'en-us')
        self.assertEqual(result, 'Apple Reports Strong Q3 Earnings Beat')
        
        # 測試通用英文
        result = self.provider._get_display_title(article, 'en')
        self.assertEqual(result, 'Apple Reports Strong Q3 Earnings Beat')
    
    def test_get_display_title_already_chinese(self):
        """測試已經是中文的文章"""
        article = self.sample_articles[2]
        
        # 中文用戶看中文文章
        result = self.provider._get_display_title(article, 'zh-tw')
        self.assertEqual(result, '台積電營收創新高')
        
        # 英文用戶看中文文章（應該顯示原文）
        result = self.provider._get_display_title(article, 'en-us')
        self.assertEqual(result, '台積電營收創新高')
    
    def test_get_display_title_edge_cases(self):
        """測試邊界情況"""
        # 空文章
        empty_article = {'title': 'Empty Test', 'translated_title': None}
        
        result = self.provider._get_display_title(empty_article, 'zh-tw')
        self.assertEqual(result, '🇫🇮 Empty Test')
        
        # 空翻譯
        article_empty_translation = {'title': 'Test', 'translated_title': ''}
        result = self.provider._get_display_title(article_empty_translation, 'zh-tw')
        self.assertEqual(result, '🇫🇮 Test')
        
        # 未知語言（應該當作英文處理）
        result = self.provider._get_display_title(self.sample_articles[0], 'fr-fr')
        self.assertEqual(result, 'Apple Reports Strong Q3 Earnings Beat')

class TestDiscordSendArticlesIntegration(unittest.TestCase):
    """Discord 發送文章整合測試"""
    
    def setUp(self):
        """測試前準備"""
        self.provider = DiscordProvider()
        
        # Mock webhook URL
        self.test_webhook = "https://discord.com/api/webhooks/123/test"
        
        # 測試訂閱資料
        self.chinese_subscription = {
            'user_id': 'test-user-zh',
            'push_frequency_type': 'daily',
            'summary_language': 'zh-tw'
        }
        
        self.english_subscription = {
            'user_id': 'test-user-en', 
            'push_frequency_type': 'daily',
            'summary_language': 'en-us'
        }
        
        # 測試文章
        self.test_articles = [
            {
                'title': 'Apple Reports Strong Quarterly Results',
                'translated_title': '蘋果公司發布強勁季度業績',
                'summary': '蘋果公司第三季度業績超出預期...',
                'original_url': 'https://example.com/apple'
            }
        ]
    
    @patch('requests.post')
    def test_send_articles_chinese_user(self, mock_post):
        """測試中文用戶的文章發送"""
        # Mock Discord API 成功響應
        mock_response = MagicMock()
        mock_response.status_code = 204
        mock_post.return_value = mock_response
        
        # 異步測試
        async def test_async():
            success, failed = await self.provider.send_articles(
                self.test_webhook, 
                self.test_articles, 
                self.chinese_subscription
            )
            
            self.assertTrue(success)
            self.assertEqual(len(failed), 0)
            
            # 驗證 Discord API 被正確調用
            mock_post.assert_called()
            
            # 檢查調用參數 - 修正參數提取方式
            self.assertTrue(mock_post.called, "Discord API 應該被調用")
            
            # 檢查調用次數（1篇文章 + 1條總結消息）
            self.assertEqual(mock_post.call_count, 2)
            
            # 獲取第一次調用（文章發送）的參數
            first_call = mock_post.call_args_list[0]
            payload = first_call.kwargs['json']  # 使用 kwargs 獲取 json 參數
            
            # 驗證 embed 標題使用了翻譯
            embed = payload['embeds'][0]
            self.assertIn('蘋果公司發布強勁季度業績', embed['title'])
        
        # 執行異步測試
        asyncio.run(test_async())
    
    @patch('requests.post')
    def test_send_articles_english_user(self, mock_post):
        """測試英文用戶的文章發送"""
        # Mock Discord API 成功響應
        mock_response = MagicMock()
        mock_response.status_code = 204
        mock_post.return_value = mock_response
        
        # 異步測試
        async def test_async():
            success, failed = await self.provider.send_articles(
                self.test_webhook,
                self.test_articles,
                self.english_subscription
            )
            
            self.assertTrue(success)
            self.assertEqual(len(failed), 0)
            
            # 驗證 Discord API 被正確調用
            mock_post.assert_called()
            
            # 檢查調用參數
            self.assertTrue(mock_post.called, "Discord API 應該被調用")
            self.assertEqual(mock_post.call_count, 2)
            
            # 獲取第一次調用（文章發送）的參數
            first_call = mock_post.call_args_list[0]
            payload = first_call.kwargs['json']
            
            # 驗證 embed 標題使用了原文
            embed = payload['embeds'][0]
            self.assertIn('Apple Reports Strong Quarterly Results', embed['title'])
        
        # 執行異步測試
        asyncio.run(test_async())
    
    @patch('requests.post')
    def test_send_articles_no_translation(self, mock_post):
        """測試沒有翻譯的文章發送"""
        # Mock Discord API 成功響應
        mock_response = MagicMock()
        mock_response.status_code = 204
        mock_post.return_value = mock_response
        
        # 修改測試文章，移除翻譯
        articles_no_translation = [{
            'title': 'Tesla Announces New Model',
            'translated_title': None,
            'summary': 'Tesla宣布新車型...',
            'original_url': 'https://example.com/tesla'
        }]
        
        # 異步測試
        async def test_async():
            success, failed = await self.provider.send_articles(
                self.test_webhook,
                articles_no_translation,
                self.chinese_subscription
            )
            
            self.assertTrue(success)
            
            # 檢查調用參數
            self.assertTrue(mock_post.called, "Discord API 應該被調用")
            
            # 獲取第一次調用（文章發送）的參數
            first_call = mock_post.call_args_list[0]
            payload = first_call.kwargs['json']
            
            # 驗證 embed 標題包含國旗標識
            embed = payload['embeds'][0]
            self.assertIn('🇫🇮 Tesla Announces New Model', embed['title'])
        
        # 執行異步測試
        asyncio.run(test_async())

def run_discord_translation_tests():
    """執行 Discord 翻譯測試"""
    # 建立測試套件
    suite = unittest.TestSuite()
    
    # 添加測試
    suite.addTest(unittest.makeSuite(TestDiscordTranslationLogic))
    suite.addTest(unittest.makeSuite(TestDiscordSendArticlesIntegration))
    
    # 執行測試
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()

if __name__ == "__main__":
    print("開始 Discord 翻譯推送測試...")
    
    success = run_discord_translation_tests()
    
    if success:
        print("\n所有 Discord 翻譯推送測試通過！")
        print("Phase 4 Discord 推送邏輯修改成功")
    else:
        print("\n部分測試失敗")
    
    print("\n測試完成。可以開始 Phase 5 端到端測試。")