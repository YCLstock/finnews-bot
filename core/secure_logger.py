import os
import logging
from typing import Any

# 檢測是否為生產環境
IS_PRODUCTION = os.environ.get("ENVIRONMENT", "development").lower() == "production"

class SecureLogger:
    """安全日誌記錄器 - 在生產環境中過濾敏感信息"""
    
    def __init__(self, name: str = "finnews-bot"):
        self.logger = logging.getLogger(name)
        if not self.logger.handlers:
            self._setup_logger()
    
    def _setup_logger(self):
        """設置日誌記錄器"""
        level = logging.WARNING if IS_PRODUCTION else logging.DEBUG
        self.logger.setLevel(level)
        
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
    
    def debug(self, message: str, *args: Any) -> None:
        """開發環境調試信息"""
        if not IS_PRODUCTION:
            self.logger.debug(message, *args)
    
    def info(self, message: str, *args: Any) -> None:
        """一般信息（生產環境也會記錄）"""
        self.logger.info(message, *args)
    
    def warning(self, message: str, *args: Any) -> None:
        """警告信息"""
        self.logger.warning(message, *args)
    
    def error(self, message: str, *args: Any) -> None:
        """錯誤信息"""
        self.logger.error(message, *args)
    
    def auth_success(self, user_email: str, method: str = "unknown") -> None:
        """記錄認證成功（生產環境會清理敏感信息）"""
        if IS_PRODUCTION:
            # 生產環境只記錄認證成功，不記錄完整 email
            masked_email = self._mask_email(user_email)
            self.info(f"Auth success: {masked_email} via {method}")
        else:
            self.debug(f"✅ 認證成功 - 用戶: {user_email} 方法: {method}")
    
    def auth_failure(self, error_msg: str, user_hint: str = None) -> None:
        """記錄認證失敗"""
        if IS_PRODUCTION:
            # 生產環境只記錄失敗，不記錄詳細錯誤
            self.warning("Authentication failed")
        else:
            self.debug(f"❌ 認證失敗: {error_msg} {f'用戶提示: {user_hint}' if user_hint else ''}")
    
    def api_request(self, method: str, endpoint: str, has_auth: bool = False) -> None:
        """記錄 API 請求"""
        if not IS_PRODUCTION:
            auth_status = "✅" if has_auth else "❌"
            self.debug(f"🚀 API Request: {method} {endpoint}, Auth: {auth_status}")
    
    def validation_error(self, endpoint: str, error_details: Any = None) -> None:
        """記錄驗證錯誤"""
        if IS_PRODUCTION:
            self.warning(f"Validation error on {endpoint}")
        else:
            self.debug(f"ERROR: 422 驗證錯誤 - 端點: {endpoint}")
            if error_details:
                self.debug(f"ERROR: 驗證錯誤詳情: {error_details}")
    
    def environment_check(self, var_name: str, is_configured: bool) -> None:
        """記錄環境變數檢查"""
        if is_configured:
            self.debug(f"✅ {var_name} 已配置")
        else:
            self.warning(f"⚠️ {var_name} 未配置")
    
    def cache_operation(self, operation: str, details: str = None) -> None:
        """記錄緩存操作"""
        if not IS_PRODUCTION:
            self.debug(f"📦 緩存操作: {operation} {details or ''}")
    
    def _mask_email(self, email: str) -> str:
        """遮罩 email 地址以保護隱私"""
        if "@" not in email:
            return "***"
        
        local, domain = email.split("@", 1)
        if len(local) <= 2:
            masked_local = "*" * len(local)
        else:
            masked_local = local[0] + "*" * (len(local) - 2) + local[-1]
        
        return f"{masked_local}@{domain}"

# 創建全局安全日誌記錄器實例
secure_logger = SecureLogger()

# 便利函數
def log_debug(message: str, *args: Any) -> None:
    """開發環境調試日誌"""
    secure_logger.debug(message, *args)

def log_info(message: str, *args: Any) -> None:
    """一般信息日誌"""
    secure_logger.info(message, *args)

def log_warning(message: str, *args: Any) -> None:
    """警告日誌"""
    secure_logger.warning(message, *args)

def log_error(message: str, *args: Any) -> None:
    """錯誤日誌"""
    secure_logger.error(message, *args)

def log_auth_success(user_email: str, method: str = "unknown") -> None:
    """認證成功日誌"""
    secure_logger.auth_success(user_email, method)

def log_auth_failure(error_msg: str, user_hint: str = None) -> None:
    """認證失敗日誌"""
    secure_logger.auth_failure(error_msg, user_hint)

def is_production() -> bool:
    """檢查是否為生產環境"""
    return IS_PRODUCTION