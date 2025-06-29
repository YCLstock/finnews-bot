from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, validator

from api.auth import get_current_user_id
from core.database import db_manager
from core.utils import validate_discord_webhook, validate_keywords

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])

# Pydantic models for request/response
class SubscriptionCreate(BaseModel):
    """創建訂閱的請求模型"""
    delivery_platform: str = "discord"  # 目前只支援 Discord
    delivery_target: str  # Discord Webhook URL
    keywords: List[str] = []
    news_sources: List[str] = ["yahoo_finance"]  # 預設新聞源
    summary_language: str = "zh-TW"  # 預設繁體中文
    push_frequency_type: str = "daily"  # 新的推送頻率類型
    
    @validator('delivery_target')
    def validate_webhook(cls, v):
        if not validate_discord_webhook(v):
            raise ValueError('Invalid Discord webhook URL')
        return v
    
    @validator('keywords')
    def validate_keywords_list(cls, v):
        if not validate_keywords(v):
            raise ValueError('Invalid keywords list (max 10 keywords)')
        return v
    
    @validator('push_frequency_type')
    def validate_frequency_type(cls, v):
        if v not in ['daily', 'twice', 'thrice']:
            raise ValueError('push_frequency_type must be one of: daily, twice, thrice')
        return v

class SubscriptionUpdate(BaseModel):
    """更新訂閱的請求模型"""
    delivery_target: str = None
    keywords: List[str] = None
    news_sources: List[str] = None
    summary_language: str = None
    push_frequency_type: str = None
    is_active: bool = None
    
    @validator('delivery_target')
    def validate_webhook(cls, v):
        if v is not None and not validate_discord_webhook(v):
            raise ValueError('Invalid Discord webhook URL')
        return v
    
    @validator('keywords')
    def validate_keywords_list(cls, v):
        if v is not None and not validate_keywords(v):
            raise ValueError('Invalid keywords list (max 10 keywords)')
        return v
    
    @validator('push_frequency_type')
    def validate_frequency_type(cls, v):
        if v is not None and v not in ['daily', 'twice', 'thrice']:
            raise ValueError('push_frequency_type must be one of: daily, twice, thrice')
        return v

class SubscriptionResponse(BaseModel):
    """訂閱回應模型"""
    user_id: str
    delivery_platform: str
    delivery_target: str
    keywords: List[str]
    news_sources: List[str]
    summary_language: str
    push_frequency_type: str
    is_active: bool
    last_pushed_at: Optional[str] = None
    updated_at: Optional[str] = None
    last_push_window: Optional[str] = None

@router.get("/", response_model=Optional[SubscriptionResponse])
async def get_user_subscription(current_user_id: str = Depends(get_current_user_id)):
    """
    獲取當前用戶的訂閱（單一訂閱）
    """
    subscription = db_manager.get_subscription_by_user(current_user_id)
    return subscription

@router.post("/", response_model=SubscriptionResponse, status_code=status.HTTP_201_CREATED)
async def create_or_update_subscription(
    subscription_data: SubscriptionCreate,
    current_user_id: str = Depends(get_current_user_id)
):
    """
    創建或更新用戶的訂閱（使用 UPSERT）
    """
    # 準備資料庫資料
    db_data = {
        "user_id": current_user_id,
        "delivery_platform": subscription_data.delivery_platform,
        "delivery_target": subscription_data.delivery_target,
        "keywords": subscription_data.keywords,
        "news_sources": subscription_data.news_sources,
        "summary_language": subscription_data.summary_language,
        "push_frequency_type": subscription_data.push_frequency_type,
        "is_active": True
    }
    
    result = db_manager.create_subscription(db_data)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create subscription"
        )
    
    return result

@router.put("/", response_model=SubscriptionResponse)
async def update_subscription(
    update_data: SubscriptionUpdate,
    current_user_id: str = Depends(get_current_user_id)
):
    """
    更新用戶的訂閱
    """
    # 檢查用戶是否有訂閱
    existing_subscription = db_manager.get_subscription_by_user(current_user_id)
    if not existing_subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found"
        )
    
    # 準備更新資料（只包含非 None 的欄位）
    update_dict = {}
    for field, value in update_data.dict().items():
        if value is not None:
            update_dict[field] = value
    
    if not update_dict:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No data provided for update"
        )
    
    result = db_manager.update_subscription(current_user_id, update_dict)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update subscription"
        )
    
    return result

@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_subscription(
    current_user_id: str = Depends(get_current_user_id)
):
    """
    刪除用戶的訂閱
    """
    # 檢查用戶是否有訂閱
    existing_subscription = db_manager.get_subscription_by_user(current_user_id)
    if not existing_subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found"
        )
    
    success = db_manager.delete_subscription(current_user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete subscription"
        )

@router.patch("/toggle", response_model=SubscriptionResponse)
async def toggle_subscription(
    current_user_id: str = Depends(get_current_user_id)
):
    """
    切換用戶訂閱的啟用/停用狀態
    """
    # 檢查用戶是否有訂閱
    existing_subscription = db_manager.get_subscription_by_user(current_user_id)
    if not existing_subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found"
        )
    
    # 切換啟用/停用狀態
    new_status = not existing_subscription['is_active']
    result = db_manager.update_subscription(current_user_id, {"is_active": new_status})
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to toggle subscription"
        )
    
    return result

@router.get("/frequency-options")
async def get_frequency_options():
    """獲取可用的推送頻率選項"""
    return {
        "options": [
            {
                "value": "daily",
                "label": "每日一次",
                "description": "每天早上 08:00 推送",
                "times": ["08:00"],
                "max_articles": 10
            },
            {
                "value": "twice", 
                "label": "每日兩次",
                "description": "早上 08:00 和晚上 20:00 推送",
                "times": ["08:00", "20:00"],
                "max_articles": 5
            },
            {
                "value": "thrice",
                "label": "每日三次", 
                "description": "早上 08:00、下午 13:00 和晚上 20:00 推送",
                "times": ["08:00", "13:00", "20:00"],
                "max_articles": 3
            }
        ]
    } 