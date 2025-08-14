#!/usr/bin/env python3
"""
執行資料庫遷移腳本
Phase 1: 新增 translated_title 欄位
"""

import os
import sys
import logging

# 添加項目根目錄到路徑
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import db_manager
from core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_migration():
    """執行資料庫遷移"""
    try:
        logger.info("🚀 開始執行 translated_title 欄位遷移...")
        
        # 檢查欄位是否已存在
        logger.info("🔍 檢查欄位是否已存在...")
        
        # 嘗試查詢 translated_title 欄位
        try:
            result = db_manager.supabase.table('news_articles').select('id, translated_title').limit(1).execute()
            logger.info("✅ translated_title 欄位已存在，跳過遷移")
            return True
        except Exception:
            logger.info("📝 translated_title 欄位不存在，開始新增...")
        
        # 執行 ALTER TABLE 語句
        migration_sql = """
        ALTER TABLE public.news_articles 
        ADD COLUMN translated_title TEXT;
        """
        
        logger.info("📝 執行 ALTER TABLE...")
        
        # 使用 RPC 執行原生 SQL
        result = db_manager.supabase.rpc('exec_sql', {'sql_query': migration_sql}).execute()
        
        if result.data:
            logger.info("✅ 成功新增 translated_title 欄位")
        else:
            logger.info("✅ 遷移完成")
        
        # 驗證欄位是否新增成功
        logger.info("🔍 驗證遷移結果...")
        verification_result = db_manager.supabase.table('news_articles').select('id, title, translated_title').limit(1).execute()
        
        if verification_result:
            logger.info("✅ 驗證成功，translated_title 欄位可正常訪問")
            return True
        else:
            logger.error("❌ 驗證失敗")
            return False
            
    except Exception as e:
        logger.error(f"❌ 遷移過程發生錯誤: {e}")
        logger.info("🔄 嘗試使用備用方法...")
        
        # 備用方法：直接嘗試插入包含 translated_title 的資料來觸發欄位創建
        try:
            test_data = {
                'original_url': 'migration-test-url-temp',
                'source': 'migration_test',
                'title': 'Migration Test',
                'summary': 'Test for migration',
                'translated_title': '遷移測試',
                'tags': ['test'],
                'topics': []
            }
            
            # 如果插入成功，說明欄位已存在
            insert_result = db_manager.supabase.table('news_articles').insert(test_data).execute()
            
            if insert_result.data:
                # 清理測試資料
                article_id = insert_result.data[0]['id']
                db_manager.supabase.table('news_articles').delete().eq('id', article_id).execute()
                logger.info("✅ 備用方法驗證成功")
                return True
            
        except Exception as backup_error:
            logger.error(f"❌ 備用方法也失敗: {backup_error}")
            return False

if __name__ == "__main__":
    logger.info(f"環境: {settings.ENVIRONMENT}")
    logger.info(f"資料庫 URL: {settings.SUPABASE_URL}")
    
    if run_migration():
        logger.info("🎉 資料庫遷移成功完成！")
        sys.exit(0)
    else:
        logger.error("❌ 資料庫遷移失敗")
        sys.exit(1)