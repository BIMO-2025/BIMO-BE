"""
인증 라우터 모듈
각 소셜 로그인 프로바이더별 엔드포인트를 제공합니다.
"""

from fastapi import APIRouter, Depends
from app.feature.auth import auth_schemas
from app.feature.auth.auth_service import AuthService
from app.core.deps import get_auth_service

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
    responses={404: {"description": "Not found"}},
)


@router.post("/logout")
async def logout():
    """
    로그아웃 엔드포인트
    
    서버는 Stateless(JWT) 방식을 사용하므로, 이 요청은 성공 메시지만 반환합니다.
    **클라이언트에서 반드시 로컬 스토리지/쿠키의 Access Token을 삭제해야 합니다.**
    """
    return {"message": "성공적으로 로그아웃되었습니다."}


def _create_token_response(auth_result: dict) -> auth_schemas.TokenResponse:
    """인증 결과를 TokenResponse 모델로 변환하는 헬퍼 함수"""
    user_info = None
    if "user" in auth_result and auth_result["user"]:
        user = auth_result["user"]
        user_info = auth_schemas.UserInfo(
            uid=user.uid,
            email=user.email,
            display_name=user.display_name,
            photo_url=user.photo_url,
            provider_id=user.provider_id
        )
    
    return auth_schemas.TokenResponse(
        access_token=auth_result["access_token"],
        refresh_token=auth_result.get("refresh_token"),
        token_type=auth_result["token_type"],
        user=user_info
    )


@router.post("/google/login", response_model=auth_schemas.TokenResponse)
async def login_with_google(
    request: auth_schemas.SocialLoginRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Google 로그인 엔드포인트
    
    클라이언트로부터 받은 Google Firebase ID Token을 검증하고,
    API Access Token을 발급합니다.
    
    - **token**: Google Firebase ID Token
    """
    result = await auth_service.authenticate_with_google(request.token, fcm_token=request.fcm_token)
    return _create_token_response(result)


@router.post("/apple/login", response_model=auth_schemas.TokenResponse)
async def login_with_apple(
    request: auth_schemas.SocialLoginRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Apple 로그인 엔드포인트
    
    클라이언트로부터 받은 Apple Firebase ID Token을 검증하고,
    API Access Token을 발급합니다.
    
    - **token**: Apple Firebase ID Token
    """
    result = await auth_service.authenticate_with_apple(request.token, fcm_token=request.fcm_token)
    return _create_token_response(result)


@router.post("/kakao/login", response_model=auth_schemas.TokenResponse)
async def login_with_kakao(
    request: auth_schemas.SocialLoginRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Kakao 로그인 엔드포인트
    
    클라이언트로부터 받은 Kakao Access Token과 사용자 정보를 받아,
    Firebase Auth 사용자를 생성/조회한 뒤 API Access Token을 발급합니다.
    """
    result = await auth_service.authenticate_with_kakao(
        token=request.token,
        fcm_token=request.fcm_token,
        kakao_id=request.kakao_id,
        email=request.email,
        display_name=request.display_name,
        photo_url=request.photo_url
    )
    return _create_token_response(result)


@router.post("/refresh", response_model=auth_schemas.AccessTokenResponse)
async def refresh_token(
    request: auth_schemas.RefreshTokenRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Access Token 갱신 엔드포인트
    
    Refresh Token을 검증하여 새로운 Access Token을 발급합니다.
    """
    return await auth_service.refresh_access_token(request.refresh_token)
