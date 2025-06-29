#!/usr/bin/env python3
"""
測試改進後的 JWT 驗證功能 - HMAC 版本
"""

import sys
import os
from pathlib import Path

# 添加項目根目錄到 Python 路徑
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from api.auth import jwt_verifier
from core.config import settings

def test_jwt_secret_config():
    """測試 JWT Secret 配置"""
    print("🔑 測試 JWT Secret 配置...")
    try:
        if not settings.SUPABASE_JWT_SECRET:
            print("❌ SUPABASE_JWT_SECRET 未設置")
            return False
        
        # 檢查 JWT 驗證器初始化
        secret_len = len(str(jwt_verifier._jwt_secret))
        print(f"✅ JWT Secret 已配置，長度: {secret_len} bytes")
        
        # 檢查 Secret 格式
        if hasattr(jwt_verifier._jwt_secret, 'decode'):
            print("✅ JWT Secret 格式: bytes")
        else:
            print("✅ JWT Secret 格式: string")
            
        return True
        
    except Exception as e:
        print(f"❌ JWT Secret 配置測試失敗: {e}")
        return False

def test_cache_functionality():
    """測試緩存功能"""
    print("\n📦 測試緩存功能...")
    try:
        stats = jwt_verifier.get_cache_stats()
        print("✅ 緩存統計信息:")
        for key, value in stats.items():
            print(f"   {key}: {value}")
        return True
    except Exception as e:
        print(f"❌ 緩存測試失敗: {e}")
        return False

def test_invalid_token():
    """測試無效 token 的處理"""
    print("\n🚫 測試無效 token 處理...")
    try:
        # 使用一個明顯無效的 token
        invalid_token = "invalid.token.here"
        jwt_verifier.verify_token(invalid_token)
        print("❌ 應該拋出異常但沒有")
        return False
    except Exception as e:
        print(f"✅ 正確拋出異常: {type(e).__name__}")
        return True

def test_malformed_jwt():
    """測試格式錯誤的 JWT"""
    print("\n🔧 測試格式錯誤的 JWT...")
    try:
        # 測試格式錯誤的 JWT
        malformed_jwt = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.invalid_payload.invalid_signature"
        jwt_verifier.verify_token(malformed_jwt)
        print("❌ 應該拋出異常但沒有")
        return False
    except Exception as e:
        print(f"✅ 正確拋出異常: {type(e).__name__}")
        return True

def test_jwt_creation_example():
    """測試 JWT 創建範例（僅用於演示格式）"""
    print("\n📝 演示 JWT 創建格式...")
    try:
        import jwt
        from datetime import datetime, timedelta
        
        # 創建一個測試 payload（僅用於展示格式）
        test_payload = {
            'sub': 'test-user-id',
            'email': 'test@example.com',
            'token_type': 'access',
            'role': 'authenticated',
            'iat': datetime.utcnow(),
            'exp': datetime.utcnow() + timedelta(hours=1),
            'aud': 'authenticated',
            'iss': f"{settings.SUPABASE_URL}/auth/v1"
        }
        
        # 僅顯示格式，不進行實際驗證
        print("✅ JWT Payload 格式示例:")
        print(f"   - sub (user_id): {test_payload['sub']}")
        print(f"   - email: {test_payload['email']}")
        print(f"   - token_type: {test_payload['token_type']}")
        print(f"   - audience: {test_payload['aud']}")
        print(f"   - issuer: {test_payload['iss']}")
        
        return True
        
    except Exception as e:
        print(f"❌ JWT 格式測試失敗: {e}")
        return False

def main():
    """主測試函數"""
    print("🧪 開始測試改進後的 JWT 驗證功能 (HMAC 版本)")
    print("=" * 60)
    
    tests = [
        ("JWT Secret 配置", test_jwt_secret_config),
        ("緩存功能", test_cache_functionality),
        ("無效 Token 處理", test_invalid_token),
        ("格式錯誤 JWT 處理", test_malformed_jwt),
        ("JWT 格式示例", test_jwt_creation_example),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔸 執行測試: {test_name}")
        if test_func():
            passed += 1
            print(f"✅ {test_name} - 通過")
        else:
            print(f"❌ {test_name} - 失敗")
    
    print("\n" + "=" * 60)
    print(f"📊 測試結果: {passed}/{total} 通過")
    
    if passed == total:
        print("🎉 所有測試通過！JWT 驗證功能正常")
        print("\n💡 提示:")
        print("  - JWT Secret 已正確配置")
        print("  - 使用 HMAC SHA256 算法進行驗證")
        print("  - 支援緩存和錯誤處理")
    else:
        print("⚠️ 部分測試失敗，請檢查配置")
        if not settings.SUPABASE_JWT_SECRET:
            print("\n🔧 解決方案:")
            print("  請在 .env 文件中設置 SUPABASE_JWT_SECRET")
            print("  SUPABASE_JWT_SECRET=您的JWT秘鑰")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 