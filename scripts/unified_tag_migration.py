#!/usr/bin/env python3
"""
統一標籤管理系統 - 數據遷移和統一腳本
將硬編碼標籤同步到Supabase資料庫，實現系統統一
"""

import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Tuple

# 添加項目根目錄到 Python 路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.database import db_manager
from core.logger_config import setup_logging

# 設定 logger
logger = logging.getLogger(__name__)

class TagMigrationManager:
    """標籤系統統一遷移管理器"""
    
    def __init__(self):
        # 當前硬編碼的標籤 (來自scraper.py)
        self.current_hardcoded_tags = [
            "APPLE", "TSMC", "TESLA", "AI_TECH", "CRYPTO",
            "STOCK_MARKET", "ECONOMIES", "LATEST", "EARNINGS", 
            "TECH", "ELECTRIC_VEHICLES", "FEDERAL_RESERVE",
            "HOUSING", "ENERGY", "HEALTHCARE", "FINANCE",
            "TARIFFS", "TRADE", "COMMODITIES", "BONDS"
        ]
        
        # 標籤中英文對照
        self.tag_translations = {
            "APPLE": {"zh": "蘋果公司", "en": "Apple Inc.", "priority": 10},
            "TSMC": {"zh": "台積電", "en": "Taiwan Semiconductor", "priority": 10},
            "TESLA": {"zh": "特斯拉", "en": "Tesla Inc.", "priority": 10},
            "AI_TECH": {"zh": "AI科技", "en": "AI Technology", "priority": 15},
            "CRYPTO": {"zh": "加密貨幣", "en": "Cryptocurrency", "priority": 20},
            "STOCK_MARKET": {"zh": "股票市場", "en": "Stock Market", "priority": 5},
            "ECONOMIES": {"zh": "經濟指標", "en": "Economic Indicators", "priority": 5},
            "LATEST": {"zh": "最新消息", "en": "Latest News", "priority": 30},
            "EARNINGS": {"zh": "企業財報", "en": "Corporate Earnings", "priority": 8},
            "TECH": {"zh": "科技產業", "en": "Technology Sector", "priority": 12},
            "ELECTRIC_VEHICLES": {"zh": "電動車", "en": "Electric Vehicles", "priority": 15},
            "FEDERAL_RESERVE": {"zh": "聯準會", "en": "Federal Reserve", "priority": 6},
            "HOUSING": {"zh": "房地產", "en": "Real Estate", "priority": 18},
            "ENERGY": {"zh": "能源產業", "en": "Energy Sector", "priority": 16},
            "HEALTHCARE": {"zh": "醫療保健", "en": "Healthcare", "priority": 20},
            "FINANCE": {"zh": "金融業", "en": "Financial Services", "priority": 12},
            "TARIFFS": {"zh": "關稅貿易", "en": "Tariffs & Trade", "priority": 14},
            "TRADE": {"zh": "國際貿易", "en": "International Trade", "priority": 14},
            "COMMODITIES": {"zh": "商品期貨", "en": "Commodities", "priority": 17},
            "BONDS": {"zh": "債券市場", "en": "Bond Market", "priority": 19}
        }
        
        # 基礎關鍵字映射 (從topics_keyword_mapping.json提取)
        self.basic_keyword_mappings = {
            "APPLE": ["apple", "aapl", "蘋果", "庫克", "iphone", "mac"],
            "TSMC": ["tsmc", "taiwan semiconductor", "台積電", "晶圓"],
            "TESLA": ["tesla", "tsla", "特斯拉", "馬斯克", "elon musk"],
            "AI_TECH": ["ai", "artificial intelligence", "人工智慧", "machine learning", "機器學習", "chatgpt", "openai"],
            "CRYPTO": ["bitcoin", "crypto", "cryptocurrency", "blockchain", "比特幣", "加密貨幣", "區塊鏈"],
            "STOCK_MARKET": ["stock", "market", "dow", "nasdaq", "s&p", "股市", "股票", "道瓊", "納斯達克"],
            "ECONOMIES": ["economy", "gdp", "recession", "unemployment", "經濟", "失業率", "衰退", "成長"],
            "EARNINGS": ["earnings", "revenue", "profit", "quarterly", "財報", "營收", "獲利", "季報"],
            "TECH": ["technology", "tech", "科技", "科技股", "semiconductor", "半導體"],
            "ELECTRIC_VEHICLES": ["electric vehicle", "ev", "電動車", "新能源車", "充電"],
            "FEDERAL_RESERVE": ["federal reserve", "fed", "interest rate", "聯準會", "央行", "利率"],
            "HOUSING": ["housing", "real estate", "mortgage", "房地產", "房價", "房貸"],
            "ENERGY": ["energy", "oil", "gas", "renewable", "能源", "石油", "天然氣", "再生能源"],
            "HEALTHCARE": ["healthcare", "pharma", "medical", "醫療", "製藥", "生技"],
            "FINANCE": ["finance", "banking", "金融", "銀行", "保險"],
            "TARIFFS": ["tariff", "關稅", "貿易戰"],
            "TRADE": ["trade", "import", "export", "貿易", "進口", "出口"],
            "COMMODITIES": ["commodities", "gold", "silver", "商品", "黃金", "白銀"],
            "BONDS": ["bonds", "treasury", "yield", "債券", "公債", "殖利率"]
        }
    
    def check_database_status(self) -> Dict[str, Any]:
        """檢查資料庫當前狀態"""
        try:
            # 檢查tags表
            tags_result = db_manager.supabase.table("tags").select("*").execute()
            existing_tags = tags_result.data if tags_result.data else []
            
            # 檢查keyword_mappings表
            mappings_result = db_manager.supabase.table("keyword_mappings").select("*").execute()
            existing_mappings = mappings_result.data if mappings_result.data else []
            
            status = {
                "tags_count": len(existing_tags),
                "existing_tags": [tag["tag_code"] for tag in existing_tags],
                "mappings_count": len(existing_mappings),
                "needs_migration": len(existing_tags) == 0 or len(existing_mappings) == 0
            }
            
            print(f"[Database Status] Tags: {status['tags_count']}, Mappings: {status['mappings_count']}")
            return status
            
        except Exception as e:
            print(f"[ERROR] Failed to check database status: {e}")
            return {"error": str(e), "needs_migration": True}
    
    def migrate_tags_to_database(self) -> bool:
        """將硬編碼標籤遷移到資料庫"""
        try:
            print("=== 開始標籤資料庫遷移 ===")
            
            # 準備標籤數據
            tags_data = []
            for tag_code in self.current_hardcoded_tags:
                translation = self.tag_translations.get(tag_code, {})
                
                tag_data = {
                    "tag_code": tag_code,
                    "tag_name_zh": translation.get("zh", tag_code),
                    "tag_name_en": translation.get("en", tag_code),
                    "priority": translation.get("priority", 100),
                    "is_active": True
                }
                tags_data.append(tag_data)
            
            # 批量插入標籤
            result = db_manager.supabase.table("tags").upsert(
                tags_data, 
                on_conflict="tag_code"
            ).execute()
            
            print(f"[SUCCESS] Migrated {len(result.data)} tags to database")
            return True
            
        except Exception as e:
            print(f"[ERROR] Tag migration failed: {e}")
            return False
    
    def migrate_keyword_mappings(self) -> bool:
        """將關鍵字映射遷移到資料庫"""
        try:
            print("=== 開始關鍵字映射遷移 ===")
            
            # 獲取標籤ID映射
            tags_result = db_manager.supabase.table("tags").select("id, tag_code").execute()
            tag_id_map = {tag["tag_code"]: tag["id"] for tag in tags_result.data}
            
            # 準備關鍵字映射數據
            mappings_data = []
            for tag_code, keywords in self.basic_keyword_mappings.items():
                if tag_code not in tag_id_map:
                    continue
                
                tag_id = tag_id_map[tag_code]
                
                for keyword in keywords:
                    # 判斷語言
                    language = "zh" if any('\u4e00' <= char <= '\u9fff' for char in keyword) else "en"
                    
                    mapping_data = {
                        "tag_id": tag_id,
                        "keyword": keyword,
                        "language": language,
                        "mapping_type": "system_migration",
                        "confidence": 1.0,
                        "match_method": "exact",
                        "is_active": True
                    }
                    mappings_data.append(mapping_data)
            
            # 批量插入映射
            result = db_manager.supabase.table("keyword_mappings").upsert(
                mappings_data,
                on_conflict="tag_id,keyword"
            ).execute()
            
            print(f"[SUCCESS] Migrated {len(result.data)} keyword mappings to database")
            return True
            
        except Exception as e:
            print(f"[ERROR] Keyword mapping migration failed: {e}")
            return False
    
    def create_tag_sync_script(self) -> str:
        """生成標籤同步腳本"""
        script_content = '''#!/usr/bin/env python3
"""
動態標籤獲取腳本 - 替換硬編碼標籤
由統一標籤管理系統自動生成
"""

import sys
from pathlib import Path
from typing import List, Optional

# 添加項目根目錄
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.tag_manager import tag_manager

def get_active_tags() -> List[str]:
    """從資料庫獲取活躍標籤列表"""
    try:
        tags = tag_manager.get_all_active_tags()
        return [tag.tag_code for tag in tags]
    except Exception as e:
        print(f"[WARNING] Failed to load tags from database: {e}")
        # 降級到備用標籤
        return [
            "APPLE", "TSMC", "TESLA", "AI_TECH", "CRYPTO",
            "STOCK_MARKET", "ECONOMIES", "LATEST", "EARNINGS", 
            "TECH", "ELECTRIC_VEHICLES", "FEDERAL_RESERVE"
        ]

def get_tags_for_scraper() -> List[str]:
    """為爬蟲提供標籤列表"""
    return get_active_tags()

def get_tags_for_pusher() -> List[str]:
    """為推送系統提供標籤列表"""
    return get_active_tags()

# 向後兼容
core_tags = get_active_tags()
'''
        return script_content
    
    def run_full_migration(self) -> bool:
        """執行完整遷移流程"""
        print("[START] 開始統一標籤管理系統遷移")
        print("=" * 60)
        
        # 步驟1: 檢查資料庫狀態
        status = self.check_database_status()
        if "error" in status:
            print(f"❌ 資料庫檢查失敗: {status['error']}")
            return False
        
        # 步驟2: 遷移標籤
        if not self.migrate_tags_to_database():
            print("❌ 標籤遷移失敗")
            return False
        
        # 步驟3: 遷移關鍵字映射
        if not self.migrate_keyword_mappings():
            print("❌ 關鍵字映射遷移失敗")
            return False
        
        # 步驟4: 生成同步腳本
        script_path = project_root / "scripts" / "dynamic_tags.py"
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(self.create_tag_sync_script())
        print(f"[OK] 生成動態標籤腳本: {script_path}")
        
        print("\n[SUCCESS] 統一標籤管理系統遷移完成！")
        print("接下來需要:")
        print("1. 修改 scraper.py 使用 dynamic_tags.get_tags_for_scraper()")
        print("2. 修改推送系統使用統一標籤管理")
        print("3. 測試驗證新系統")
        
        return True

def main():
    """主執行函數"""
    setup_logging()
    
    migrator = TagMigrationManager()
    success = migrator.run_full_migration()
    
    return 0 if success else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)