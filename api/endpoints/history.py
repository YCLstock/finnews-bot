from typing import List, Dict, Any
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from datetime import datetime

from api.auth import get_current_user_id
from core.database import db_manager

router = APIRouter(prefix="/history", tags=["history"])

class PushHistoryResponse(BaseModel):
    """推送歷史回應模型"""
    id: int
    user_id: str
    article_id: int
    pushed_at: str
    news_articles: Dict[str, Any] = None  # 包含文章詳細資訊

@router.get("/", response_model=List[PushHistoryResponse])
async def get_push_history(
    current_user_id: str = Depends(get_current_user_id),
    limit: int = Query(default=50, ge=1, le=100, description="Number of records to return")
):
    """
    根據 todolist 要求：開發獲取推播歷史的API端點 (/history)
    獲取當前用戶的推送歷史
    """
    history = db_manager.get_push_history_by_user(current_user_id, limit)
    return history

@router.get("/stats")
async def get_push_stats(current_user_id: str = Depends(get_current_user_id)):
    """獲取用戶的推送統計資訊"""
    # 這是一個額外的端點，提供統計數據
    history = db_manager.get_push_history_by_user(current_user_id, 1000)  # 獲取更多記錄用於統計
    
    # 計算統計資訊
    total_pushes = len(history)
    
    # 按日期分組統計
    daily_stats = {}
    for record in history:
        date = record['pushed_at'][:10]  # 取日期部分 YYYY-MM-DD
        daily_stats[date] = daily_stats.get(date, 0) + 1
    
    # 最近 7 天的推送數量
    recent_pushes = [record for record in history if record['pushed_at'] >= (datetime.now().isoformat()[:10])]
    
    return {
        "total_pushes": total_pushes,
        "recent_pushes_7_days": len(recent_pushes),
        "daily_stats": daily_stats,
        "most_active_day": max(daily_stats.items(), key=lambda x: x[1]) if daily_stats else None
    } 