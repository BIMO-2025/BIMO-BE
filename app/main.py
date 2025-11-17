# app/main.py

from fastapi import FastAPI

# 1. 기능별 라우터 import
from app.feature.LLM import llm_router
from app.feature.auth import auth_router

# 2. Firebase 초기화 실행
from app.core import firebase

# 3. 커스텀 예외 핸들러 import
from app.core.exceptions.exceptions import CustomException
from app.core.exceptions.exception_handlers import custom_exception_handler


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

# ... (다른 라우터들도 여기에 추가)