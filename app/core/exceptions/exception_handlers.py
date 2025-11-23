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


async def custom_exception_handler(request: Request, exc: CustomException):
    """
    CustomException을 캐치하여 표준화된 JSON 형식으로 응답합니다.
    """
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error_code=exc.error_code,
            message=exc.message,
        ).model_dump(),
    )