#!/usr/bin/env python3
"""
標籤管理API端點 - 提供透明度和用戶控制功能
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, validator
from datetime import datetime

from api.auth import get_current_user_id
from core.tag_manager import tag_manager
from core.database import db_manager

router = APIRouter(prefix="/tags", tags=["tags"])

# Pydantic 模型定義

class TagInfo(BaseModel):
    """標籤資訊模型"""
    tag_code: str
    tag_name_zh: str
    tag_name_en: Optional[str]
    category: str
    description: Optional[str]
    color_code: str

class KeywordConversion(BaseModel):
    """關鍵字轉換結果模型"""
    keyword: str
    matched_tags: List[str]
    confidence_details: List[Dict[str, Any]]
    conversion_method: str

class TagPreviewResponse(BaseModel):
    """標籤預覽回應模型"""
    conversions: List[KeywordConversion]
    total_matched_tags: List[str]
    preview_generated_at: str

class UserTagPreference(BaseModel):
    """用戶標籤偏好模型"""
    tag_code: str
    weight: float = 1.0
    is_blocked: bool = False

class MatchExplanation(BaseModel):
    """匹配解釋模型"""
    article_title: str
    matched_tags: List[str]
    match_reasons: List[Dict[str, Any]]
    relevance_score: float

# API端點實作

@router.get("/", response_model=List[TagInfo])
async def get_all_tags():
    """
    獲取所有可用標籤
    用於前端標籤選擇和用戶了解
    """
    try:
        tags = tag_manager.get_all_active_tags()
        
        tag_info_list = []
        for tag in tags:
            tag_info_list.append(TagInfo(
                tag_code=tag.tag_code,
                tag_name_zh=tag.tag_name_zh,
                tag_name_en=tag.tag_name_en,
                category=tag.category,
                description=tag.description,
                color_code=tag.color_code
            ))
        
        return tag_info_list
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get tags: {str(e)}")

@router.get("/categories")
async def get_tag_categories():
    """獲取標籤分類"""
    try:
        result = db_manager.supabase.table("tag_categories").select(
            "category_code, category_name_zh, category_name_en, description, icon"
        ).eq("is_active", True).order("sort_order").execute()
        
        return {"categories": result.data}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get categories: {str(e)}")

@router.get("/preview")
async def preview_keyword_conversion(
    keywords: str = Query(..., description="Comma-separated keywords to preview"),
    current_user_id: str = Depends(get_current_user_id)
):
    """
    預覽關鍵字轉換結果
    核心透明度功能 - 讓用戶了解關鍵字將如何轉換
    """
    try:
        # 解析關鍵字
        keyword_list = [kw.strip() for kw in keywords.split(',') if kw.strip()]
        
        if not keyword_list:
            raise HTTPException(status_code=400, detail="No valid keywords provided")
        
        # 獲取關鍵字映射
        keyword_mappings = tag_manager.get_all_keyword_mappings()
        all_tags = {tag.id: tag for tag in tag_manager.get_all_active_tags()}
        
        conversions = []
        all_matched_tags = set()
        
        for keyword in keyword_list:
            keyword_lower = keyword.lower().strip()
            matched_tags = []
            confidence_details = []
            
            if keyword_lower in keyword_mappings:
                for mapping in keyword_mappings[keyword_lower]:
                    if mapping.tag_id in all_tags:
                        tag = all_tags[mapping.tag_id]
                        matched_tags.append(tag.tag_code)
                        all_matched_tags.add(tag.tag_code)
                        
                        confidence_details.append({
                            "tag_code": tag.tag_code,
                            "tag_name": tag.tag_name_zh,
                            "confidence": mapping.confidence,
                            "mapping_type": mapping.mapping_type,
                            "match_method": mapping.match_method
                        })
            
            # 如果沒有直接匹配，嘗試AI轉換預覽
            if not matched_tags:
                # 這裡可以調用AI進行即時轉換預覽
                ai_tags = tag_manager._ai_preview_conversion([keyword])  # 需要實作
                for tag_code in ai_tags:
                    matched_tags.append(tag_code)
                    all_matched_tags.add(tag_code)
                    confidence_details.append({
                        "tag_code": tag_code,
                        "tag_name": next((t.tag_name_zh for t in all_tags.values() if t.tag_code == tag_code), tag_code),
                        "confidence": 0.8,  # AI預估信心度
                        "mapping_type": "ai_preview",
                        "match_method": "semantic"
                    })
            
            conversions.append(KeywordConversion(
                keyword=keyword,
                matched_tags=matched_tags,
                confidence_details=confidence_details,
                conversion_method="database_lookup" if matched_tags else "no_match"
            ))
        
        return TagPreviewResponse(
            conversions=conversions,
            total_matched_tags=list(all_matched_tags),
            preview_generated_at=datetime.now().isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Preview failed: {str(e)}")

@router.get("/preferences", response_model=List[UserTagPreference])
async def get_user_tag_preferences(current_user_id: str = Depends(get_current_user_id)):
    """獲取用戶標籤偏好設定"""
    try:
        result = db_manager.supabase.table("user_tag_preferences").select(
            "tag_id, weight, is_blocked, tags(tag_code)"
        ).eq("user_id", current_user_id).execute()
        
        preferences = []
        for row in result.data:
            if row.get("tags"):
                preferences.append(UserTagPreference(
                    tag_code=row["tags"]["tag_code"],
                    weight=row["weight"],
                    is_blocked=row["is_blocked"]
                ))
        
        return preferences
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get preferences: {str(e)}")

@router.post("/preferences")
async def update_user_tag_preferences(
    preferences: List[UserTagPreference],
    current_user_id: str = Depends(get_current_user_id)
):
    """更新用戶標籤偏好"""
    try:
        # 獲取標籤ID映射
        tags_result = db_manager.supabase.table("tags").select("id, tag_code").execute()
        tag_code_to_id = {row["tag_code"]: row["id"] for row in tags_result.data}
        
        # 準備更新資料
        preference_data = []
        for pref in preferences:
            if pref.tag_code in tag_code_to_id:
                preference_data.append({
                    "user_id": current_user_id,
                    "tag_id": tag_code_to_id[pref.tag_code],
                    "weight": pref.weight,
                    "is_blocked": pref.is_blocked,
                    "updated_at": datetime.now().isoformat()
                })
        
        if preference_data:
            # 使用 UPSERT 更新偏好
            result = db_manager.supabase.table("user_tag_preferences").upsert(
                preference_data
            ).execute()
            
            return {"message": f"Updated {len(preference_data)} tag preferences", "updated_count": len(result.data)}
        else:
            return {"message": "No valid preferences to update", "updated_count": 0}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update preferences: {str(e)}")

@router.get("/explain-match")
async def explain_article_match(
    article_id: int = Query(..., description="Article ID to explain"),
    current_user_id: str = Depends(get_current_user_id)
):
    """
    解釋文章匹配原因
    透明度功能 - 解釋為什麼這篇文章被推送給用戶
    """
    try:
        # 獲取文章資訊
        article_result = db_manager.supabase.table("news_articles").select(
            "id, title, summary, original_url"
        ).eq("id", article_id).execute()
        
        if not article_result.data:
            raise HTTPException(status_code=404, detail="Article not found")
        
        article = article_result.data[0]
        
        # 獲取文章標籤
        article_tags_result = db_manager.supabase.table("article_tags").select(
            "tag_id, confidence, source, tags(tag_code, tag_name_zh)"
        ).eq("article_id", article_id).execute()
        
        article_tags = [
            {
                "tag_code": row["tags"]["tag_code"],
                "tag_name": row["tags"]["tag_name_zh"],
                "confidence": row["confidence"],
                "source": row["source"]
            }
            for row in article_tags_result.data if row.get("tags")
        ]
        
        # 獲取用戶訂閱標籤
        user_subscription = db_manager.get_subscription_by_user(current_user_id)
        if not user_subscription:
            raise HTTPException(status_code=404, detail="User subscription not found")
        
        user_tags = user_subscription.get("subscribed_tags", [])
        user_keywords = user_subscription.get("keywords", [])
        
        # 分析匹配原因
        match_reasons = []
        matched_tags = []
        
        # 1. 標籤匹配
        for article_tag in article_tags:
            if article_tag["tag_code"] in user_tags:
                matched_tags.append(article_tag["tag_code"])
                match_reasons.append({
                    "type": "tag_match",
                    "description": f"文章標籤 '{article_tag['tag_name']}' 符合您的訂閱偏好",
                    "tag_code": article_tag["tag_code"],
                    "confidence": article_tag["confidence"],
                    "source": article_tag["source"]
                })
        
        # 2. 關鍵字匹配
        for keyword in user_keywords:
            if keyword.lower() in article["title"].lower() or keyword.lower() in article["summary"].lower():
                match_reasons.append({
                    "type": "keyword_match",
                    "description": f"文章內容包含您的關鍵字 '{keyword}'",
                    "keyword": keyword,
                    "found_in": "title" if keyword.lower() in article["title"].lower() else "summary"
                })
        
        # 計算相關性分數
        relevance_score = min(1.0, len(match_reasons) * 0.3 + sum(
            reason.get("confidence", 0.5) for reason in match_reasons if "confidence" in reason
        ) / max(1, len([r for r in match_reasons if "confidence" in r])))
        
        return MatchExplanation(
            article_title=article["title"],
            matched_tags=matched_tags,
            match_reasons=match_reasons,
            relevance_score=round(relevance_score, 2)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to explain match: {str(e)}")

@router.get("/stats")
async def get_tag_stats(current_user_id: str = Depends(get_current_user_id)):
    """獲取用戶標籤統計資訊"""
    try:
        # 獲取用戶推送歷史中的標籤統計
        history_result = db_manager.supabase.table("push_history").select(
            "article_id, news_articles(id), article_tags(tag_id, tags(tag_code, tag_name_zh))"
        ).eq("user_id", current_user_id).limit(100).execute()
        
        # 統計標籤頻率
        tag_stats = {}
        for record in history_result.data:
            if record.get("news_articles") and record["news_articles"].get("article_tags"):
                for article_tag in record["news_articles"]["article_tags"]:
                    if article_tag.get("tags"):
                        tag_code = article_tag["tags"]["tag_code"]
                        tag_name = article_tag["tags"]["tag_name_zh"]
                        
                        if tag_code not in tag_stats:
                            tag_stats[tag_code] = {
                                "tag_code": tag_code,
                                "tag_name": tag_name,
                                "push_count": 0,
                                "last_pushed": None
                            }
                        
                        tag_stats[tag_code]["push_count"] += 1
        
        # 排序並返回
        sorted_stats = sorted(tag_stats.values(), key=lambda x: x["push_count"], reverse=True)
        
        return {
            "user_tag_statistics": sorted_stats,
            "total_unique_tags": len(tag_stats),
            "analysis_period": "Last 100 pushes"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get tag stats: {str(e)}")

@router.get("/cache-stats")
async def get_cache_stats():
    """獲取標籤管理器緩存統計 (系統監控用)"""
    try:
        stats = tag_manager.get_cache_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get cache stats: {str(e)}")

# 管理員功能 (需要管理權限)

@router.post("/admin/add-keyword")
async def add_keyword_mapping(
    tag_code: str,
    keyword: str,
    confidence: float = 1.0,
    mapping_type: str = "manual",
    current_user_id: str = Depends(get_current_user_id)  # 這裡應該改為管理員權限檢查
):
    """新增關鍵字映射 (管理員功能)"""
    try:
        success = tag_manager.add_keyword_mapping(
            tag_code=tag_code,
            keyword=keyword,
            confidence=confidence,
            mapping_type=mapping_type
        )
        
        if success:
            return {"message": f"Added keyword mapping: {keyword} -> {tag_code}"}
        else:
            raise HTTPException(status_code=400, detail="Failed to add keyword mapping")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add keyword: {str(e)}")