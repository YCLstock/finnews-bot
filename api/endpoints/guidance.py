#!/usr/bin/env python3
"""
用戶引導與語義聚類API端點
提供用戶教育引導和關鍵字優化功能
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Body
from pydantic import BaseModel, validator
from datetime import datetime

from api.auth import get_current_user_id
from core.user_guidance import get_guidance_instance
from core.semantic_clustering import get_clustering_instance
from core.enhanced_topics_mapper import get_enhanced_mapper_instance
from core.database import db_manager

router = APIRouter(prefix="/guidance", tags=["guidance"])

# 取得全域實例
guidance_system = get_guidance_instance()
clustering_system = get_clustering_instance()
enhanced_mapper = get_enhanced_mapper_instance()

# Pydantic 模型定義

class OnboardingStartResponse(BaseModel):
    """引導開始回應模型"""
    user_id: str
    step: str
    progress: int
    total_steps: int
    content: Dict[str, Any]
    next_action: str

class InvestmentFocusRequest(BaseModel):
    """投資領域選擇請求模型"""
    selected_options: List[str]
    
    @validator('selected_options')
    def validate_options(cls, v):
        if len(v) > 3:
            raise ValueError('最多只能選擇3個投資領域')
        return v

class InvestmentFocusResponse(BaseModel):
    """投資領域選擇回應模型"""
    status: str
    step: str
    progress: int
    recommended_keywords: List[str]
    recommended_topics: List[str]
    selected_focus: List[Dict[str, Any]]
    customization_template: Dict[str, Any]
    message: Optional[str] = None

class KeywordAnalysisRequest(BaseModel):
    """關鍵字分析請求模型"""
    keywords: List[str]
    
    @validator('keywords')
    def validate_keywords(cls, v):
        if len(v) == 0:
            raise ValueError('請提供至少一個關鍵字')
        if len(v) > 10:
            raise ValueError('關鍵字數量不能超過10個')
        return v

class KeywordAnalysisResponse(BaseModel):
    """關鍵字分析回應模型"""
    user_id: str
    original_keywords: List[str]
    clustering_result: Dict[str, Any]
    guidance: Dict[str, Any]
    timestamp: str

class OnboardingFinalizationRequest(BaseModel):
    """引導完成請求模型"""
    final_keywords: List[str]
    
    @validator('final_keywords')
    def validate_final_keywords(cls, v):
        if len(v) < 2:
            raise ValueError('建議至少選擇2個關鍵字')
        if len(v) > 8:
            raise ValueError('關鍵字數量不能超過8個')
        return v

class OnboardingCompletionResponse(BaseModel):
    """引導完成回應模型"""
    status: str
    step: str
    progress: int
    user_id: str
    final_keywords: List[str]
    analysis: Dict[str, Any]
    message: str
    next_steps: List[str]

class OptimizationSuggestionResponse(BaseModel):
    """優化建議回應模型"""
    user_id: str
    current_focus_score: float
    optimization_priority: str
    user_experience_score: float
    guidance_suggestions: Dict[str, Any]
    auto_optimization: Dict[str, Any]
    recommended_actions: List[Dict[str, Any]]

class ClusteringAnalysisResponse(BaseModel):
    """聚類分析回應模型"""
    clusters: List[List[str]]
    focus_score: float
    primary_topics: List[str]
    suggestions: Dict[str, Any]
    method: str

# API端點實作

@router.get("/status")
async def get_guidance_status(current_user_id: str = Depends(get_current_user_id)):
    """
    檢查用戶引導狀態
    """
    try:
        subscription = db_manager.get_subscription_by_user(current_user_id)
        
        if not subscription:
            return {
                "has_subscription": False,
                "guidance_completed": False,
                "needs_guidance": True,
                "focus_score": 0.0,
                "last_guidance_at": None
            }
        
        return {
            "has_subscription": True,
            "guidance_completed": subscription.get("guidance_completed", False),
            "needs_guidance": not subscription.get("guidance_completed", False),
            "focus_score": subscription.get("focus_score", 0.0),
            "last_guidance_at": subscription.get("last_guidance_at"),
            "clustering_enabled": subscription.get("clustering_enabled", True)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get guidance status: {str(e)}")

@router.post("/start-onboarding", response_model=OnboardingStartResponse)
async def start_onboarding(current_user_id: str = Depends(get_current_user_id)):
    """
    開始用戶引導流程
    """
    try:
        result = guidance_system.start_user_onboarding(current_user_id)
        return OnboardingStartResponse(**result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start onboarding: {str(e)}")

@router.post("/investment-focus", response_model=InvestmentFocusResponse)
async def process_investment_focus(
    request: InvestmentFocusRequest,
    current_user_id: str = Depends(get_current_user_id)
):
    """
    處理投資領域選擇
    """
    try:
        result = guidance_system.process_investment_focus_selection(
            current_user_id, 
            request.selected_options
        )
        return InvestmentFocusResponse(**result)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process investment focus: {str(e)}")

@router.post("/analyze-keywords", response_model=KeywordAnalysisResponse)
async def analyze_keywords(
    request: KeywordAnalysisRequest,
    current_user_id: str = Depends(get_current_user_id)
):
    """
    分析用戶關鍵字並提供建議
    """
    try:
        result = guidance_system.analyze_user_keywords(current_user_id, request.keywords)
        return KeywordAnalysisResponse(**result)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze keywords: {str(e)}")

@router.post("/finalize-onboarding", response_model=OnboardingCompletionResponse)
async def finalize_onboarding(
    request: OnboardingFinalizationRequest,
    current_user_id: str = Depends(get_current_user_id)
):
    """
    完成用戶引導流程
    """
    try:
        # 完成引導
        result = guidance_system.finalize_onboarding(current_user_id, request.final_keywords)
        
        # 更新用戶訂閱
        focus_score = result['analysis'].get('clustering_result', {}).get('focus_score', 0.5)
        primary_topics = result['analysis'].get('clustering_result', {}).get('primary_topics', [])
        
        # 獲取或創建訂閱
        subscription = db_manager.get_subscription_by_user(current_user_id)
        if subscription:
            # 更新現有訂閱
            update_success = db_manager.update_subscription_with_enhanced_data(
                current_user_id, 
                request.final_keywords, 
                focus_score, 
                primary_topics
            )
            if not update_success:
                raise HTTPException(status_code=500, detail="Failed to update subscription")
        else:
            # 創建新訂閱
            subscription_data = {
                "user_id": current_user_id,
                "keywords": request.final_keywords,
                "focus_score": focus_score,
                "guidance_completed": True,
                "clustering_enabled": True,
                "is_active": True,
                "push_frequency_type": "daily"
            }
            create_success = db_manager.create_subscription(subscription_data)
            if not create_success:
                raise HTTPException(status_code=500, detail="Failed to create subscription")
        
        return OnboardingCompletionResponse(**result)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to finalize onboarding: {str(e)}")

@router.get("/optimization-suggestions", response_model=OptimizationSuggestionResponse)
async def get_optimization_suggestions(current_user_id: str = Depends(get_current_user_id)):
    """
    為用戶獲取優化建議
    """
    try:
        result = enhanced_mapper.get_optimization_suggestions_for_user(current_user_id)
        
        if 'error' in result:
            raise HTTPException(status_code=404, detail=result['error'])
        
        return OptimizationSuggestionResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get optimization suggestions: {str(e)}")

@router.post("/optimize-existing")
async def optimize_existing_user(current_user_id: str = Depends(get_current_user_id)):
    """
    為現有用戶提供優化建議
    """
    try:
        result = guidance_system.optimize_existing_user(current_user_id)
        
        if 'error' in result:
            raise HTTPException(status_code=404, detail=result['error'])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to optimize existing user: {str(e)}")

@router.post("/clustering-analysis", response_model=ClusteringAnalysisResponse)
async def perform_clustering_analysis(
    request: KeywordAnalysisRequest,
    current_user_id: str = Depends(get_current_user_id)
):
    """
    執行關鍵字語義聚類分析
    """
    try:
        result = clustering_system.cluster_keywords(request.keywords)
        
        # 保存聚類結果到資料庫
        save_success = db_manager.save_keyword_clustering_result(
            current_user_id,
            request.keywords,
            result['clusters'],
            result['focus_score'],
            result['primary_topics'],
            result['method']
        )
        
        if not save_success:
            # 記錄警告但不中斷API回應
            print(f"Warning: Failed to save clustering result for user {current_user_id}")
        
        return ClusteringAnalysisResponse(**result)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to perform clustering analysis: {str(e)}")

@router.get("/enhanced-topics")
async def get_enhanced_topics(current_user_id: str = Depends(get_current_user_id)):
    """
    獲取用戶的增強版Topics推薦
    """
    try:
        subscription = db_manager.get_subscription_by_user(current_user_id)
        
        if not subscription:
            raise HTTPException(status_code=404, detail="User subscription not found")
        
        result = enhanced_mapper.get_topics_for_user_subscription_enhanced(subscription)
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get enhanced topics: {str(e)}")

@router.get("/history")
async def get_guidance_history(
    limit: int = 10,
    current_user_id: str = Depends(get_current_user_id)
):
    """
    獲取用戶的引導歷史記錄
    """
    try:
        guidance_history = db_manager.get_user_guidance_history(current_user_id, limit)
        clustering_history = db_manager.get_user_clustering_history(current_user_id, limit)
        
        return {
            "guidance_history": guidance_history,
            "clustering_history": clustering_history,
            "total_guidance_records": len(guidance_history),
            "total_clustering_records": len(clustering_history)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get guidance history: {str(e)}")

@router.get("/focus-score")
async def get_current_focus_score(current_user_id: str = Depends(get_current_user_id)):
    """
    獲取用戶當前的聚焦度評分
    """
    try:
        subscription = db_manager.get_subscription_by_user(current_user_id)
        
        if not subscription:
            return {
                "has_subscription": False,
                "focus_score": 0.0,
                "clustering_enabled": False
            }
        
        user_keywords = subscription.get("keywords", [])
        if not user_keywords:
            return {
                "has_subscription": True,
                "focus_score": 0.0,
                "clustering_enabled": subscription.get("clustering_enabled", False),
                "needs_keywords": True
            }
        
        # 重新計算聚焦度
        clustering_result = clustering_system.cluster_keywords(user_keywords)
        current_focus_score = clustering_result['focus_score']
        
        # 更新資料庫中的聚焦度
        if current_focus_score != subscription.get("focus_score"):
            db_manager.update_user_guidance_status(
                current_user_id, 
                focus_score=current_focus_score
            )
        
        return {
            "has_subscription": True,
            "focus_score": current_focus_score,
            "clustering_enabled": subscription.get("clustering_enabled", False),
            "keywords_count": len(user_keywords),
            "clusters_count": len(clustering_result['clusters']),
            "primary_topics": clustering_result['primary_topics']
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get focus score: {str(e)}")

@router.post("/update-keywords")
async def update_user_keywords(
    request: KeywordAnalysisRequest,
    current_user_id: str = Depends(get_current_user_id)
):
    """
    更新用戶關鍵字並重新進行聚類分析
    """
    try:
        # 執行聚類分析
        clustering_result = clustering_system.cluster_keywords(request.keywords)
        
        # 更新用戶訂閱
        update_success = db_manager.update_subscription_with_enhanced_data(
            current_user_id,
            request.keywords,
            clustering_result['focus_score'],
            clustering_result['primary_topics']
        )
        
        if not update_success:
            raise HTTPException(status_code=500, detail="Failed to update user keywords")
        
        # 保存聚類結果
        db_manager.save_keyword_clustering_result(
            current_user_id,
            request.keywords,
            clustering_result['clusters'],
            clustering_result['focus_score'],
            clustering_result['primary_topics'],
            clustering_result['method']
        )
        
        return {
            "status": "success",
            "message": "Keywords updated successfully",
            "updated_keywords": request.keywords,
            "new_focus_score": clustering_result['focus_score'],
            "clustering_result": clustering_result
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update keywords: {str(e)}")

# 系統管理端點

@router.get("/admin/users-needing-guidance")
async def get_users_needing_guidance():
    """
    獲取需要引導的用戶列表 (管理員功能)
    """
    try:
        users = db_manager.get_users_needing_guidance()
        return {
            "users_needing_guidance": users,
            "count": len(users)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get users needing guidance: {str(e)}")

@router.get("/admin/users-low-focus")
async def get_users_with_low_focus(threshold: float = 0.5):
    """
    獲取聚焦度較低的用戶列表 (管理員功能)
    """
    try:
        users = db_manager.get_users_with_low_focus_score(threshold)
        return {
            "users_with_low_focus": users,
            "count": len(users),
            "threshold": threshold
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get users with low focus: {str(e)}")