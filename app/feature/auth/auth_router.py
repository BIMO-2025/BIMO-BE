"""
인증 라우터 모듈
각 소셜 로그인 프로바이더별 엔드포인트를 제공합니다.
"""

from fastapi import APIRouter
from app.feature.auth import auth_schemas, auth_service

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
    responses={404: {"description": "Not found"}},
)


async def _handle_social_login(
    authenticate_func,
    request: auth_schemas.SocialLoginRequest
) -> auth_schemas.TokenResponse:
    """소셜 로그인 공통 핸들러"""
    result = await authenticate_func(request.token, fcm_token=request.fcm_token)
    return auth_schemas.TokenResponse(
        access_token=result["access_token"],
        token_type=result["token_type"]
    )


@router.post("/google/login", response_model=auth_schemas.TokenResponse)
async def login_with_google(request: auth_schemas.SocialLoginRequest):
    """
    Google 로그인 엔드포인트
    
    클라이언트로부터 받은 Google Firebase ID Token을 검증하고,
    API Access Token을 발급합니다.
    
    - **token**: Google Firebase ID Token (클라이언트에서 Firebase SDK로 발급받은 토큰)
    
    Returns:
        - **access_token**: 우리 서비스 전용 JWT 토큰
        - **token_type**: "bearer"
    """
    return await _handle_social_login(auth_service.authenticate_with_google, request)


@router.post("/apple/login", response_model=auth_schemas.TokenResponse)
async def login_with_apple(request: auth_schemas.SocialLoginRequest):
    """
    Apple 로그인 엔드포인트
    
    클라이언트로부터 받은 Apple Firebase ID Token을 검증하고,
    API Access Token을 발급합니다.
    
    - **token**: Apple Firebase ID Token (클라이언트에서 Firebase SDK로 발급받은 토큰)
    
    Returns:
        - **access_token**: 우리 서비스 전용 JWT 토큰
        - **token_type**: "bearer"
    """
    return await _handle_social_login(auth_service.authenticate_with_apple, request)


@router.post("/kakao/login", response_model=auth_schemas.TokenResponse)
async def login_with_kakao(request: auth_schemas.SocialLoginRequest):
    """
    Kakao 로그인 엔드포인트
    
    클라이언트로부터 받은 Kakao Access Token을 검증하고,
    Firebase Auth 사용자를 생성/조회한 뒤 API Access Token을 발급합니다.
    
    - **token**: Kakao Access Token (Kakao SDK로 발급받은 토큰)
    
    Returns:
        - **access_token**: 우리 서비스 전용 JWT 토큰
        - **token_type**: "bearer"
    """
    return await _handle_social_login(auth_service.authenticate_with_kakao, request)
