#!/usr/bin/env python3
"""
檢查 news_articles 表的當前 schema
"""

import os
import sys
import logging

# 添加項目根目錄到路徑
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import db_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_table_schema():
    """檢查表結構"""
    try:
        logger.info("🔍 檢查 news_articles 表當前結構...")
        
        # 嘗試查詢一條記錄來看欄位
        result = db_manager.supabase.table('news_articles').select('*').limit(1).execute()
        
        if result.data:
            article = result.data[0]
            logger.info("📋 當前 news_articles 表包含以下欄位:")
            for field in sorted(article.keys()):
                logger.info(f"  - {field}: {type(article[field]).__name__}")
                
            # 特別檢查 translated_title 欄位
            if 'translated_title' in article:
                logger.info("✅ translated_title 欄位已存在！")
                return True
            else:
                logger.info("❌ translated_title 欄位不存在")
                return False
        else:
            logger.warning("⚠️ 表中沒有資料，無法檢查完整結構")
            
            # 嘗試插入測試資料來檢查欄位
            try:
                test_article = {
                    'original_url': 'https://schema-test-temp.example.com',
                    'source': 'schema_test',
                    'title': 'Schema Test Article',
                    'summary': 'Testing schema',
                    'tags': ['test']
                }
                
                insert_result = db_manager.supabase.table('news_articles').insert(test_article).execute()
                
                if insert_result.data:
                    article_id = insert_result.data[0]['id']
                    logger.info("✅ 基本插入成功，表結構正常")
                    
                    # 清理
                    db_manager.supabase.table('news_articles').delete().eq('id', article_id).execute()
                    
                    return False  # 沒有 translated_title
                
            except Exception as e:
                logger.error(f"測試插入失敗: {e}")
                return False
            
    except Exception as e:
        logger.error(f"檢查表結構失敗: {e}")
        return False

if __name__ == "__main__":
    check_table_schema()