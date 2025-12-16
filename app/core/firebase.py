"""
Firebase Admin SDK 초기화 및 관리

이 모듈은 Firebase Firestore와 Auth 클라이언트를 제공합니다.
"""

import json
import os
import firebase_admin
from firebase_admin import auth, credentials, firestore
from typing import Optional

from app.core.config import settings
from app.core.exceptions.exceptions import AppConfigError


class FirebaseService:
    """Firebase Admin SDK 서비스 클래스"""
    
    def __init__(self):
        """Firebase 서비스 초기화 (실제 연결은 initialize() 호출 시)"""
        self._db: Optional[firestore.Client] = None
        self._auth_client = None
        self._initialized = False
    
    def initialize(self) -> None:
        """
        Firebase Admin SDK를 초기화합니다.
        
        Raises:
            AppConfigError: 초기화 실패 시
        """
        if self._initialized:
            print("Firebase는 이미 초기화되었습니다.")
            return
        
        # 1. .env 설정 확인 (Fail Fast 1)
        # 새 프로젝트 키를 우선 사용, 없으면 기존 키 사용
        service_key_path = settings.FIREBASE_SERVICE_ACCOUNT_KEY
        
        if not service_key_path:
            raise AppConfigError(
                "환경 변수 'FIREBASE_NEW_SERVICE_ACCOUNT_KEY' 또는 'FIREBASE_SERVICE_ACCOUNT_KEY'가 설정되지 않았습니다. .env 파일을 확인하세요."
            )
        
        try:
            # 2. 서비스 키 처리: 파일 경로 vs JSON 문자열 자동 감지
            if service_key_path.strip().startswith('{'):
                # JSON 문자열인 경우 (Render 환경 변수)
                try:
                    service_account_info = json.loads(service_key_path)
                    cred = credentials.Certificate(service_account_info)
                    print("[INFO] Firebase 서비스 키를 JSON 문자열로 로드했습니다.")
                except json.JSONDecodeError as e:
                    raise AppConfigError(f"Firebase 서비스 키 JSON 파싱 실패: {e}")
            else:
                # 파일 경로인 경우 (로컬 개발 환경)
                if not os.path.exists(service_key_path):
                    raise AppConfigError(
                        f"Firebase 서비스 키 파일을 찾을 수 없습니다. 경로를 확인하세요: {service_key_path}"
                    )
                cred = credentials.Certificate(service_key_path)
                print(f"[INFO] Firebase 서비스 키를 파일에서 로드했습니다: {service_key_path}")
            
            # 3. Firebase Admin SDK 초기화 (Fail Fast 3)
            # 이미 초기화된 경우 기존 앱 사용
            try:
                firebase_admin.initialize_app(cred)
            except ValueError as init_error:
                # 이미 초기화된 경우
                if "already exists" in str(init_error):
                    print("Firebase 앱이 이미 존재합니다. 기존 앱을 사용합니다.")
                else:
                    raise
            
            # 4. 클라이언트 생성
            self._db = firestore.client()
            self._auth_client = auth
            self._initialized = True
            
            print("[OK] Firebase Admin SDK가 성공적으로 초기화되었습니다. (Firestore, Auth)")
        
        except ValueError as e:
            # credentials.Certificate()가 실패한 경우
            raise AppConfigError(f"Firebase 서비스 키가 유효하지 않습니다: {e}")
        except AppConfigError:
            # 이미 AppConfigError로 래핑된 경우 그대로 전달
            raise
        except Exception as e:
            # 기타 알 수 없는 오류
            raise AppConfigError(f"Firebase 초기화 중 알 수 없는 오류 발생: {e}")
    
    @property
    def db(self) -> firestore.Client:
        """Firestore 클라이언트 반환"""
        if not self._initialized or self._db is None:
            raise RuntimeError("Firebase가 초기화되지 않았습니다. initialize()를 먼저 호출하세요.")
        return self._db
    
    @property
    def auth_client(self):
        """Firebase Auth 클라이언트 반환"""
        if not self._initialized:
            raise RuntimeError("Firebase가 초기화되지 않았습니다. initialize()를 먼저 호출하세요.")
        return self._auth_client
    
    @property
    def is_initialized(self) -> bool:
        """초기화 여부 반환"""
        return self._initialized


# 싱글톤 인스턴스 (앱 전체에서 공유)
_firebase_service: Optional[FirebaseService] = None


def get_firebase_service() -> FirebaseService:
    """
    Firebase 서비스 싱글톤 인스턴스를 반환합니다.
    
    Returns:
        FirebaseService 인스턴스
    """
    global _firebase_service
    if _firebase_service is None:
        _firebase_service = FirebaseService()
    return _firebase_service


# =============================================================================
# 하위 호환성을 위한 모듈 레벨 변수 (deprecated)
# 새로운 코드에서는 FirebaseService 클래스를 직접 사용하세요.
# =============================================================================

# 임시로 모듈 레벨에서 초기화 (기존 코드 호환성)
try:
    _temp_service = get_firebase_service()
    _temp_service.initialize()
    
    # 기존 코드와의 호환성을 위해 모듈 레벨 변수 유지
    db = _temp_service.db
    auth_client = _temp_service.auth_client
    
except AppConfigError:
    # 초기화 실패 시 None으로 설정
    db = None
    auth_client = None
    # 에러는 재발생시켜 앱 시작 중단
    raise


__all__ = ["FirebaseService", "get_firebase_service", "db", "auth_client"]