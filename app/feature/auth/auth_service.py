"""
인증 서비스 모듈
각 프로바이더별 인증 로직을 통합 관리합니다.
"""

from fastapi.concurrency import run_in_threadpool
from app.feature.auth.providers import (
    GoogleAuthProvider,
    AppleAuthProvider,
    KakaoAuthProvider,
)
from app.core.security import decode_refresh_token, create_access_token
from app.core.firebase import FirebaseService
from app.core.exceptions.exceptions import (
    InvalidTokenError,
    UserProfileNotFoundError,
    DatabaseError,
    CustomException,
)

class AuthService:
    """인증 관련 비즈니스 로직을 처리하는 서비스 클래스"""

    def __init__(self, firebase_service: FirebaseService):
        """
        AuthService 초기화
        
        Args:
            firebase_service: Firebase 서비스 인스턴스
        """
        self.db = firebase_service.db
        self.user_collection = self.db.collection("users")

    async def authenticate_with_google(self, token: str, fcm_token: str | None = None) -> dict:
        """
        Google 로그인을 처리합니다.
        
        Args:
            token: 클라이언트로부터 받은 Firebase ID Token
            fcm_token: FCM 디바이스 토큰 (선택사항)
            
        Returns:
            인증 결과 딕셔너리
        """
        return await GoogleAuthProvider.authenticate(token, fcm_token=fcm_token)

    async def authenticate_with_apple(self, token: str, fcm_token: str | None = None) -> dict:
        """
        Apple 로그인을 처리합니다.
        
        Args:
            token: 클라이언트로부터 받은 Firebase ID Token
            fcm_token: FCM 디바이스 토큰 (선택사항)
            
        Returns:
             인증 결과 딕셔너리
        """
        return await AppleAuthProvider.authenticate(token, fcm_token=fcm_token)

    async def authenticate_with_kakao(
        self,
        token: str,
        fcm_token: str | None = None,
        kakao_id: str | None = None,
        email: str | None = None,
        display_name: str | None = None,
        photo_url: str | None = None
    ) -> dict:
        """
        Kakao 로그인을 처리합니다.
        
        Args:
            token: 클라이언트로부터 받은 Kakao Access Token
            fcm_token: FCM 디바이스 토큰 (선택사항)
            kakao_id: 카카오 사용자 ID
            email: 이메일
            display_name: 닉네임
            photo_url: 프로필 사진 URL
            
        Returns:
             인증 결과 딕셔너리
        """
        return await KakaoAuthProvider.authenticate(
            token=token,
            fcm_token=fcm_token,
            kakao_id=kakao_id,
            email=email,
            display_name=display_name,
            photo_url=photo_url
        )

    async def refresh_access_token(self, refresh_token: str) -> dict:
        """
        Refresh Token을 검증하여 새로운 Access Token을 발급합니다.
        
        Args:
            refresh_token: Refresh Token
            
        Returns:
            새로운 Access Token 정보
        """
        # 1. Refresh Token 검증 및 디코딩
        payload = decode_refresh_token(refresh_token)
        uid = payload.get("sub")
        
        if not uid:
            raise InvalidTokenError(message="토큰에 사용자 식별자가 없습니다.")

        # 2. 사용자 존재 여부 확인 (Firestore)
        try:
            user_ref = self.user_collection.document(uid)
            user_doc = await run_in_threadpool(user_ref.get)
            
            if not user_doc.exists:
                raise UserProfileNotFoundError()
                
            # 필요한 경우 사용자 상태(활성/정지 등)를 여기서 체크할 수 있습니다.
            
        except Exception as e:
            if isinstance(e, CustomException):
                raise e
            raise DatabaseError(message=f"사용자 확인 중 오류 발생: {e}")

        # 3. 새로운 Access Token 발급
        new_access_token = create_access_token(data={"sub": uid})
        
        return {
            "access_token": new_access_token,
            "token_type": "bearer"
        }