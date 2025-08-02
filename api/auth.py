import jwt
import base64
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import hashlib

from core.config import settings

# JWT 驗證器
security = HTTPBearer()

class JWTVerifier:
    """改進版本的 JWT 驗證器 - 使用 HMAC 對稱金鑰"""
    
    def __init__(self):
        self._token_cache = {}  # 簡單的內存緩存
        self._jwt_secret = self._prepare_jwt_secret()
        
    def _prepare_jwt_secret(self) -> str:
        """準備 JWT Secret，確保格式正確"""
        if not settings.SUPABASE_JWT_SECRET:
            raise ValueError("SUPABASE_JWT_SECRET is required")
        
        secret = settings.SUPABASE_JWT_SECRET.strip()
        
        # 如果是 base64 編碼的，嘗試解碼
        try:
            # 檢查是否是 base64 格式
            if len(secret) % 4 == 0 and secret.replace('+', '').replace('/', '').replace('=', '').isalnum():
                decoded = base64.b64decode(secret)
                print("KEY: Using base64 decoded JWT Secret")
                return decoded
        except Exception:
            pass
        
        # 直接使用原始字符串
        print("KEY: Using raw string JWT Secret")
        return secret.encode('utf-8')
        
    def _generate_cache_key(self, token: str) -> str:
        """生成 token 的緩存鍵"""
        return hashlib.sha256(token.encode()).hexdigest()[:16]
    
    def verify_token_locally(self, token: str) -> Dict[str, Any]:
        """
        本地驗證 JWT token - 使用 HMAC 對稱金鑰
        這是主要的驗證方式
        """
        try:
            # 使用 HMAC 算法驗證 JWT
            payload = jwt.decode(
                token,
                self._jwt_secret,
                algorithms=['HS256'],  # 使用 HMAC SHA256
                audience='authenticated',  # Supabase 的 audience
                issuer=f"{settings.SUPABASE_URL}/auth/v1"  # Supabase 的 issuer
            )
            
            # 檢查必要欄位
            if not payload.get('sub'):  # sub 就是 user_id
                raise ValueError("Token missing user ID (sub)")
            
            if not payload.get('email'):
                raise ValueError("Token missing email")
            
            # 檢查 token 類型
            if payload.get('token_type') != 'access':
                raise ValueError(f"Invalid token type: {payload.get('token_type')}")
            
            # 檢查過期時間（JWT 庫已經自動檢查，但我們可以手動再確認）
            exp = payload.get('exp')
            if exp and datetime.fromtimestamp(exp) < datetime.now():
                raise jwt.ExpiredSignatureError("Token has expired")
            
            print(f"✅ 本地 HMAC 驗證成功 - 用戶: {payload.get('email')}")
            
            return {
                "user_id": payload['sub'],
                "email": payload['email'],
                "role": payload.get('role', 'authenticated'),
                "exp": payload.get('exp'),
                "iat": payload.get('iat'),
                "user_metadata": payload.get('user_metadata', {}),
                "app_metadata": payload.get('app_metadata', {}),
                "verification_method": "local_hmac"
            }
            
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except jwt.InvalidTokenError as e:
            print(f"❌ JWT 驗證失敗: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token: {str(e)}",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(e),
                headers={"WWW-Authenticate": "Bearer"},
            )
        except Exception as e:
            print(f"❌ 本地 JWT 驗證失敗: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token verification failed",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    def verify_token_with_supabase(self, token: str) -> Dict[str, Any]:
        """
        使用 Supabase API 驗證 token
        這是備用方案，當本地驗證失敗時使用
        """
        try:
            from supabase import create_client
            supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)
            
            print("🔄 使用 Supabase API 驗證...")
            user_response = supabase.auth.get_user(token)
            
            if not user_response.user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token - user not found",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            user = user_response.user
            print(f"✅ Supabase API 驗證成功 - 用戶: {user.email}")
            
            return {
                "user_id": user.id,
                "email": user.email,
                "role": user.role if hasattr(user, 'role') else 'authenticated',
                "user_metadata": user.user_metadata or {},
                "app_metadata": user.app_metadata or {},
                "verification_method": "supabase_api"
            }
            
        except Exception as e:
            print(f"❌ Supabase API 驗證失敗: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token verification failed",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """
        主要的 token 驗證方法
        優先使用本地 HMAC 驗證，失敗時退回到 Supabase API
        支持緩存機制
        """
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token is required",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # 檢查緩存
        cache_key = self._generate_cache_key(token)
        if cache_key in self._token_cache:
            cached_data, expiry = self._token_cache[cache_key]
            if datetime.now() < expiry:
                print("📦 使用緩存的驗證結果")
                return cached_data
            else:
                # 清除過期的緩存
                del self._token_cache[cache_key]
        
        user_data = None
        verification_error = None
        
        try:
            # 優先使用本地 HMAC 驗證
            user_data = self.verify_token_locally(token)
            
        except HTTPException as e:
            # 記錄本地驗證失敗的原因
            verification_error = str(e.detail)
            print(f"⚠️ 本地驗證失敗: {verification_error}")
            
            # 如果是 token 過期，直接拋出錯誤，不嘗試 Supabase API
            if "expired" in verification_error.lower():
                raise e
            
            try:
                # 嘗試 Supabase API 驗證
                user_data = self.verify_token_with_supabase(token)
                
            except HTTPException as supabase_error:
                # 兩種方法都失敗，拋出最後的錯誤
                print(f"❌ 所有驗證方法都失敗")
                raise supabase_error
        
        if user_data:
            # 緩存結果（緩存 5 分鐘）
            cache_expiry = datetime.now() + timedelta(minutes=5)
            self._token_cache[cache_key] = (user_data, cache_expiry)
            
            # 清理過期的緩存項目（簡單的清理策略）
            if len(self._token_cache) > 100:  # 限制緩存大小
                self._cleanup_cache()
            
            return user_data
        
        # 這個情況應該不會發生，但作為安全措施
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    def _cleanup_cache(self):
        """清理過期的緩存項目"""
        now = datetime.now()
        expired_keys = [
            key for key, (_, expiry) in self._token_cache.items() 
            if now >= expiry
        ]
        for key in expired_keys:
            del self._token_cache[key]
        
        print(f"🧹 清理了 {len(expired_keys)} 個過期的緩存項目")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """獲取緩存統計信息（用於監控）"""
        now = datetime.now()
        active_count = sum(1 for _, expiry in self._token_cache.values() if now < expiry)
        
        return {
            "total_cached_tokens": len(self._token_cache),
            "active_cached_tokens": active_count,
            "jwt_secret_configured": bool(self._jwt_secret),
            "verification_method": "hmac_sha256"
        }

# 創建全局驗證器實例
jwt_verifier = JWTVerifier()

def verify_supabase_jwt(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """
    改進版本的 JWT 驗證函數
    支持本地 HMAC 驗證、緩存和詳細錯誤處理
    """
    token = credentials.credentials
    return jwt_verifier.verify_token(token)

def get_current_user_id(user_info: dict = Depends(verify_supabase_jwt)) -> str:
    """獲取當前用戶 ID 的便捷函數"""
    return user_info["user_id"]

def get_current_user_email(user_info: dict = Depends(verify_supabase_jwt)) -> str:
    """獲取當前用戶 Email 的便捷函數"""
    return user_info["email"]

def require_admin_role(user_info: dict = Depends(verify_supabase_jwt)) -> dict:
    """要求管理員權限的依賴函數"""
    user_role = user_info.get("role", "authenticated")
    app_metadata = user_info.get("app_metadata", {})
    
    # 檢查角色或 app_metadata 中的權限
    is_admin = (
        user_role == "admin" or 
        app_metadata.get("role") == "admin" or 
        app_metadata.get("is_admin") is True
    )
    
    if not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    return user_info

# 可選的用戶信息依賴函數
def get_optional_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))) -> Optional[dict]:
    """獲取可選的用戶信息（不強制登入）"""
    if not credentials:
        return None
    
    try:
        return jwt_verifier.verify_token(credentials.credentials)
    except HTTPException:
        return None

class AuthenticationError(Exception):
    """認證相關錯誤"""
    pass 