from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, validator

from api.auth import get_current_user_id, verify_supabase_jwt
from core.database import db_manager
from core.utils import validate_discord_webhook, validate_keywords, normalize_language_code
from core.delivery_manager import get_delivery_manager

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])

# Pydantic models for request/response
class SubscriptionCreate(BaseModel):
    """創建訂閱的請求模型"""
    delivery_platform: str = "discord"  # 支援 "discord" 或 "email"
    delivery_target: str  # Discord Webhook URL 或 Email 地址
    keywords: List[str] = []
    news_sources: List[str] = ["yahoo_finance"]  # 預設新聞源
    summary_language: str = "zh-tw"  # 預設繁體中文
    push_frequency_type: str = "daily"  # 新的推送頻率類型
    
    @validator('delivery_platform')
    def validate_platform(cls, v):
        supported_platforms = get_delivery_manager().get_supported_platforms()
        if v not in supported_platforms:
            raise ValueError(f'delivery_platform must be one of: {", ".join(supported_platforms)}')
        return v
    
    @validator('delivery_target')
    def validate_target(cls, v, values):
        platform = values.get('delivery_platform', 'discord')
        print(f"🔍 驗證 {platform} 推送目標: {v}")
        
        delivery_manager = get_delivery_manager()
        if not delivery_manager.validate_target(platform, v):
            if platform == 'discord':
                error_msg = f'Invalid Discord webhook URL: {v}. Must start with https://discord.com/api/webhooks/'
            elif platform == 'email':
                error_msg = f'Invalid email address: {v}. Please provide a valid email address.'
            else:
                error_msg = f'Invalid {platform} target: {v}'
            
            print(f"❌ {platform} 推送目標驗證失敗: {v}")
            raise ValueError(error_msg)
        
        print(f"✅ {platform} 推送目標驗證通過: {v}")
        return v
    
    @validator('keywords')
    def validate_keywords_list(cls, v):
        print(f"🔍 驗證關鍵字列表: {v}")
        if not validate_keywords(v):
            print(f"❌ 關鍵字列表驗證失敗: {v}")
            raise ValueError(f'Invalid keywords list: {v}. Max 10 keywords, each must be non-empty string.')
        print(f"✅ 關鍵字列表驗證通過: {v}")
        return v
    
    @validator('push_frequency_type')
    def validate_frequency_type(cls, v):
        if v not in ['daily', 'twice', 'thrice']:
            raise ValueError('push_frequency_type must be one of: daily, twice, thrice')
        return v
    
    @validator('summary_language')
    def validate_summary_language(cls, v):
        print(f"🔍 驗證摘要語言: {v}")
        
        # 標準化語言代碼格式
        normalized_language = normalize_language_code(v)
        
        valid_languages = ['zh-tw', 'zh-cn', 'en-us', 'en', 'zh']
        if normalized_language not in valid_languages:
            print(f"❌ 摘要語言驗證失敗: {normalized_language}")
            raise ValueError(f'summary_language must be one of: {", ".join(valid_languages)}')
        
        print(f"✅ 摘要語言驗證通過: {normalized_language}")
        return normalized_language

class SubscriptionUpdate(BaseModel):
    """更新訂閱的請求模型"""
    delivery_platform: str = None
    delivery_target: str = None
    keywords: List[str] = None
    news_sources: List[str] = None
    summary_language: str = None
    push_frequency_type: str = None
    is_active: bool = None
    
    @validator('delivery_platform')
    def validate_platform(cls, v):
        if v is not None:
            supported_platforms = get_delivery_manager().get_supported_platforms()
            if v not in supported_platforms:
                raise ValueError(f'delivery_platform must be one of: {", ".join(supported_platforms)}')
        return v
    
    @validator('delivery_target')
    def validate_target(cls, v, values):
        if v is not None:
            platform = values.get('delivery_platform')
            if platform:
                delivery_manager = get_delivery_manager()
                if not delivery_manager.validate_target(platform, v):
                    if platform == 'discord':
                        raise ValueError('Invalid Discord webhook URL')
                    elif platform == 'email':
                        raise ValueError('Invalid email address')
                    else:
                        raise ValueError(f'Invalid {platform} target')
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
    
    @validator('summary_language')
    def validate_summary_language(cls, v):
        if v is not None:
            print(f"🔍 更新驗證摘要語言: {v}")
            
            # 標準化語言代碼格式
            normalized_language = normalize_language_code(v)
            
            valid_languages = ['zh-tw', 'zh-cn', 'en-us', 'en', 'zh']
            if normalized_language not in valid_languages:
                print(f"❌ 更新摘要語言驗證失敗: {normalized_language}")
                raise ValueError(f'summary_language must be one of: {", ".join(valid_languages)}')
            
            print(f"✅ 更新摘要語言驗證通過: {normalized_language}")
            return normalized_language
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
    try:
        print(f"🔍 正在查詢用戶訂閱: {current_user_id}")
        subscription = db_manager.get_subscription_by_user(current_user_id)
        
        if subscription is None:
            print(f"📭 用戶 {current_user_id} 暫無訂閱")
        else:
            print(f"✅ 成功獲取用戶 {current_user_id} 的訂閱")
            
        return subscription
        
    except Exception as e:
        print(f"❌ 獲取用戶訂閱時發生錯誤: {str(e)}")
        print(f"❌ 錯誤類型: {type(e).__name__}")
        import traceback
        print(f"❌ 詳細錯誤: {traceback.format_exc()}")
        
        # 返回 500 錯誤而不是讓系統返回 403
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve subscription: {str(e)}"
        )

@router.post("/", response_model=SubscriptionResponse, status_code=status.HTTP_201_CREATED)
async def create_or_update_subscription(
    subscription_data: SubscriptionCreate,
    current_user_id: str = Depends(get_current_user_id)
):
    """
    創建或更新用戶的訂閱（使用 UPSERT）
    """
    try:
        print(f"📝 正在創建/更新用戶 {current_user_id} 的訂閱")
        print(f"📝 收到的資料: {subscription_data.dict()}")
        print(f"📝 語言設定: {subscription_data.summary_language}")
        
        # 準備資料庫資料
        db_data = {
            "user_id": current_user_id,
            "delivery_platform": subscription_data.delivery_platform,
            "delivery_target": subscription_data.delivery_target,
            "keywords": subscription_data.keywords,
            "original_keywords": subscription_data.keywords,  # 新增：儲存原始關鍵字
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
        
        # 標記關鍵字為已更新（觸發後續AI標籤轉換）
        db_manager.mark_keywords_as_updated(current_user_id)
        
        print(f"✅ 成功創建/更新用戶 {current_user_id} 的訂閱")
        print(f"📝 關鍵字已標記為待轉換，將在下次定時任務中處理")
        return result
        
    except HTTPException:
        # 重新拋出 HTTP 異常
        raise
    except Exception as e:
        print(f"❌ 創建訂閱時發生錯誤: {str(e)}")
        print(f"❌ 錯誤類型: {type(e).__name__}")
        import traceback
        print(f"❌ 詳細錯誤: {traceback.format_exc()}")
        
        # 檢查是否為資料庫 enum 錯誤
        if "invalid input value for enum" in str(e):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid enum value: {str(e)}"
            )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create subscription: {str(e)}"
        )

@router.put("/", response_model=SubscriptionResponse)
async def update_subscription(
    update_data: SubscriptionUpdate,
    current_user_id: str = Depends(get_current_user_id)
):
    """
    更新用戶的訂閱
    """
    try:
        print(f"🔄 正在更新用戶 {current_user_id} 的訂閱")
        
        # 檢查用戶是否有訂閱
        existing_subscription = db_manager.get_subscription_by_user(current_user_id)
        if not existing_subscription:
            print(f"❌ 更新失敗: 用戶 {current_user_id} 沒有訂閱記錄")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subscription not found"
            )
            
    except HTTPException:
        # 重新拋出 HTTP 異常
        raise
    except Exception as e:
        print(f"❌ 檢查訂閱存在性時發生錯誤: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check existing subscription: {str(e)}"
        )
    
    # 準備更新資料（只包含非 None 的欄位）
    update_dict = {}
    keywords_updated = False
    
    for field, value in update_data.dict().items():
        if value is not None:
            update_dict[field] = value
            # 如果更新了關鍵字，同時更新original_keywords
            if field == "keywords":
                update_dict["original_keywords"] = value
                keywords_updated = True
    
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
    
    # 如果更新了關鍵字，標記為待轉換
    if keywords_updated:
        db_manager.mark_keywords_as_updated(current_user_id)
        print(f"📝 用戶 {current_user_id} 關鍵字已更新並標記為待轉換")
    
    return result

@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_subscription(
    current_user_id: str = Depends(get_current_user_id)
):
    """
    刪除用戶的訂閱
    """
    try:
        print(f"🗑️ 正在刪除用戶 {current_user_id} 的訂閱")
        
        # 檢查用戶是否有訂閱
        existing_subscription = db_manager.get_subscription_by_user(current_user_id)
        if not existing_subscription:
            print(f"❌ 刪除失敗: 用戶 {current_user_id} 沒有訂閱記錄")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subscription not found"
            )
            
    except HTTPException:
        # 重新拋出 HTTP 異常
        raise
    except Exception as e:
        print(f"❌ 檢查訂閱存在性時發生錯誤: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check existing subscription: {str(e)}"
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
    try:
        print(f"🔄 正在切換用戶 {current_user_id} 的訂閱狀態")
        
        # 檢查用戶是否有訂閱
        existing_subscription = db_manager.get_subscription_by_user(current_user_id)
        if not existing_subscription:
            print(f"❌ 切換失敗: 用戶 {current_user_id} 沒有訂閱記錄")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subscription not found"
            )
            
    except HTTPException:
        # 重新拋出 HTTP 異常
        raise
    except Exception as e:
        print(f"❌ 檢查訂閱存在性時發生錯誤: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check existing subscription: {str(e)}"
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