"""
중앙 의존성 주입 관리
모든 의존성 주입 함수를 이 모듈에서 관리합니다.
"""

from typing import Any, TYPE_CHECKING
from fastapi import Request, Depends

from app.core.config import get_settings, Settings

# TYPE_CHECKING을 사용하여 순환 참조 방지
if TYPE_CHECKING:
    from app.core.network_monitor import NetworkMonitor
    from app.core.firebase import FirebaseService
    from app.core.clients.amadeus import AmadeusClient
    from app.feature.llm.gemini_client import GeminiClient
    from app.feature.offline.offline_service import OfflineService


# =============================================================================
# 설정 의존성
# =============================================================================

def get_config() -> Settings:
    """앱 설정 객체 반환"""
    return get_settings()


# =============================================================================
# 코어 서비스 의존성
# =============================================================================

def get_firebase_service() -> "FirebaseService":
    """
    Firebase 서비스 반환
    
    Returns:
        FirebaseService 인스턴스
    """
    from app.core.firebase import get_firebase_service as _get_firebase
    return _get_firebase()


def get_amadeus_client() -> "AmadeusClient":
    """
    Amadeus 클라이언트 반환
    
    Returns:
        AmadeusClient 인스턴스
    """
    from app.core.clients.amadeus import get_amadeus_client as _get_amadeus
    return _get_amadeus()


def get_gemini_client() -> "GeminiClient":
    """
    Gemini 클라이언트 반환
    
    Returns:
        GeminiClient 인스턴스
    """
    from app.feature.llm.gemini_client import get_gemini_client as _get_gemini
    return _get_gemini()


# =============================================================================
# App State 의존성 (lifespan에서 초기화된 서비스)
# =============================================================================

def get_network_monitor(request: Request) -> Any:
    """
    App state에서 NetworkMonitor 인스턴스를 가져옵니다.
    반환 타입은 NetworkMonitor여야 하지만, 순환 참조 방지를 위해 Any로 둡니다.
    """
    return request.app.state.network_monitor


def get_offline_service(request: Request) -> Any:
    """
    App state에서 OfflineService 인스턴스를 가져옵니다.
    """
    return request.app.state.offline_service

