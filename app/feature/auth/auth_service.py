"""
인증 서비스 모듈
각 프로바이더별 인증 로직을 통합 관리합니다.
"""

from app.feature.auth.providers import (
    GoogleAuthProvider,
    AppleAuthProvider,
    KakaoAuthProvider,
)

# ============================================
# 각 프로바이더별 인증 함수
# ============================================


async def authenticate_with_google(token: str) -> dict:
    """
    Google 로그인을 처리합니다.
    
    Args:
        token: 클라이언트로부터 받은 Firebase ID Token
        
    Returns:
        {
            "access_token": "JWT 토큰",
            "token_type": "bearer",
            "user": UserInDB 객체
        }
    """
    return await GoogleAuthProvider.authenticate(token)


async def authenticate_with_apple(token: str) -> dict:
    """
    Apple 로그인을 처리합니다.
    
    Args:
        token: 클라이언트로부터 받은 Firebase ID Token
        
    Returns:
        {
            "access_token": "JWT 토큰",
            "token_type": "bearer",
            "user": UserInDB 객체
        }
    """
    return await AppleAuthProvider.authenticate(token)


async def authenticate_with_kakao(token: str) -> dict:
    """
    Kakao 로그인을 처리합니다.
    
    Args:
        token: 클라이언트로부터 받은 Kakao Access Token
        
    Returns:
        {
            "access_token": "JWT 토큰",
            "token_type": "bearer",
            "user": UserInDB 객체
        }
    """
    return await KakaoAuthProvider.authenticate(token)


# ============================================
# 하위 호환성을 위한 레거시 함수들
# (기존 코드와의 호환성을 위해 유지)
# ============================================


async def verify_firebase_id_token(token: str) -> dict:
    """
    [레거시 함수] Firebase ID Token을 검증합니다.
    Google/Apple 공용으로 사용됩니다.
    
    Deprecated: GoogleAuthProvider.verify_token 또는 AppleAuthProvider.verify_token 사용을 권장합니다.
    """
    return await GoogleAuthProvider.verify_token(token)


async def verify_kakao_token(token: str) -> dict:
    """
    [레거시 함수] Kakao Access Token을 검증하고 사용자 정보를 가져옵니다.
    
    Deprecated: KakaoAuthProvider.verify_token 사용을 권장합니다.
    """
    return await KakaoAuthProvider.verify_token(token)


def generate_api_token(uid: str) -> str:
    """
    [레거시 함수] 우리 서비스 전용 API Access Token (JWT)을 생성합니다.
    
    Deprecated: 각 프로바이더의 generate_api_token 메서드 사용을 권장합니다.
    """
    return GoogleAuthProvider.generate_api_token(uid)