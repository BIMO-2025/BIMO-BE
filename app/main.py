# app/main.py

from fastapi import FastAPI

# 1. 기능별 라우터 import
from app.feature.LLM import llm_router
from app.feature.auth import auth_router
from app.feature.reviews import reviews_router
from app.feature.wellness import wellness_router
from app.feature.notifications import notification_router
from app.feature.offline import offline_router
from app.feature.flights import flights_router

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
    # 1. 서비스 초기화 및 시작
    print("🚀 Services initializing...")
    
    # NetworkMonitor
    network_monitor = NetworkMonitor()
    await network_monitor.start_monitoring(interval=30)
    app.state.network_monitor = network_monitor
    
    # LocalDatabase (가정: 초기화 필요 없음 또는 간단함)
    local_db = LocalDatabase()
    
    # SyncQueue
    # 주의: SyncQueue가 내부적으로 network_monitor 등을 필요로 할 수 있음.
    # 만약 SyncQueue도 리팩토링 대상이라면 주입해줘야 함.
    # 현재는 기존 코드 호환성을 위해 최대한 유지하되, 리팩토링된 OfflineService 조립
    sync_queue = SyncQueue() # TODO: SyncQueue도 DI 적용 필요 시 수정
    
    # CacheService
    cache_service = CacheService() # TODO: CacheService도 DI 적용 필요 시 수정
    
    # OfflineService 조립 (의존성 주입)
    offline_service = OfflineService(
        local_db=local_db,
        network_monitor=network_monitor,
        sync_queue=sync_queue,
        cache_service=cache_service
    )
    app.state.offline_service = offline_service
    
    print("✅ Services started.")
    
    yield
    
    # 2. 서비스 종료 및 정리
    print("🛑 Services shutting down...")
    await network_monitor.stop_monitoring()
    print("Services stopped.")


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
app.include_router(llm_router.router)
app.include_router(reviews_router.router)
app.include_router(wellness_router.router)
app.include_router(notification_router.router)
app.include_router(offline_router.router)
app.include_router(flights_router.router)
