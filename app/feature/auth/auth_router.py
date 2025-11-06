from fastapi import APIRouter, Depends, HTTPException, status

from app.feature.auth import auth_schemas, auth_service

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
    responses={404: {"description": "Not found"}},
)


@router.post("/google/login", response_model=auth_schemas.TokenResponse)
async def login_with_google(
        request: auth_schemas.SocialLoginRequest
):
    """
    클라이언트에서 받은 Google ID Token을 검증하고,
    사용자를 확인/생성한 뒤,
    우리 서비스의 API Access Token을 발급합니다.

    이 엔드포인트는 서비스 계층(auth_service)에서 발생하는
    모든 CustomException을 자동으로 main.py의
    exception_handler가 처리하도록 위임합니다.
    """

    # 1. Google ID Token 검증
    decoded_token = await auth_service.verify_google_id_token(request.token)

    # 2. 사용자 조회 또는 생성
    user = await auth_service.get_or_create_user(decoded_token)

    # 3. 우리 서비스 전용 API 토큰 생성
    # (generate_api_token은 동기 함수이지만, I/O가 없는 CPU 작업이므로
    # run_in_threadpool이 필요하지 않습니다.)
    api_access_token = auth_service.generate_api_token(uid=user.uid)

    return {
        "access_token": api_access_token,
        "token_type": "bearer"
    }
