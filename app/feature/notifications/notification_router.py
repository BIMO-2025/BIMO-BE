"""
알림 라우터
"""
from fastapi import APIRouter, Depends, HTTPException, Header
from typing import Optional

from app.feature.notifications import notification_schemas, notification_service
from app.core.security import decode_access_token
from app.core.exceptions.exceptions import InvalidTokenError

router = APIRouter(
    prefix="/notifications",
    tags=["Notifications"],
    responses={404: {"description": "Not found"}},
)


def get_current_user_id(authorization: Optional[str] = Header(None)) -> str:
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
    token = authorization.replace("Bearer ", "").strip()
    
    try:
        payload = decode_access_token(token)
        uid = payload.get("sub")
        
        if not uid:
            raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다.")
        
        return uid
        
    except InvalidTokenError:
        raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다.")


@router.post("/send")
async def send_notification(
    request: notification_schemas.SendNotificationRequest,
    uid: str = Depends(get_current_user_id),
):
    """
    특정 사용자에게 알림을 전송합니다.
    
    - **uid**: 사용자 UID
    - **title**: 알림 제목
    - **body**: 알림 본문
    - **data**: 추가 데이터 (선택사항)
    - **image_url**: 알림 이미지 URL (선택사항)
    """
    result = await notification_service.send_notification_to_user_by_uid(
        uid=uid,
        title=request.title,
        body=request.body,
        data=request.data,
        image_url=request.image_url
    )
    
    return {
        "success_count": result["success_count"],
        "failure_count": result["failure_count"],
        "message": "알림 전송 완료" if result["success_count"] > 0 else "알림 전송 실패"
    }


@router.post("/token/update")
async def update_fcm_token(
    request: notification_schemas.UpdateFCMTokenRequest,
    uid: str = Depends(get_current_user_id),
):
    """
    현재 사용자의 FCM 토큰을 업데이트합니다.
    
    - **fcm_token**: FCM 디바이스 토큰
    
    Authorization 헤더에 JWT 토큰이 필요합니다.
    """
    success = await notification_service.update_user_fcm_token(uid, request.fcm_token)
    
    if success:
        return {"message": "FCM 토큰이 업데이트되었습니다."}
    else:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")


@router.post("/token/remove")
async def remove_fcm_token(
    request: notification_schemas.UpdateFCMTokenRequest,
    uid: str = Depends(get_current_user_id),
):
    """
    현재 사용자의 FCM 토큰을 제거합니다 (로그아웃 시 사용).
    
    - **fcm_token**: 제거할 FCM 디바이스 토큰
    
    Authorization 헤더에 JWT 토큰이 필요합니다.
    """
    success = await notification_service.remove_user_fcm_token(uid, request.fcm_token)
    
    if success:
        return {"message": "FCM 토큰이 제거되었습니다."}
    else:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

