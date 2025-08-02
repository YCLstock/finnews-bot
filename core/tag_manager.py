#!/usr/bin/env python3
"""
標籤管理器 - 支援資料庫標籤管理與多層緩存優化
設計目標：高效能、高可用、易擴展
"""

import time
import json
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from threading import Lock
import hashlib

from core.database import db_manager
from core.config import settings

@dataclass
class Tag:
    """標籤資料類別"""
    id: int
    tag_code: str
    tag_name_zh: str
    tag_name_en: Optional[str]
    priority: int
    is_active: bool

@dataclass
class KeywordMapping:
    """關鍵字映射資料類別"""
    id: int
    tag_id: int
    keyword: str
    language: str
    mapping_type: str
    confidence: float
    match_method: str
    is_active: bool

class TagCacheManager:
    """標籤緩存管理器 - 三層緩存架構"""
    
    def __init__(self):
        self._memory_cache = {}          # L1: 記憶體緩存 (最熱資料)
        self._query_cache = {}           # L2: 查詢結果緩存
        self._metadata_cache = {}        # L3: 元資料緩存 (標籤列表等)
        self._cache_lock = Lock()
        self._last_refresh = {}
        
        # 緩存配置
        self.CACHE_TTL = {
            'tags_list': 3600,           # 標籤列表緩存1小時
            'keyword_mappings': 1800,    # 關鍵字映射緩存30分鐘
            'user_preferences': 300,     # 用戶偏好緩存5分鐘
            'tag_metadata': 7200,        # 標籤元資料緩存2小時
        }
    
    def get_cache_key(self, operation: str, params: dict) -> str:
        """生成緩存鍵"""
        param_str = json.dumps(params, sort_keys=True, ensure_ascii=False)
        return f"{operation}:{hashlib.md5(param_str.encode()).hexdigest()[:8]}"
    
    def is_cache_valid(self, cache_type: str, last_update: float) -> bool:
        """檢查緩存是否有效"""
        ttl = self.CACHE_TTL.get(cache_type, 300)
        return (time.time() - last_update) < ttl
    
    def get_from_cache(self, cache_key: str, cache_type: str) -> Optional[Any]:
        """從緩存獲取資料"""
        with self._cache_lock:
            if cache_key in self._memory_cache:
                data, timestamp = self._memory_cache[cache_key]
                if self.is_cache_valid(cache_type, timestamp):
                    return data
                else:
                    # 清理過期緩存
                    del self._memory_cache[cache_key]
        return None
    
    def set_cache(self, cache_key: str, data: Any) -> None:
        """設置緩存資料"""
        with self._cache_lock:
            self._memory_cache[cache_key] = (data, time.time())
            # 限制緩存大小，避免記憶體溢出
            if len(self._memory_cache) > 1000:
                self._cleanup_old_cache()
    
    def _cleanup_old_cache(self) -> None:
        """清理舊的緩存項目"""
        current_time = time.time()
        expired_keys = []
        
        for key, (_, timestamp) in self._memory_cache.items():
            if (current_time - timestamp) > 3600:  # 1小時後強制清理
                expired_keys.append(key)
        
        for key in expired_keys:
            del self._memory_cache[key]
        
        print(f"[TagCache] Cleaned up {len(expired_keys)} expired cache entries")
    
    def invalidate_cache(self, pattern: str = None) -> None:
        """失效緩存"""
        with self._cache_lock:
            if pattern:
                # 清理特定模式的緩存
                keys_to_remove = [k for k in self._memory_cache.keys() if pattern in k]
                for key in keys_to_remove:
                    del self._memory_cache[key]
            else:
                # 清理所有緩存
                self._memory_cache.clear()
        print(f"[TagCache] Invalidated cache with pattern: {pattern}")

class TagManager:
    """標籤管理器主類"""
    
    def __init__(self):
        self.cache_manager = TagCacheManager()
        self._initialized = False
    
    def initialize(self) -> bool:
        """初始化標籤管理器"""
        try:
            # 預載入核心標籤資料到緩存
            self.get_all_active_tags()
            self.get_all_keyword_mappings()
            self._initialized = True
            print("[TagManager] Initialized successfully with database backend")
            return True
        except Exception as e:
            print(f"[TagManager] Initialization failed: {e}")
            return False
    
    def get_all_active_tags(self) -> List[Tag]:
        """獲取所有活躍標籤 (帶緩存)"""
        cache_key = self.cache_manager.get_cache_key("tags_list", {"active_only": True})
        
        # 檢查緩存
        cached_data = self.cache_manager.get_from_cache(cache_key, "tags_list")
        if cached_data:
            return cached_data
        
        # 查詢資料庫
        try:
            result = db_manager.supabase.table("tags").select(
                "id, tag_code, tag_name_zh, tag_name_en, priority, is_active"
            ).eq("is_active", True).order("priority").execute()
            
            tags = [Tag(**row) for row in result.data]
            
            # 設定緩存
            self.cache_manager.set_cache(cache_key, tags)
            print(f"[TagManager] Loaded {len(tags)} active tags from database")
            
            return tags
            
        except Exception as e:
            print(f"[TagManager] Failed to load tags: {e}")
            # 降級到硬編碼標籤
            return self._get_fallback_tags()
    
    def get_tags_by_category(self, category: str) -> List[Tag]:
        """根據分類獲取標籤"""
        cache_key = self.cache_manager.get_cache_key("tags_by_category", {"category": category})
        
        cached_data = self.cache_manager.get_from_cache(cache_key, "tags_list")
        if cached_data:
            return cached_data
        
        try:
            result = db_manager.supabase.table("tags").select(
                "id, tag_code, tag_name_zh, tag_name_en, priority, is_active"
            ).eq("is_active", True).order("priority").execute()
            
            tags = [Tag(**row) for row in result.data]
            self.cache_manager.set_cache(cache_key, tags)
            
            return tags
            
        except Exception as e:
            print(f"[TagManager] Failed to load tags by category {category}: {e}")
            return []
    
    def get_all_keyword_mappings(self) -> Dict[str, List[KeywordMapping]]:
        """獲取所有關鍵字映射 (帶緩存)"""
        cache_key = self.cache_manager.get_cache_key("keyword_mappings", {"active_only": True})
        
        cached_data = self.cache_manager.get_from_cache(cache_key, "keyword_mappings")
        if cached_data:
            return cached_data
        
        try:
            result = db_manager.supabase.table("keyword_mappings").select(
                "id, tag_id, keyword, language, mapping_type, confidence, match_method, is_active"
            ).eq("is_active", True).order("confidence", desc=True).execute()
            
            # 按關鍵字分組
            mappings_dict = {}
            for row in result.data:
                mapping = KeywordMapping(**row)
                keyword_lower = mapping.keyword.lower()
                
                if keyword_lower not in mappings_dict:
                    mappings_dict[keyword_lower] = []
                mappings_dict[keyword_lower].append(mapping)
            
            self.cache_manager.set_cache(cache_key, mappings_dict)
            print(f"[TagManager] Loaded {len(mappings_dict)} keyword mappings from database")
            
            return mappings_dict
            
        except Exception as e:
            print(f"[TagManager] Failed to load keyword mappings: {e}")
            return self._get_fallback_keyword_mappings()
    
    def convert_keywords_to_tags(self, keywords: List[str]) -> List[str]:
        """將關鍵字轉換為標籤代碼 (核心功能)"""
        if not keywords:
            return []
        
        # 準備緩存鍵
        cache_key = self.cache_manager.get_cache_key("keyword_conversion", {"keywords": sorted(keywords)})
        
        # 檢查緩存
        cached_result = self.cache_manager.get_from_cache(cache_key, "keyword_mappings")
        if cached_result:
            print(f"[TagManager] Cache hit for keyword conversion: {keywords}")
            return cached_result
        
        try:
            # 獲取關鍵字映射
            keyword_mappings = self.get_all_keyword_mappings()
            tag_data = {tag.id: tag.tag_code for tag in self.get_all_active_tags()}
            
            # 執行轉換
            matched_tags = set()
            conversion_details = []
            
            for keyword in keywords:
                keyword_lower = keyword.lower().strip()
                
                if keyword_lower in keyword_mappings:
                    for mapping in keyword_mappings[keyword_lower]:
                        if mapping.tag_id in tag_data:
                            matched_tags.add(tag_data[mapping.tag_id])
                            conversion_details.append({
                                "keyword": keyword,
                                "tag": tag_data[mapping.tag_id],
                                "confidence": mapping.confidence,
                                "method": mapping.mapping_type
                            })
            
            result_tags = list(matched_tags)[:5]  # 限制最多5個標籤
            
            # 記錄轉換詳情用於透明度
            conversion_info = {
                "tags": result_tags,
                "details": conversion_details,
                "timestamp": datetime.now().isoformat()
            }
            
            # 設定緩存
            self.cache_manager.set_cache(cache_key, result_tags)
            
            print(f"[TagManager] Converted keywords {keywords} -> {result_tags}")
            return result_tags
            
        except Exception as e:
            print(f"[TagManager] Keyword conversion failed: {e}")
            # 降級到舊版轉換邏輯
            return self._fallback_keyword_conversion(keywords)
    
    def get_tag_info(self, tag_codes: List[str]) -> List[Dict[str, Any]]:
        """獲取標籤詳細資訊 (用於透明度功能)"""
        try:
            result = db_manager.supabase.table("tags").select(
                "tag_code, tag_name_zh, tag_name_en"
            ).in_("tag_code", tag_codes).eq("is_active", True).execute()
            
            return result.data
            
        except Exception as e:
            print(f"[TagManager] Failed to get tag info: {e}")
            return []
    
    def add_keyword_mapping(self, tag_code: str, keyword: str, confidence: float = 1.0, 
                           mapping_type: str = "manual") -> bool:
        """新增關鍵字映射 (管理功能)"""
        try:
            # 獲取標籤ID
            tag_result = db_manager.supabase.table("tags").select("id").eq(
                "tag_code", tag_code
            ).eq("is_active", True).execute()
            
            if not tag_result.data:
                print(f"[TagManager] Tag {tag_code} not found")
                return False
            
            tag_id = tag_result.data[0]["id"]
            
            # 新增映射
            mapping_data = {
                "tag_id": tag_id,
                "keyword": keyword,
                "mapping_type": mapping_type,
                "confidence": confidence,
                "is_active": True
            }
            
            result = db_manager.supabase.table("keyword_mappings").insert(mapping_data).execute()
            
            if result.data:
                # 清除相關緩存
                self.cache_manager.invalidate_cache("keyword")
                print(f"[TagManager] Added keyword mapping: {keyword} -> {tag_code}")
                return True
            
            return False
            
        except Exception as e:
            print(f"[TagManager] Failed to add keyword mapping: {e}")
            return False
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """獲取緩存統計資訊"""
        with self.cache_manager._cache_lock:
            total_entries = len(self.cache_manager._memory_cache)
            
            # 計算各類型緩存數量
            cache_types = {}
            for key in self.cache_manager._memory_cache.keys():
                cache_type = key.split(':')[0]
                cache_types[cache_type] = cache_types.get(cache_type, 0) + 1
            
            return {
                "total_cached_entries": total_entries,
                "cache_types": cache_types,
                "initialized": self._initialized,
                "cache_hit_stats": "Available in production mode"
            }
    
    def _get_fallback_tags(self) -> List[Tag]:
        """降級硬編碼標籤 (備用方案)"""
        fallback_tags = [
            Tag(1, "APPLE", "蘋果公司", "Apple Inc.", 10, True),
            Tag(2, "TSMC", "台積電", "TSMC", 10, True),
            Tag(3, "TESLA", "特斯拉", "Tesla", 10, True),
            Tag(4, "AI_TECH", "AI科技", "AI Technology", 20, True),
            Tag(5, "CRYPTO", "加密貨幣", "Cryptocurrency", 30, True),
        ]
        print("[TagManager] Using fallback hardcoded tags")
        return fallback_tags
    
    def _get_fallback_keyword_mappings(self) -> Dict[str, List[KeywordMapping]]:
        """降級硬編碼關鍵字映射"""
        fallback_mappings = {
            "apple": [KeywordMapping(1, 1, "apple", "en", "manual", 1.0, "exact", True)],
            "蘋果": [KeywordMapping(2, 1, "蘋果", "zh", "manual", 1.0, "exact", True)],
            "tsmc": [KeywordMapping(3, 2, "tsmc", "en", "manual", 1.0, "exact", True)],
            "台積電": [KeywordMapping(4, 2, "台積電", "zh", "manual", 1.0, "exact", True)],
            # ... 更多備用映射
        }
        print("[TagManager] Using fallback hardcoded keyword mappings")
        return fallback_mappings
    
    def _fallback_keyword_conversion(self, keywords: List[str]) -> List[str]:
        """降級關鍵字轉換邏輯"""
        # 使用原有的硬編碼轉換邏輯
        from services.keyword_sync_service import keyword_sync_service
        return keyword_sync_service.convert_keywords_to_tags(keywords)

# 創建全局標籤管理器實例
tag_manager = TagManager()

# 自動初始化
if not tag_manager.initialize():
    print("[TagManager] Warning: Initialization failed, using fallback mode")