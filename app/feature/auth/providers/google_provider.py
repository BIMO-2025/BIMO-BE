"""
Google 로그인 전용 인증 프로바이더
"""

from google.oauth2 import id_token
from google.auth.transport import requests

from app.feature.auth.providers.firebase_provider import FirebaseAuthProvider
from app.shared.schemas import UserInDB
from app.core.config import settings
from app.core.exceptions.exceptions import (
    TokenVerificationError,
    InvalidTokenError,
    TokenExpiredError
)


class GoogleAuthProvider(FirebaseAuthProvider):
    """Google 로그인을 처리하는 프로바이더"""

    @classmethod
    async def verify_token(cls, token: str) -> dict:
        """
        [비동기 함수] Google Firebase ID Token을 검증합니다.
        
        실패 시, Google iOS Client ID에 대한 직접 검증을 시도합니다.
        (iOS 앱에서 받은 토큰이 Firebase 프로젝트의 Audience와 일치하지 않는 경우 대비)

        Args:
            token: 클라이언트로부터 받은 Firebase ID Token 또는 Google ID Token
            
        Returns:
            검증된 토큰의 디코딩된 정보 (uid, email, name, picture 등)
        """
        try:
            # 1차 시도: Firebase Admin SDK를 통한 검증
            return await super().verify_token(token)
        except (TokenVerificationError, InvalidTokenError, TokenExpiredError) as e:
            # 2차 시도: Google iOS Client ID 직접 검증 (Fallback)
            if not settings.GOOGLE_IOS_CLIENT_ID:
                raise e
            
            try:
                # 동기 함수이므로 스레드풀에서 실행하는 것이 좋으나, 
                # google-auth 라이브러리의 verify_oauth2_token은 HTTP 요청을 포함하므로
                # 여기서는 간단히 직접 호출하거나, 성능이 중요하다면 run_in_threadpool 사용 고려
                # (현재 구조상 verify_token은 async이므로 바로 호출해도 무방하나, 블로킹 방지 위해)
                from fastapi.concurrency import run_in_threadpool
                
                def verify_google_token_sync():
                    return id_token.verify_oauth2_token(
                        token, 
                        requests.Request(), 
                        audience=settings.GOOGLE_IOS_CLIENT_ID
                    )

                id_info = await run_in_threadpool(verify_google_token_sync)
                
                # Google ID Token 정보를 Firebase User 포맷으로 변환
                # Google ID Token claims: https://developers.google.com/identity/protocols/oauth2/openid-connect#an-id-tokens-payload
                return {
                    "uid": id_info.get("sub"),  # Google 고유 사용자 ID
                    "email": id_info.get("email"),
                    "name": id_info.get("name"),
                    "picture": id_info.get("picture"),
                    "firebase": {
                        "sign_in_provider": "google.com",
                        "identities": {
                            "google.com": [id_info.get("sub")]
                        }
                    }
                }
            except Exception as google_error:
                # Fallback 실패 시 원래의 Firebase 에러 또는 새로운 에러 로깅
                print(f"Google iOS Token verification failed: {google_error}")
                raise e  # 원래 발생했던 Firebase 에러를 던짐 (또는 구체적인 에러로 변경 가능)

    @classmethod
    async def get_or_create_user(cls, decoded_token: dict, fcm_token: str | None = None) -> UserInDB:
        """
        [비동기 함수] Google 사용자 정보를 바탕으로 Firestore에서 사용자를 조회하거나 생성합니다.
        
        Args:
            decoded_token: verify_token에서 반환된 디코딩된 토큰 정보
            
        Returns:
            Firestore에 저장된 사용자 정보 (UserInDB)
        """
        return await super().get_or_create_user(decoded_token, provider_name="Google", fcm_token=fcm_token)

    @classmethod
    async def authenticate(cls, token: str, fcm_token: str | None = None) -> dict:
        """
        [비동기 함수] Google 로그인 전체 프로세스를 처리합니다.
        
        Args:
            token: 클라이언트로부터 받은 Firebase ID Token
            
        Returns:
            {
                "access_token": "JWT 토큰",
                "token_type": "bearer",
                "user": UserInDB 객체
            }
        """
        # 1. 토큰 검증
        decoded_token = await cls.verify_token(token)

        # 2. 사용자 조회 또는 생성
        user = await cls.get_or_create_user(decoded_token, fcm_token=fcm_token)

        # 3. API 토큰 생성
        api_access_token = cls.generate_api_token(uid=user.uid)

        return {
            "access_token": api_access_token,
            "token_type": "bearer",
            "user": user
        }

