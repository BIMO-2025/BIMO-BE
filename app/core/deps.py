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
    from app.core.clients.duffel import DuffelClient
    from app.feature.llm.gemini_client import GeminiClient
    from app.feature.offline.offline_service import OfflineService

# NOTE:
# FastAPI는 의존성 함수의 타입 힌트를 런타임에 eval 할 수 있습니다
# (특히 Python 3.13 환경에서 inspect.signature(..., eval_str=True) 경로).
# 따라서 ForwardRef("FirebaseService") 같은 문자열 타입을 쓰면,
# 해당 심볼이 모듈 전역에 실제로 존재하지 않을 경우 NameError로 앱 부팅이 실패합니다.
#
# 순환 참조를 피하면서도 부팅을 안정화하기 위해, 핵심 타입은 런타임에도 import 해둡니다.
from app.core.firebase import FirebaseService
from app.core.clients.duffel import DuffelClient
from app.feature.llm.gemini_client import GeminiClient
from app.feature.llm.llm_service import LLMService
from app.feature.wellness.wellness_service import WellnessService
from app.feature.reviews.review_filter_service import ReviewFilterService
from app.feature.reviews.review_summary_service import ReviewSummaryService


# =============================================================================
# 설정 의존성
# =============================================================================

def get_config() -> Settings:
    """앱 설정 객체 반환"""
    return get_settings()


# =============================================================================
# 코어 서비스 의존성
# =============================================================================

def get_firebase_service() -> FirebaseService:
    """
    Firebase 서비스 반환
    
    Returns:
        FirebaseService 인스턴스
    """
    from app.core.firebase import get_firebase_service as _get_firebase
    return _get_firebase()


def get_duffel_client() -> DuffelClient:
    """
    Duffel 클라이언트 반환
    
    Returns:
        DuffelClient 인스턴스
    """
    from app.core.clients.duffel import get_duffel_client as _get_duffel
    return _get_duffel()


def get_gemini_client() -> GeminiClient:
    """
    Gemini 클라이언트 반환
    
    Returns:
        GeminiClient 인스턴스
    """
    from app.feature.llm.gemini_client import get_gemini_client as _get_gemini
    return _get_gemini()


# =============================================================================
# LLM 서비스 의존성
# =============================================================================

def get_llm_service() -> "LLMService":
    """
    LLM 서비스 반환
    
    Returns:
        LLMService 인스턴스
    """
    gemini_client = get_gemini_client()
    return LLMService(gemini_client=gemini_client)


def get_wellness_service() -> "WellnessService":
    """
    Wellness 서비스 반환
    
    Returns:
        WellnessService 인스턴스
    """
    llm_service = get_llm_service()
    return WellnessService(llm_service=llm_service)


def get_review_filter_service() -> "ReviewFilterService":
    """
    ReviewFilterService 반환
    """
    return ReviewFilterService()


def get_review_summary_service() -> "ReviewSummaryService":
    """
    ReviewSummaryService 반환
    """
    llm_service = get_llm_service()
    return ReviewSummaryService(llm_service=llm_service)


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

