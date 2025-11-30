"""
Firebase Cloud Messaging (FCM) 푸시 알림 전송 모듈
"""
from typing import List, Optional, Dict
from fastapi.concurrency import run_in_threadpool
from firebase_admin import messaging

from app.core.exceptions.exceptions import ExternalApiError, CustomException


async def send_notification(
    fcm_tokens: List[str],
    title: str,
    body: str,
    data: Optional[Dict[str, str]] = None,
    image_url: Optional[str] = None,
) -> messaging.BatchResponse:
    """
    FCM 푸시 알림을 전송합니다.
    
    Args:
        fcm_tokens: FCM 디바이스 토큰 목록
        title: 알림 제목
        body: 알림 본문
        data: 추가 데이터 (키-값 쌍)
        image_url: 알림 이미지 URL (선택사항)
        
    Returns:
        BatchResponse: 전송 결과
        
    Raises:
        ExternalApiError: FCM 전송 실패
    """
    if not fcm_tokens:
        raise ValueError("FCM 토큰 목록이 비어있습니다.")
    
    try:
        # 알림 객체 생성
        notification = messaging.Notification(
            title=title,
            body=body,
            image=image_url if image_url else None
        )
        
        # 메시지 생성
        message = messaging.MulticastMessage(
            notification=notification,
            data=data or {},
            tokens=fcm_tokens,
            android=messaging.AndroidConfig(
                priority="high"
            ),
            apns=messaging.APNSConfig(
                payload=messaging.APNSPayload(
                    aps=messaging.Aps(
                        sound="default",
                        badge=1
                    )
                )
            )
        )
        
        # 동기 함수로 전송 (run_in_threadpool 사용)
        response = await run_in_threadpool(messaging.send_multicast, message)
        
        return response
        
    except Exception as e:
        if isinstance(e, CustomException):
            raise e
        raise ExternalApiError(
            provider="FCM",
            message=f"FCM 알림 전송 실패: {e}"
        )


async def send_notification_to_user(
    user_fcm_tokens: List[str],
    title: str,
    body: str,
    data: Optional[Dict[str, str]] = None,
    image_url: Optional[str] = None,
) -> Dict:
    """
    사용자의 모든 디바이스에 알림을 전송합니다.
    
    Args:
        user_fcm_tokens: 사용자의 FCM 토큰 목록
        title: 알림 제목
        body: 알림 본문
        data: 추가 데이터
        image_url: 알림 이미지 URL
        
    Returns:
        {
            "success_count": int,
            "failure_count": int,
            "responses": List
        }
    """
    if not user_fcm_tokens:
        return {
            "success_count": 0,
            "failure_count": 0,
            "responses": [],
            "message": "FCM 토큰이 없습니다."
        }
    
    try:
        response = await send_notification(
            fcm_tokens=user_fcm_tokens,
            title=title,
            body=body,
            data=data,
            image_url=image_url
        )
        
        return {
            "success_count": response.success_count,
            "failure_count": response.failure_count,
            "responses": [
                {
                    "success": resp.success,
                    "message_id": resp.message_id if resp.success else None,
                    "error": str(resp.exception) if resp.exception else None
                }
                for resp in response.responses
            ]
        }
    except Exception as e:
        return {
            "success_count": 0,
            "failure_count": len(user_fcm_tokens),
            "responses": [],
            "error": str(e)
        }

