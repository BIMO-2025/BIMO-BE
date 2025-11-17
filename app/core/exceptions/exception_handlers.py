from fastapi import Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.core.exceptions.exceptions import CustomException

class ErrorResponse(BaseModel):
    """
    클라이언트에게 반환될 표준 에러 응답 DTO
    """
    error_code: str
    message: str

# --- 애플리케이션 시작(설정) 오류 ---
# 이 예외는 HTTP 핸들러가 잡는 것이 아니라,
# 앱 시작 자체를 중단시키기 위한 것입니다.
class AppConfigError(Exception):
    """
    .env 설정이 없거나, 서비스 키 파일이 잘못되었거나,
    필수 설정값이 누락되었을 때
    (애플리케이션 시작 시점에 발생)
    """
    pass

async def custom_exception_handler(request: Request, exc: CustomException):
    """
    CustomException을 캐치하여 표준화된 JSON 형식으로 응답합니다.
    """
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error_code=exc.error_code,
            message=exc.message
        ).model_dump()
    )