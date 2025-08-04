#!/usr/bin/env python3
"""
快速引導API端點
提供30秒快速設定功能，無需複雜的AI分析
"""

from typing import List, Dict, Any, Literal
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, validator
from datetime import datetime
import logging

from api.auth import get_current_user_id
from core.database import db_manager
from core.delivery_manager import get_delivery_manager
from core.utils import normalize_language_code

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/quick-onboarding", tags=["quick-onboarding"])

# 快速設定模板
QUICK_TEMPLATES = {
    "tech": {
        "id": "tech",
        "name": "科技股追蹤",
        "name_en": "Tech Stocks",
        "description": "關注蘋果、特斯拉、AI等科技趨勢",
        "description_en": "Follow Apple, Tesla, AI and tech trends",
        "icon": "💻",
        "keywords": ["蘋果", "特斯拉", "AI", "科技股"],
        "topics": ["tech", "electric-vehicles"],
        "sample_news": "蘋果發布新 iPhone、特斯拉股價動態、AI技術突破",
        "focus_score": 0.85
    },
    "crypto": {
        "id": "crypto", 
        "name": "加密貨幣",
        "name_en": "Cryptocurrency",
        "description": "比特幣、以太坊等數位資產動態",
        "description_en": "Bitcoin, Ethereum and digital asset updates",
        "icon": "₿",
        "keywords": ["比特幣", "以太坊", "加密貨幣"],
        "topics": ["crypto"],
        "sample_news": "比特幣價格突破新高、以太坊升級消息、加密貨幣政策",
        "focus_score": 0.90
    },
    "market": {
        "id": "market",
        "name": "市場動態", 
        "name_en": "Market Updates",
        "description": "股市、經濟政策、總體經濟分析",
        "description_en": "Stock market, economic policy, macro analysis",
        "icon": "📈",
        "keywords": ["股市", "經濟政策", "利率", "通膨"],
        "topics": ["stock-market", "inflation", "economies"],
        "sample_news": "Fed 利率決策、台股大盤走勢分析、通膨數據解讀",
        "focus_score": 0.80
    }
}

# Pydantic 模型定義

class QuickSetupRequest(BaseModel):
    """快速設定請求模型"""
    interest_category: Literal["tech", "crypto", "market"]
    delivery_platform: Literal["discord", "email"]
    delivery_target: str
    summary_language: str = "zh-tw"
    push_frequency_type: str = "daily"
    
    @validator('delivery_platform')
    def validate_platform(cls, v):
        delivery_manager = get_delivery_manager()
        supported_platforms = delivery_manager.get_supported_platforms()
        if v not in supported_platforms:
            raise ValueError(f'delivery_platform must be one of: {", ".join(supported_platforms)}')
        return v
    
    @validator('delivery_target')
    def validate_target(cls, v, values):
        platform = values.get('delivery_platform')
        if platform:
            # 只進行格式驗證，不進行網路連通性測試
            if platform == 'discord':
                if not v.startswith('https://discord.com/api/webhooks/'):
                    raise ValueError('Discord Webhook URL 格式不正確，必須以 https://discord.com/api/webhooks/ 開頭')
            elif platform == 'email':
                import re
                email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                if not re.match(email_pattern, v):
                    raise ValueError('電子郵件地址格式不正確，請提供有效的電子郵件地址')
        return v
    
    @validator('summary_language')
    def validate_language(cls, v):
        normalized = normalize_language_code(v)
        valid_languages = ['zh-tw', 'zh-cn', 'en-us', 'en', 'zh']
        if normalized not in valid_languages:
            raise ValueError(f'summary_language must be one of: {", ".join(valid_languages)}')
        return normalized
    
    @validator('push_frequency_type')
    def validate_frequency(cls, v):
        if v not in ['daily', 'twice', 'thrice']:
            raise ValueError('push_frequency_type must be one of: daily, twice, thrice')
        return v

class QuickSetupResponse(BaseModel):
    """快速設定回應模型"""
    success: bool
    subscription_id: str
    template_used: str
    keywords: List[str]
    focus_score: float
    message: str
    next_steps: List[str]

class QuickTemplate(BaseModel):
    """快速模板模型"""
    id: str
    name: str
    name_en: str
    description: str
    description_en: str
    icon: str
    keywords: List[str]
    sample_news: str
    focus_score: float

# API 端點實作

@router.get("/templates")
async def get_quick_templates():
    """獲取快速設定模板"""
    try:
        templates = [QuickTemplate(**template) for template in QUICK_TEMPLATES.values()]
        
        return {
            "success": True,
            "templates": templates,
            "supported_platforms": get_delivery_manager().get_supported_platforms(),
            "platform_info": {
                "discord": {
                    "name": "Discord",
                    "description": "推送到 Discord 頻道",
                    "setup_complexity": "中等",
                    "requires_setup": True,
                    "icon": "💬"
                },
                "email": {
                    "name": "Email",
                    "description": "發送到您的信箱",
                    "setup_complexity": "簡單",
                    "requires_setup": False,
                    "icon": "📧"
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get quick templates: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve templates"
        )

@router.post("/setup", response_model=QuickSetupResponse)
async def quick_setup(
    request: QuickSetupRequest,
    current_user_id: str = Depends(get_current_user_id)
):
    """30秒快速設定，使用預設關鍵字模板"""
    try:
        logger.info(f"Starting quick setup for user {current_user_id}")
        logger.info(f"Request data: {request.dict()}")
        
        # 檢查模板是否存在
        if request.interest_category not in QUICK_TEMPLATES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid interest category: {request.interest_category}"
            )
        
        template = QUICK_TEMPLATES[request.interest_category]
        
        # 檢查用戶是否已有訂閱
        existing_subscription = db_manager.get_subscription_by_user(current_user_id)
        if existing_subscription:
            logger.info(f"User {current_user_id} already has subscription, updating...")
        
        # 準備訂閱資料
        subscription_data = {
            "user_id": current_user_id,
            "delivery_platform": request.delivery_platform,
            "delivery_target": request.delivery_target,
            "keywords": template["keywords"],
            "original_keywords": template["keywords"],
            "news_sources": ["yahoo_finance"],
            "summary_language": request.summary_language,
            "push_frequency_type": request.push_frequency_type,
            "is_active": True,
            "guidance_completed": True,
            "focus_score": template["focus_score"],
            "clustering_method": "rule_based",  # 快速模式使用規則分析，用來推斷 onboarding_method
            "primary_topics": template["topics"]
        }
        
        # 創建或更新訂閱
        result = db_manager.create_subscription(subscription_data)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create subscription"
            )
        
        # 生成回應
        next_steps = [
            "您的個人化新聞推送已設定完成",
            f"將透過 {request.delivery_platform} 接收 {template['name']} 相關新聞",
            "您可以隨時在設定中調整關鍵字或推送頻率",
            "首次推送將在下個排程時間進行"
        ]
        
        if request.delivery_platform == "email":
            next_steps.append("請檢查信箱垃圾郵件資料夾以確保不會錯過新聞")
        
        logger.info(f"Quick setup completed successfully for user {current_user_id}")
        
        return QuickSetupResponse(
            success=True,
            subscription_id=current_user_id,
            template_used=template["name"],
            keywords=template["keywords"],
            focus_score=template["focus_score"],
            message=f"🎉 快速設定完成！您將開始接收 {template['name']} 相關新聞推送。",
            next_steps=next_steps
        )
        
    except HTTPException:
        # 重新拋出 HTTP 異常
        raise
    except Exception as e:
        logger.error(f"Quick setup failed for user {current_user_id}: {str(e)}")
        import traceback
        logger.error(f"Detailed error: {traceback.format_exc()}")
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Quick setup failed: {str(e)}"
        )

@router.get("/platform-info")
async def get_platform_info():
    """獲取支援的推送平台資訊"""
    try:
        delivery_manager = get_delivery_manager()
        
        return {
            "supported_platforms": delivery_manager.get_supported_platforms(),
            "platforms": {
                "discord": {
                    "name": "Discord",
                    "description": "推送到 Discord 頻道",
                    "icon": "💬",
                    "setup_required": True,
                    "setup_steps": [
                        "進入您的 Discord 伺服器",
                        "建立或選擇接收新聞的頻道",
                        "在頻道設定中建立 Webhook",
                        "複製 Webhook URL"
                    ],
                    "target_format": "https://discord.com/api/webhooks/...",
                    "pros": ["即時推送", "豐富格式", "支援討論"],
                    "cons": ["需要設定步驟", "需要 Discord 帳號"]
                },
                "email": {
                    "name": "Email",
                    "description": "發送到您的電子信箱",
                    "icon": "📧",
                    "setup_required": False,
                    "setup_steps": [
                        "輸入您的 Email 地址即可"
                    ],
                    "target_format": "your@email.com",
                    "pros": ["設定簡單", "人人都有信箱", "方便保存"],
                    "cons": ["可能進垃圾郵件", "非即時推送"]
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get platform info: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve platform information"
        )

@router.post("/validate-target")
async def validate_delivery_target(
    platform: str,
    target: str
):
    """驗證推送目標格式（僅格式驗證，不進行網路測試）"""
    try:
        delivery_manager = get_delivery_manager()
        
        # 檢查平台是否支援
        if platform not in delivery_manager.get_supported_platforms():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported platform: {platform}"
            )
        
        # 只進行格式驗證
        format_valid = False
        error_message = ""
        
        if platform == 'discord':
            format_valid = target.startswith('https://discord.com/api/webhooks/')
            if not format_valid:
                error_message = "Discord Webhook URL 格式不正確，必須以 https://discord.com/api/webhooks/ 開頭"
        elif platform == 'email':
            import re
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            format_valid = bool(re.match(email_pattern, target))
            if not format_valid:
                error_message = "電子郵件地址格式不正確，請提供有效的電子郵件地址"
        
        response = {
            "platform": platform,
            "target": target[:50] + "..." if len(target) > 50 else target,  # 隱藏完整目標
            "is_valid": format_valid,
            "validation_type": "format_only",
            "last_updated": datetime.now().isoformat()
        }
        
        if not format_valid:
            response["error"] = error_message
            if platform == "discord":
                response["help"] = "請確認您複製的是完整的 Discord Webhook URL"
            elif platform == "email":
                response["help"] = "請輸入有效的電子郵件地址，例如：user@example.com"
        else:
            response["message"] = "格式驗證通過，將在提交時進行連通性測試"
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to validate target format: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Format validation failed"
        )

@router.get("/migration-check")
async def check_existing_subscription(
    current_user_id: str = Depends(get_current_user_id)
):
    """檢查用戶是否已有訂閱（用於引導升級）"""
    try:
        existing_subscription = db_manager.get_subscription_by_user(current_user_id)
        
        if not existing_subscription:
            return {
                "has_subscription": False,
                "can_use_quick_setup": True,
                "message": "您可以使用快速設定開始接收新聞"
            }
        
        # 檢查是否為舊的複雜設定（通過 clustering_method 推斷）
        clustering_method = existing_subscription.get("clustering_method", "semantic")
        is_quick_setup = clustering_method == "rule_based"
        onboarding_method = "quick_start" if is_quick_setup else "custom"
        
        return {
            "has_subscription": True,
            "current_method": onboarding_method,
            "is_quick_setup": is_quick_setup,
            "delivery_platform": existing_subscription.get("delivery_platform"),
            "keywords_count": len(existing_subscription.get("keywords", [])),
            "focus_score": existing_subscription.get("focus_score", 0),
            "can_migrate_to_quick": not is_quick_setup,
            "message": "您已有訂閱設定" if not is_quick_setup else "您使用的是快速設定模式"
        }
        
    except Exception as e:
        logger.error(f"Failed to check existing subscription: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check subscription status"
        )