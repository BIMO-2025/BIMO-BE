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
from app.core.offline import get_network_monitor


# 4. FastAPI 앱 인스턴스 생성
app = FastAPI(
    title="BIMO-BE Project",
    description="BIMO-BE FastAPI 서버입니다.",
    version="0.1.0",
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


# 6. 애플리케이션 생명주기 이벤트
@app.on_event("startup")
async def startup_event():
    """애플리케이션 시작 시 실행"""
    # 네트워크 모니터링 시작
    network_monitor = get_network_monitor()
    await network_monitor.start_monitoring(interval=30)
    print("✅ 네트워크 모니터링이 시작되었습니다.")


@app.on_event("shutdown")
async def shutdown_event():
    """애플리케이션 종료 시 실행"""
    # 네트워크 모니터링 중지
    network_monitor = get_network_monitor()
    await network_monitor.stop_monitoring()
    print("🛑 네트워크 모니터링이 중지되었습니다.")
