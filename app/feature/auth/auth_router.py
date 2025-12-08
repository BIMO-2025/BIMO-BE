from fastapi import APIRouter, Depends, HTTPException
from app.feature.auth.auth_service import AuthService
from app.feature.auth.models import UserCreate, TokenResponse, LoginProvider

router = APIRouter(prefix="/auth", tags=["auth"])

def get_auth_service():
    return AuthService()

@router.post("/login/{provider}", response_model=TokenResponse)
async def login(
    provider: LoginProvider,
    user_data: UserCreate, # 실제로는 소셜 토큰을 받아 서버에서 검증해야 함. 여기선 데모용으로 직접 데이터 받음.
    service: AuthService = Depends(get_auth_service)
):
    """
    간편 로그인 (카카오, 구글, 애플)
    - 클라이언트에서 소셜 로그인 성공 후 정보를 전달 (데모 버전)
    """
    if provider != user_data.provider:
        raise HTTPException(status_code=400, detail="Provider mismatch")
        
    user = await service.login_or_register(user_data)
    
    # JWT 토큰 발급 로직은 생략 (데모: user_id를 토큰처럼 사용)
    return TokenResponse(
        access_token=f"demo_token_{user.id}",
        token_type="bearer",
        user=user
    )