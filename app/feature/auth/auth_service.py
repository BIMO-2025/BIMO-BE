"""
인증 서비스 모듈
각 프로바이더별 인증 로직을 통합 관리합니다.
"""

from fastapi.concurrency import run_in_threadpool
from app.feature.auth.providers import (
    GoogleAuthProvider,
    AppleAuthProvider,
    KakaoAuthProvider,
)
from app.core.security import decode_refresh_token, create_access_token
from app.core.firebase import db
from app.core.exceptions.exceptions import InvalidTokenError, UserNotFoundError, DatabaseError, CustomException

user_collection = db.collection("users")

# ============================================
# 각 프로바이더별 인증 함수
# ============================================


async def authenticate_with_google(token: str, fcm_token: str | None = None) -> dict:
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
    return await GoogleAuthProvider.authenticate(token, fcm_token=fcm_token)


async def authenticate_with_apple(token: str, fcm_token: str | None = None) -> dict:
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
    return await AppleAuthProvider.authenticate(token, fcm_token=fcm_token)


async def authenticate_with_kakao(
    token: str,
    fcm_token: str | None = None,
    kakao_id: str | None = None,
    email: str | None = None,
    display_name: str | None = None,
    photo_url: str | None = None
) -> dict:
    """
    Kakao 로그인을 처리합니다.
    
    Args:
        token: 클라이언트로부터 받은 Kakao Access Token
        fcm_token: FCM 디바이스 토큰 (선택사항)
        kakao_id: 카카오 사용자 ID (선택사항, 클라이언트에서 받은 정보)
        email: 카카오 계정 이메일 (선택사항)
        display_name: 카카오 닉네임 (선택사항)
        photo_url: 카카오 프로필 이미지 URL (선택사항)
        
    Returns:
        {
            "access_token": "JWT 토큰",
            "token_type": "bearer",
            "user": UserInDB 객체
        }
    """
    return await KakaoAuthProvider.authenticate(
        token=token,
        fcm_token=fcm_token,
        kakao_id=kakao_id,
        email=email,
        display_name=display_name,
        photo_url=photo_url
    )


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


async def refresh_access_token(refresh_token: str) -> dict:
    """
    Refresh Token을 검증하여 새로운 Access Token을 발급합니다.
    
    Args:
        refresh_token: 클라이언트로부터 받은 Refresh Token
        
    Returns:
        {
            "access_token": "새로운 JWT Access Token",
            "token_type": "bearer"
        }
        
    Raises:
        InvalidTokenError: 토큰이 유효하지 않거나 사용자 식별자가 없을 때
        TokenExpiredError: 토큰이 만료되었을 때
        UserNotFoundError: 사용자가 존재하지 않을 때
        DatabaseError: 사용자 확인 중 오류 발생
    """
    # 1. Refresh Token 검증 및 디코딩
    payload = decode_refresh_token(refresh_token)
    uid = payload.get("sub")
    
    if not uid:
        raise InvalidTokenError(message="토큰에 사용자 식별자가 없습니다.")

    # 2. 사용자 존재 여부 확인 (Firestore)
    try:
        user_ref = user_collection.document(uid)
        user_doc = await run_in_threadpool(user_ref.get)
        
        if not user_doc.exists:
            raise UserNotFoundError(message="존재하지 않는 사용자입니다.")
            
        # 필요한 경우 사용자 상태(활성/정지 등)를 여기서 체크할 수 있습니다.
        
    except Exception as e:
        if isinstance(e, CustomException):
            raise e
        raise DatabaseError(message=f"사용자 확인 중 오류 발생: {e}")

    # 3. 새로운 Access Token 발급
    new_access_token = create_access_token(data={"sub": uid})
    
    return {
        "access_token": new_access_token,
        "token_type": "bearer"
    }


def generate_api_token(uid: str) -> str:
    """
    [레거시 함수] 우리 서비스 전용 API Access Token (JWT)을 생성합니다.
    
    Deprecated: 각 프로바이더의 generate_api_token 메서드 사용을 권장합니다.
    """
    tokens = GoogleAuthProvider.generate_api_token(uid)
    return tokens["access_token"]  # 하위 호환성을 위해 access_token만 반환