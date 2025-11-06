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
    """
    try:
        # 1. Google ID Token 검증
        decoded_token = await auth_service.verify_google_id_token(request.token)

        # 2. 사용자 조회 또는 생성
        user = await auth_service.get_or_create_user(decoded_token)

        # 3. 우리 서비스 전용 API 토큰 생성
        api_access_token = auth_service.generate_api_token(uid=user.uid)

        return {
            "access_token": api_access_token,
            "token_type": "bearer"
        }

    except HTTPException as e:
        # 서비스 로직에서 발생한 HTTPException을 그대로 반환
        raise e
    except Exception as e:
        # 그 외 예외 처리
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"로그인 처리 중 알 수 없는 오류 발생: {e}"
        )

# 참고: Kakao, Apple 로그인 라우터도 비슷한 구조로 추가할 수 있습니다.
# 예: @router.post("/kakao/login")
# Apple 로그인은 검증 방식이 조금 더 복잡할 수 있습니다. (Firebase 사용 시 유사)