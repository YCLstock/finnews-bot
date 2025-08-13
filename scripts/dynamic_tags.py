#!/usr/bin/env python3
"""
動態標籤獲取腳本 - 統一標籤管理系統
支援從資料庫動態獲取標籤，帶降級保護機制
"""

import sys
from pathlib import Path
from typing import List, Optional

# 添加項目根目錄
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

class DynamicTagManager:
    """動態標籤管理器"""
    
    def __init__(self):
        # 備用硬編碼標籤 (與當前系統一致)
        self.fallback_tags = [
            "APPLE", "TSMC", "TESLA", "AI_TECH", "CRYPTO",
            "STOCK_MARKET", "ECONOMIES", "LATEST", "EARNINGS", 
            "TECH", "ELECTRIC_VEHICLES", "FEDERAL_RESERVE",
            "HOUSING", "ENERGY", "HEALTHCARE", "FINANCE",
            "TARIFFS", "TRADE", "COMMODITIES", "BONDS"
        ]
        
        # 關鍵字到標籤的映射 (統一topics_mapper的功能)
        self.keyword_to_tag_mapping = {
            # 科技公司
            "蘋果": ["APPLE", "TECH"],
            "apple": ["APPLE", "TECH"],
            "特斯拉": ["TESLA", "ELECTRIC_VEHICLES", "TECH"],
            "tesla": ["TESLA", "ELECTRIC_VEHICLES", "TECH"],
            "台積電": ["TSMC", "TECH"],
            "tsmc": ["TSMC", "TECH"],
            
            # AI與科技
            "ai": ["AI_TECH", "TECH"],
            "人工智慧": ["AI_TECH", "TECH"],
            "科技": ["TECH"],
            "technology": ["TECH"],
            
            # 加密貨幣
            "比特幣": ["CRYPTO"],
            "bitcoin": ["CRYPTO"],
            "加密貨幣": ["CRYPTO"],
            "crypto": ["CRYPTO"],
            "區塊鏈": ["CRYPTO"],
            
            # 市場與經濟
            "股市": ["STOCK_MARKET"],
            "股票": ["STOCK_MARKET"],
            "市場": ["STOCK_MARKET"],
            "經濟": ["ECONOMIES"],
            "央行": ["FEDERAL_RESERVE", "ECONOMIES"],
            "聯準會": ["FEDERAL_RESERVE", "ECONOMIES"],
            "美聯儲": ["FEDERAL_RESERVE", "ECONOMIES"],
            
            # 其他主題
            "財報": ["EARNINGS"],
            "earnings": ["EARNINGS"],
            "房地產": ["HOUSING"],
            "energy": ["ENERGY"],
            "能源": ["ENERGY"],
            "醫療": ["HEALTHCARE"],
            "金融": ["FINANCE"],
            "貿易": ["TRADE", "TARIFFS"],
            "關稅": ["TARIFFS"],
            "債券": ["BONDS"],
            "商品": ["COMMODITIES"],
            "最新": ["LATEST"],
            "消息": ["LATEST"]
        }
        
        self._cache = None
        self._last_update = None
    
    def get_active_tags_from_database(self) -> Optional[List[str]]:
        """從資料庫獲取活躍標籤"""
        try:
            from core.tag_manager import tag_manager
            
            if tag_manager._initialized or tag_manager.initialize():
                tags = tag_manager.get_all_active_tags()
                return [tag.tag_code for tag in tags]
            else:
                return None
                
        except Exception as e:
            print(f"[WARNING] Database tag loading failed: {e}")
            return None
    
    def get_active_tags(self) -> List[str]:
        """獲取活躍標籤列表 - 帶降級保護"""
        try:
            # 嘗試從資料庫獲取
            db_tags = self.get_active_tags_from_database()
            if db_tags and len(db_tags) > 0:
                print(f"[TagManager] Loaded {len(db_tags)} tags from database")
                return db_tags
            
            # 降級到備用標籤
            print(f"[TagManager] Using fallback tags ({len(self.fallback_tags)} tags)")
            return self.fallback_tags.copy()
            
        except Exception as e:
            print(f"[ERROR] All tag loading methods failed: {e}")
            return self.fallback_tags.copy()
    
    def convert_keywords_to_tags(self, keywords: List[str]) -> List[str]:
        """將用戶關鍵字轉換為標籤 - 統一topics_mapper功能"""
        if not keywords:
            return []
        
        matched_tags = set()
        
        for keyword in keywords:
            keyword_lower = keyword.lower().strip()
            
            # 嘗試精確匹配
            if keyword_lower in self.keyword_to_tag_mapping:
                matched_tags.update(self.keyword_to_tag_mapping[keyword_lower])
            
            # 嘗試部分匹配
            for mapping_key, tags in self.keyword_to_tag_mapping.items():
                if keyword_lower in mapping_key or mapping_key in keyword_lower:
                    matched_tags.update(tags)
        
        # 如果沒有匹配到任何標籤，返回通用標籤
        result_tags = list(matched_tags)[:5] if matched_tags else ["LATEST"]
        
        print(f"[TagMapper] Keywords {keywords} -> Tags {result_tags}")
        return result_tags

# 全域標籤管理器實例
_tag_manager = DynamicTagManager()

def get_tags_for_scraper() -> List[str]:
    """為爬蟲系統提供標籤列表"""
    return _tag_manager.get_active_tags()

def get_tags_for_pusher() -> List[str]:
    """為推送系統提供標籤列表"""
    return _tag_manager.get_active_tags()

def get_active_tags() -> List[str]:
    """通用標籤獲取接口"""
    return _tag_manager.get_active_tags()

def convert_keywords_to_tags(keywords: List[str]) -> List[str]:
    """統一關鍵字轉換接口 - 替代topics_mapper"""
    return _tag_manager.convert_keywords_to_tags(keywords)

def map_keywords_to_topics(keywords: List[str]) -> List[tuple]:
    """兼容topics_mapper.map_keywords_to_topics接口"""
    tags = convert_keywords_to_tags(keywords)
    # 返回 (tag, confidence) 元組列表，與原接口兼容
    return [(tag, 1.0) for tag in tags]

# 向後兼容 - 替代原有硬編碼
core_tags = get_active_tags()

if __name__ == "__main__":
    # 測試腳本
    print("=== 動態標籤管理器測試 ===")
    tags = get_active_tags()
    print(f"獲取到 {len(tags)} 個標籤:")
    for i, tag in enumerate(tags, 1):
        print(f"  {i}. {tag}")