"""
Apple 로그인 전용 인증 프로바이더
"""

from app.feature.auth.providers.firebase_provider import FirebaseAuthProvider
from app.shared.schemas import UserInDB


class AppleAuthProvider(FirebaseAuthProvider):
    """Apple 로그인을 처리하는 프로바이더"""

    @classmethod
    async def verify_token(cls, token: str) -> dict:
        """
        [비동기 함수] Apple Firebase ID Token을 검증합니다.
        
        Args:
            token: 클라이언트로부터 받은 Firebase ID Token
            
        Returns:
            검증된 토큰의 디코딩된 정보 (uid, email, name, picture 등)
        """
        return await super().verify_token(token)

    @classmethod
    async def get_or_create_user(cls, decoded_token: dict, fcm_token: str | None = None) -> UserInDB:
        """
        [비동기 함수] Apple 사용자 정보를 바탕으로 Firestore에서 사용자를 조회하거나 생성합니다.
        
        Args:
            decoded_token: verify_token에서 반환된 디코딩된 토큰 정보
            
        Returns:
            Firestore에 저장된 사용자 정보 (UserInDB)
        """
        return await super().get_or_create_user(decoded_token, provider_name="Apple", fcm_token=fcm_token)

    @classmethod
    async def authenticate(cls, token: str, fcm_token: str | None = None) -> dict:
        """
        [비동기 함수] Apple 로그인 전체 프로세스를 처리합니다.
        
        Args:
            token: 클라이언트로부터 받은 Firebase ID Token
            fcm_token: FCM 디바이스 토큰 (선택사항)
            
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

