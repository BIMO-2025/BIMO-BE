"""
알림 서비스
"""
from typing import List, Optional, Dict
from fastapi.concurrency import run_in_threadpool

from app.core.firebase import db
from app.core.fcm import send_notification_to_user
from app.core.exceptions.exceptions import DatabaseError, CustomException

# Firestore 'users' 컬렉션 참조
user_collection = db.collection("users")


async def get_user_fcm_tokens(uid: str) -> List[str]:
    """
    사용자의 FCM 토큰 목록을 가져옵니다.
    
    Args:
        uid: 사용자 UID
        
    Returns:
        FCM 토큰 목록
    """
    try:
        user_ref = user_collection.document(uid)
        user_doc = await run_in_threadpool(user_ref.get)
        
        if not user_doc.exists:
            return []
        
        user_data = user_doc.to_dict()
        return user_data.get("fcm_tokens", [])
        
    except Exception as e:
        if isinstance(e, CustomException):
            raise e
        raise DatabaseError(message=f"FCM 토큰 조회 중 오류 발생: {e}")


async def update_user_fcm_token(uid: str, fcm_token: str) -> bool:
    """
    사용자의 FCM 토큰을 업데이트합니다.
    
    Args:
        uid: 사용자 UID
        fcm_token: 새로운 FCM 토큰
        
    Returns:
        업데이트 성공 여부
    """
    try:
        user_ref = user_collection.document(uid)
        user_doc = await run_in_threadpool(user_ref.get)
        
        if not user_doc.exists:
            return False
        
        user_data = user_doc.to_dict()
        fcm_tokens = user_data.get("fcm_tokens", [])
        
        # 토큰이 없으면 추가, 있으면 유지 (중복 방지)
        if fcm_token not in fcm_tokens:
            fcm_tokens.append(fcm_token)
            await run_in_threadpool(user_ref.update, {"fcm_tokens": fcm_tokens})
        
        return True
        
    except Exception as e:
        if isinstance(e, CustomException):
            raise e
        raise DatabaseError(message=f"FCM 토큰 업데이트 중 오류 발생: {e}")


async def remove_user_fcm_token(uid: str, fcm_token: str) -> bool:
    """
    사용자의 FCM 토큰을 제거합니다 (로그아웃 시 사용).
    
    Args:
        uid: 사용자 UID
        fcm_token: 제거할 FCM 토큰
        
    Returns:
        제거 성공 여부
    """
    try:
        user_ref = user_collection.document(uid)
        user_doc = await run_in_threadpool(user_ref.get)
        
        if not user_doc.exists:
            return False
        
        user_data = user_doc.to_dict()
        fcm_tokens = user_data.get("fcm_tokens", [])
        
        # 토큰 제거
        if fcm_token in fcm_tokens:
            fcm_tokens.remove(fcm_token)
            await run_in_threadpool(user_ref.update, {"fcm_tokens": fcm_tokens})
        
        return True
        
    except Exception as e:
        if isinstance(e, CustomException):
            raise e
        raise DatabaseError(message=f"FCM 토큰 제거 중 오류 발생: {e}")


async def send_notification_to_user_by_uid(
    uid: str,
    title: str,
    body: str,
    data: Optional[Dict[str, str]] = None,
    image_url: Optional[str] = None,
) -> Dict:
    """
    사용자 UID로 알림을 전송합니다.
    
    Args:
        uid: 사용자 UID
        title: 알림 제목
        body: 알림 본문
        data: 추가 데이터
        image_url: 알림 이미지 URL
        
    Returns:
        전송 결과
    """
    fcm_tokens = await get_user_fcm_tokens(uid)
    return await send_notification_to_user(
        user_fcm_tokens=fcm_tokens,
        title=title,
        body=body,
        data=data,
        image_url=image_url
    )

