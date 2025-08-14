from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import traceback

from core.config import settings
from core.secure_logger import secure_logger, is_production
from api.endpoints import subscriptions, history, guidance, quick_onboarding
from api.auth import jwt_verifier

# 驗證環境變數
try:
    settings.validate()
    secure_logger.info("環境變數驗證成功")
except ValueError as e:
    secure_logger.error(f"環境變數驗證失敗: {e}")
    raise

@asynccontextmanager
async def lifespan(app: FastAPI):
    """應用程式生命週期管理"""
    # 啟動時執行
    secure_logger.info("FinNews-Bot API 啟動中...")
    yield
    # 關閉時執行
    secure_logger.info("FinNews-Bot API 關閉中...")

# 創建 FastAPI 應用程式
app = FastAPI(
    title="FinNews-Bot API",
    description="Financial News Bot API for managing subscriptions and news delivery",
    version="2.0.0",
    lifespan=lifespan
)

# CORS 設定 - 根據環境配置允許的源
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],  # 限制標頭而非使用 *
)

# 添加請求驗證錯誤處理器
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """處理 422 驗證錯誤並提供適當信息"""
    endpoint = str(request.url.path)
    
    # 安全日誌記錄
    secure_logger.validation_error(endpoint, exc.errors() if not is_production() else None)
    
    if not is_production():
        # 開發環境：提供詳細錯誤信息
        try:
            body = await request.body()
            secure_logger.debug(f"請求體: {body.decode('utf-8')}")
        except Exception as e:
            secure_logger.debug(f"無法讀取請求體: {e}")
    
    # 處理錯誤信息，確保能夠 JSON 序列化
    if is_production():
        # 生產環境：提供友好的錯誤信息
        return JSONResponse(
            status_code=422,
            content={
                "detail": "請求資料格式錯誤，請檢查輸入內容",
                "message": "Validation error"
            }
        )
    else:
        # 開發環境：提供詳細錯誤信息
        error_details = []
        for error in exc.errors():
            serializable_error = {
                "type": error.get("type"),
                "loc": error.get("loc"),
                "msg": error.get("msg"),
                "input": error.get("input")
            }
            error_details.append(serializable_error)
        
        return JSONResponse(
            status_code=422,
            content={
                "detail": error_details,
                "message": "Validation error occurred"
            }
        )

# 註冊路由
app.include_router(subscriptions.router, prefix="/api/v1")
app.include_router(history.router, prefix="/api/v1")
app.include_router(guidance.router, prefix="/api/v1")
app.include_router(quick_onboarding.router, prefix="/api/v1")

@app.get("/")
async def root():
    """根端點 - API 健康檢查"""
    return {
        "message": "FinNews-Bot API is running",
        "version": "2.0.0",
        "status": "healthy"
    }

@app.get("/api/v1/health")
async def health_check():
    """健康檢查端點"""
    try:
        # 簡單的資料庫連接測試
        from core.database import db_manager
        test_result = db_manager.get_active_subscriptions()  # 不會實際獲取資料，只是測試連接
        
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": settings.SUPABASE_URL is not None
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service unavailable: {str(e)}")

@app.get("/api/v1/config")
async def get_config():
    """獲取客戶端需要的配置資訊（不包含敏感資訊）"""
    # 在生產環境中檢查這些配置是否應該暴露
    config = {
        "supported_languages": ["zh-tw", "zh-cn", "en-us", "en", "zh"],
        "supported_news_sources": ["yahoo_finance"],
        "max_keywords": 10
    }
    
    # 只在開發環境或明確需要時暴露 Supabase 配置
    if not is_production():
        config.update({
            "supabase_url": settings.SUPABASE_URL,
            "supabase_anon_key": settings.SUPABASE_ANON_KEY,
        })
    
    return config

@app.get("/api/v1/auth/stats")
async def get_auth_stats():
    """獲取 JWT 驗證的緩存統計信息（用於監控）"""
    # 這個端點包含敏感的系統資訊，應該限制存取
    if is_production():
        # 生產環境中可能需要管理員權限或完全禁用
        raise HTTPException(
            status_code=404, 
            detail="Endpoint not available in production"
        )
    
    try:
        stats = jwt_verifier.get_cache_stats()
        return {
            "auth_cache_stats": stats,
            "status": "healthy",
            "environment": "development"
        }
    except Exception as e:
        secure_logger.error(f"Failed to get auth stats: {str(e)}")
        raise HTTPException(status_code=500, detail="Unable to get auth stats")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=not is_production()  # 只在開發環境啟用 reload
    ) 