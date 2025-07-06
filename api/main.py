from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from core.config import settings
from api.endpoints import subscriptions, history
from api.auth import jwt_verifier

# 驗證環境變數
try:
    settings.validate()
    print("✅ 環境變數驗證成功")
except ValueError as e:
    print(f"❌ 環境變數驗證失敗: {e}")
    raise

@asynccontextmanager
async def lifespan(app: FastAPI):
    """應用程式生命週期管理"""
    # 啟動時執行
    print("🚀 FinNews-Bot API 啟動中...")
    yield
    # 關閉時執行
    print("🛑 FinNews-Bot API 關閉中...")

# 創建 FastAPI 應用程式
app = FastAPI(
    title="FinNews-Bot API",
    description="Financial News Bot API for managing subscriptions and news delivery",
    version="2.0.0",
    lifespan=lifespan
)

# CORS 設定 - 允許前端與 API 通信
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Next.js 開發環境
        "http://localhost:3001",  # 額外的開發環境
        "https://finnews-bot-frontend.vercel.app",  # 主要 Vercel 域名
        "https://finnews-bot-frontend-git-feature-06c8a8-lins-projects-06103545.vercel.app",  # 您的分支域名
        "https://finnews-bot-frontend-git-main-lins-projects-06103545.vercel.app",  # main 分支域名
        "https://lins-projects-06103545.vercel.app",  # 可能的項目域名
        # 添加更多可能的 Vercel 域名模式
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
)

# 註冊路由
app.include_router(subscriptions.router, prefix="/api/v1")
app.include_router(history.router, prefix="/api/v1")

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
    return {
        "supabase_url": settings.SUPABASE_URL,
        "supabase_anon_key": settings.SUPABASE_ANON_KEY,
        "supported_languages": ["zh-TW", "en-US"],
        "supported_news_sources": ["yahoo_finance"],
        "max_keywords": 10
    }

@app.get("/api/v1/auth/stats")
async def get_auth_stats():
    """獲取 JWT 驗證的緩存統計信息（用於監控）"""
    try:
        stats = jwt_verifier.get_cache_stats()
        return {
            "auth_cache_stats": stats,
            "status": "healthy"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unable to get auth stats: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True  # 開發環境啟用，生產環境應設為 False
    ) 