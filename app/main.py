# app/main.py

from fastapi import FastAPI

# 1. 기능별 라우터 import
from app.feature.llm import llm_router
from app.feature.auth import auth_router
from app.feature.reviews import reviews_router
from app.feature.wellness import wellness_router
from app.feature.notifications import notification_router
from app.feature.offline import offline_router
from app.feature.flights import flights_router, my_flights_router
from app.feature.airlines import airline_router
from app.feature.users import user_router
from app.feature.flights.flights_router import search_router
from app.feature.uploads import upload_router

# 2. Firebase 초기화 실행
from app.core import firebase

# 3. 커스텀 예외 핸들러 import
from app.core.exceptions.exceptions import CustomException
from app.core.exceptions.exception_handlers import custom_exception_handler

# 4. 오프라인 기능 import
from contextlib import asynccontextmanager
from app.core.network_monitor import NetworkMonitor
from app.feature.offline.local_db import LocalDatabase
from app.feature.offline.sync_queue import SyncQueue
from app.feature.offline.cache_service import CacheService
from app.feature.offline.offline_service import OfflineService


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    애플리케이션 lifespan 관리
    서비스 초기화 및 정리를 담당합니다.
    """
    # ==========================================================================
    # 서비스 초기화
    # ==========================================================================
    print("[*] Services initializing...")
    
    # 1. 코어 서비스 초기화
    # -------------------------
    # Firebase
    from app.core.firebase import get_firebase_service
    firebase_service = get_firebase_service()
    firebase_service.initialize()
    app.state.firebase_service = firebase_service
    print("[OK] Firebase initialized")
    
    # Duffel 클라이언트 (lazy initialization으로 필요시 초기화됨)
    from app.core.clients.duffel import get_duffel_client
    app.state.duffel_client = get_duffel_client()
    print("[OK] Duffel client ready")
    
    # Ollama 클라이언트 (lazy initialization으로 필요시 초기화됨)
    from app.feature.llm.ollama_client import get_ollama_client
    app.state.ollama_client = get_ollama_client()
    print("[OK] Ollama client ready")

    
    # 2. 네트워크 모니터링 서비스
    # -------------------------
    network_monitor = NetworkMonitor()
    await network_monitor.start_monitoring(interval=30)
    app.state.network_monitor = network_monitor
    print("[OK] Network monitor started")
    
    # 3. 오프라인 관련 서비스
    # -------------------------
    # LocalDatabase
    local_db = LocalDatabase()
    
    # SyncQueue (의존성 주입 적용)
    sync_queue = SyncQueue(network_monitor=network_monitor)
    
    # CacheService (의존성 주입 적용)
    cache_service = CacheService(network_monitor=network_monitor)
    
    # OfflineService (의존성 주입)
    offline_service = OfflineService(
        local_db=local_db,
        network_monitor=network_monitor,
        sync_queue=sync_queue,
        cache_service=cache_service
    )
    app.state.offline_service = offline_service
    print("[OK] Offline services initialized")
    
    print("[OK] All services started successfully.\n")
    
    yield
    
    # ==========================================================================
    # 서비스 종료 및 정리
    # ==========================================================================
    print("\n[*] Services shutting down...")
    await network_monitor.stop_monitoring()
    print("[OK] All services stopped.")



# 4. FastAPI 앱 인스턴스 생성
app = FastAPI(
    title="BIMO-BE Project",
    description="BIMO-BE FastAPI 서버입니다.",
    version="0.1.0",
    lifespan=lifespan
)

# 5. 커스텀 예외 핸들러 등록
app.add_exception_handler(CustomException, custom_exception_handler)


# 6. 루트 엔드포인트 (서버 동작 확인용)
@app.get("/")
def read_root():
    return {"Hello": "Welcome to BIMO-BE API"}


# 5. 기능별 라우터 등록

app.include_router(auth_router.router)
app.include_router(user_router.router)
app.include_router(llm_router.router)
app.include_router(reviews_router.router)
app.include_router(wellness_router.router)
app.include_router(notification_router.router)
app.include_router(offline_router.router)
app.include_router(flights_router.router)
app.include_router(my_flights_router.router)
app.include_router(airline_router.router)
app.include_router(search_router)  # POST /search/airlines
app.include_router(upload_router.router)  # POST /uploads/images/base64