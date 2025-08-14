#!/usr/bin/env python3
"""
翻譯功能 Phase 1 測試腳本
測試資料庫遷移和向後相容性
"""

import os
import sys
import logging
from typing import Dict, Any

# 添加項目根目錄到路徑
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import db_manager
from core.config import settings

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TranslationMigrationTest:
    """翻譯功能資料庫遷移測試類別"""
    
    def __init__(self):
        self.db = db_manager
    
    def test_column_exists(self) -> bool:
        """測試 translated_title 欄位是否存在"""
        try:
            logger.info("🔍 測試 translated_title 欄位是否存在...")
            
            # 直接嘗試查詢 translated_title 欄位
            result = self.db.supabase.table('news_articles').select(
                'id, translated_title'
            ).limit(1).execute()
            
            if result.data:
                # 檢查返回的資料是否包含 translated_title 欄位
                first_record = result.data[0]
                if 'translated_title' in first_record:
                    logger.info(f"✅ translated_title 欄位存在且可正常訪問")
                    logger.info(f"   - 欄位值: {first_record.get('translated_title', 'NULL')}")
                    return True
                else:
                    logger.error("❌ translated_title 欄位不存在於查詢結果中")
                    return False
            else:
                # 如果沒有資料，嘗試插入測試來驗證欄位
                logger.info("表中無資料，嘗試插入測試驗證欄位存在性")
                test_data = {
                    'original_url': 'column-test-temp-url',
                    'source': 'column_test',
                    'title': 'Column Test',
                    'summary': 'Testing column existence',
                    'translated_title': '欄位測試',
                    'tags': ['test']
                }
                
                insert_result = self.db.supabase.table('news_articles').insert(test_data).execute()
                
                if insert_result.data:
                    # 清理測試資料
                    test_id = insert_result.data[0]['id']
                    self.db.supabase.table('news_articles').delete().eq('id', test_id).execute()
                    logger.info("✅ translated_title 欄位存在（通過插入測試驗證）")
                    return True
                else:
                    logger.error("❌ 插入測試失敗，欄位可能不存在")
                    return False
                
        except Exception as e:
            logger.error(f"❌ 檢查欄位存在性失敗: {e}")
            return False
    
    def test_backward_compatibility(self) -> bool:
        """測試向後相容性 - 現有功能正常運作"""
        try:
            logger.info("🔍 測試向後相容性...")
            
            # 測試基本查詢功能
            result = self.db.supabase.table('news_articles').select(
                'id, title, summary, original_url, translated_title'
            ).limit(5).execute()
            
            if result.data:
                logger.info(f"✅ 基本查詢功能正常 (查詢到 {len(result.data)} 筆資料)")
                
                # 檢查舊資料是否有translated_title欄位
                for article in result.data:
                    if 'translated_title' in article:
                        logger.info(f"✅ 文章 ID {article['id']} 包含 translated_title 欄位")
                    else:
                        logger.error(f"❌ 文章 ID {article['id']} 缺少 translated_title 欄位")
                        return False
                
                return True
            else:
                logger.warning("⚠️ 資料庫中無文章資料，無法測試相容性")
                return True
                
        except Exception as e:
            logger.error(f"❌ 向後相容性測試失敗: {e}")
            return False
    
    def test_insert_with_translation(self) -> bool:
        """測試新增文章時包含翻譯標題"""
        try:
            logger.info("🔍 測試新增文章包含翻譯標題...")
            
            test_article = {
                'original_url': f'https://test-translation-{int(time.time())}.example.com',
                'source': 'test',
                'title': 'Test Article for Translation Feature',
                'summary': 'This is a test article to verify translation functionality',
                'translated_title': '翻譯功能測試文章',
                'tags': ['test'],
                'topics': []
            }
            
            # 插入測試文章
            result = self.db.supabase.table('news_articles').insert(test_article).execute()
            
            if result.data:
                inserted_article = result.data[0]
                article_id = inserted_article['id']
                logger.info(f"✅ 成功新增包含翻譯的文章 (ID: {article_id})")
                
                # 驗證翻譯標題是否正確儲存
                if inserted_article.get('translated_title') == test_article['translated_title']:
                    logger.info("✅ 翻譯標題正確儲存")
                    
                    # 清理測試資料
                    self.db.supabase.table('news_articles').delete().eq('id', article_id).execute()
                    logger.info("🗑️ 清理測試資料完成")
                    return True
                else:
                    logger.error("❌ 翻譯標題儲存不正確")
                    return False
            else:
                logger.error("❌ 新增包含翻譯的文章失敗")
                return False
                
        except Exception as e:
            logger.error(f"❌ 新增翻譯文章測試失敗: {e}")
            return False
    
    def test_performance(self) -> bool:
        """測試查詢效能是否有明顯下降"""
        try:
            logger.info("🔍 測試查詢效能...")
            import time
            
            start_time = time.time()
            
            # 執行較大量的查詢
            result = self.db.supabase.table('news_articles').select(
                'id, title, summary, translated_title'
            ).limit(100).execute()
            
            query_time = time.time() - start_time
            
            logger.info(f"✅ 查詢 100 筆文章耗時: {query_time:.3f} 秒")
            
            if query_time < 5.0:  # 5秒內完成認為效能可接受
                logger.info("✅ 查詢效能測試通過")
                return True
            else:
                logger.warning(f"⚠️ 查詢耗時較長: {query_time:.3f} 秒")
                return False
                
        except Exception as e:
            logger.error(f"❌ 效能測試失敗: {e}")
            return False
    
    def run_all_tests(self) -> bool:
        """執行所有測試"""
        logger.info("🚀 開始 Phase 1 資料庫遷移測試...")
        
        tests = [
            ("欄位存在性測試", self.test_column_exists),
            ("向後相容性測試", self.test_backward_compatibility), 
            ("翻譯新增測試", self.test_insert_with_translation),
            ("效能測試", self.test_performance)
        ]
        
        results = []
        for test_name, test_func in tests:
            logger.info(f"\n📋 執行 {test_name}...")
            try:
                result = test_func()
                results.append(result)
                if result:
                    logger.info(f"✅ {test_name} 通過")
                else:
                    logger.error(f"❌ {test_name} 失敗")
            except Exception as e:
                logger.error(f"❌ {test_name} 發生異常: {e}")
                results.append(False)
        
        success_count = sum(results)
        total_count = len(results)
        
        logger.info(f"\n📊 測試結果: {success_count}/{total_count} 個測試通過")
        
        if success_count == total_count:
            logger.info("🎉 所有 Phase 1 測試通過，可以繼續 Phase 2！")
            return True
        else:
            logger.error("❌ 部分測試失敗，請檢查問題後重新執行")
            return False

if __name__ == "__main__":
    import time
    
    logger.info("翻譯功能 Phase 1 測試開始")
    logger.info(f"環境: {settings.ENVIRONMENT}")
    logger.info(f"資料庫: {settings.SUPABASE_URL}")
    
    tester = TranslationMigrationTest()
    success = tester.run_all_tests()
    
    if success:
        logger.info("\n✅ Phase 1 測試全部通過，資料庫遷移成功！")
        sys.exit(0)
    else:
        logger.error("\n❌ Phase 1 測試失敗，請檢查問題")
        sys.exit(1)