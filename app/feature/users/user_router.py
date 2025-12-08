from fastapi import APIRouter, Depends, Header, HTTPException
from app.feature.users.user_service import UserService
from app.feature.users.models import UserProfile, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])

def get_user_service():
    return UserService()

async def get_current_user_id(authorization: str = Header(None)) -> str:
    if not authorization:
        return "demo_user_123"
    token = authorization.replace("Bearer ", "")
    return token.replace("demo_token_", "")

@router.get("/me", response_model=UserProfile)
async def get_my_profile(
    user_id: str = Depends(get_current_user_id),
    service: UserService = Depends(get_user_service)
):
    """내 정보 조회"""
    profile = await service.get_user_profile(user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="User not found")
    return profile

@router.put("/me", response_model=UserProfile)
async def update_my_profile(
    update_data: UserUpdate,
    user_id: str = Depends(get_current_user_id),
    service: UserService = Depends(get_user_service)
):
    """내 정보 수정 (닉네임, 수면패턴)"""
    return await service.update_user(user_id, update_data)
