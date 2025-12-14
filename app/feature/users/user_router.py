"""
사용자 관련 라우터 모듈
"""

from fastapi import APIRouter, Depends, HTTPException, Header
from typing import Optional

from app.feature.users import users_schemas
from app.feature.users.user_service import UserService
from app.feature.auth.auth_schemas import UserInfo
from app.core.security import decode_access_token
from app.core.exceptions.exceptions import (
    InvalidTokenError,
    UserProfileNotFoundError,
    DatabaseError,
)

router = APIRouter(
    prefix="/user",
    tags=["User"],
    responses={404: {"description": "Not found"}},
)


async def get_current_user_id(authorization: Optional[str] = Header(None)) -> str:
    """
    JWT 토큰에서 사용자 ID를 추출합니다.
    
    Args:
        authorization: Authorization 헤더 (Bearer 토큰)
        
    Returns:
        사용자 UID
        
    Raises:
        HTTPException: 토큰이 유효하지 않을 때
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization 헤더가 필요합니다.")
    
    # "Bearer " 제거
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authorization 헤더 형식이 올바르지 않습니다.")
    
    token = authorization.replace("Bearer ", "").strip()
    
    try:
        payload = decode_access_token(token)  # 우리 서비스 JWT 디코딩
        uid = payload.get("sub")
        
        if not uid:
            raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다.")
        
        return uid
        
    except InvalidTokenError:
        raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다.")


@router.put("/nickname", response_model=users_schemas.UpdateNicknameResponse)
async def update_nickname(
    request: users_schemas.UpdateNicknameRequest,
    uid: str = Depends(get_current_user_id)
):
    """
    사용자 닉네임을 업데이트합니다.
    
    - **nickname**: 설정할 닉네임 (1-50자)
    
    Returns:
        - **success**: 성공 여부
        - **message**: 결과 메시지
        - **user**: 업데이트된 사용자 정보
    """
    try:
        # 닉네임 유효성 검사
        nickname = request.nickname.strip()
        if not nickname:
            raise HTTPException(status_code=400, detail="닉네임은 공백일 수 없습니다.")
        
        if len(nickname) > 50:
            raise HTTPException(status_code=400, detail="닉네임은 50자를 초과할 수 없습니다.")
        
        # 서비스를 통해 닉네임 업데이트
        updated_user = await UserService.update_display_name(
            uid=uid,
            display_name=nickname
        )
        
        # 응답 형식 변환
        user_info = UserInfo(
            uid=updated_user.uid,
            email=updated_user.email,
            display_name=updated_user.display_name,
            photo_url=updated_user.photo_url,
            provider_id=updated_user.provider_id
        )
        
        return users_schemas.UpdateNicknameResponse(
            success=True,
            message="닉네임이 성공적으로 업데이트되었습니다.",
            user=user_info
        )
        
    except UserProfileNotFoundError:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"서버 오류가 발생했습니다: {str(e)}")

