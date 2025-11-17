import importlib
from typing import List, Optional

from fastapi.concurrency import run_in_threadpool

from app.core.config import GEMINI_API_KEY, GEMINI_MODEL_NAME
from app.core.exceptions.exceptions import AppConfigError, ExternalApiError
from app.feature.LLM.llm_schemas import (
    FlightInfo,
    ImageAttachment,
    LLMChatRequest,
)

try:
    genai = importlib.import_module("google.generativeai")
except ModuleNotFoundError as exc:
    raise AppConfigError(
        "필수 패키지 'google-generativeai'가 설치되지 않았습니다. "
        "pip install google-generativeai 로 설치하세요."
    ) from exc

# Gemini API 초기화 (Fail Fast)
if not GEMINI_API_KEY:
    raise AppConfigError(
        "환경 변수 'GEMINI_API_KEY'가 설정되지 않았습니다. .env 파일을 확인하세요."
    )

genai.configure(api_key=GEMINI_API_KEY)
MODEL_NAME = GEMINI_MODEL_NAME
DEFAULT_SYSTEM_INSTRUCTION = (
    "You are an airline experience concierge. "
    "Extract structured flight metadata from any provided boarding pass images "
    "(airline, flight number, route, date, seat class/number, meal info, loyalty tier). "
    "Combine that with user prompts to provide concise reviews about the airline, "
    "seat comfort, in-flight meals, cabin service, and helpful travel tips. "
    "If critical data is missing from both the images and text, clearly state "
    "the limitation and suggest which detail is needed."
)


def _build_prompt_segments(
    prompt: str,
    context: Optional[List[str]],
    flight_info: Optional[FlightInfo],
    images: Optional[List[ImageAttachment]],
) -> List[object]:
    """
    Gemini SDK generate_content 호출 시 사용할 프롬프트 목록을 구성합니다.
    """
    segments: List[str] = []
    if context:
        segments.extend([ctx for ctx in context if ctx.strip()])

    if images:
        segments.extend(_build_image_parts(images))

    if flight_info:
        compiled_info = _format_flight_info(flight_info)
        if compiled_info:
            segments.append(compiled_info)

    segments.append(prompt)
    return segments


def _format_flight_info(flight: FlightInfo) -> str:
    """
    FlightInfo 객체를 모델이 이해하기 쉬운 요약 문자열로 변환합니다.
    """
    fields = []
    if flight.airline:
        fields.append(f"Airline: {flight.airline}")
    if flight.flight_number:
        fields.append(f"Flight: {flight.flight_number}")
    if flight.departure_airport or flight.arrival_airport:
        route = f"{flight.departure_airport or '?'} → {flight.arrival_airport or '?'}"
        fields.append(f"Route: {route}")
    if flight.departure_date:
        fields.append(f"Date: {flight.departure_date}")
    if flight.seat_class:
        seat_desc = flight.seat_class
        if flight.seat_number:
            seat_desc += f" ({flight.seat_number})"
        fields.append(f"Seat: {seat_desc}")
    elif flight.seat_number:
        fields.append(f"Seat: {flight.seat_number}")
    if flight.meal_preference:
        fields.append(f"Meal preference: {flight.meal_preference}")

    if not fields:
        return ""

    return "Flight context :: " + ", ".join(fields)


def _build_image_parts(images: List[ImageAttachment]) -> List[object]:
    """
    Gemini 멀티모달 입력에 사용할 이미지 Part를 생성합니다.
    """
    parts: List[object] = []
    for image in images:
        mime_type = image.mime_type or "image/png"
        if image.base64_data:
            parts.append(
                {
                    "mime_type": mime_type,
                    "data": image.base64_data,
                }
            )
        elif image.url:
            parts.append(
                {
                    "file_data": {
                        "file_uri": image.url,
                        "mime_type": mime_type,
                    }
                }
            )
    return parts


async def generate_chat_completion(request: LLMChatRequest) -> str:
    """
    Gemini 모델에 프롬프트를 전달하고 응답 텍스트를 반환합니다.
    """
    system_instruction = request.system_instruction or DEFAULT_SYSTEM_INSTRUCTION
    model = genai.GenerativeModel(
        model_name=MODEL_NAME,
        system_instruction=system_instruction,
    )

    prompt_segments = _build_prompt_segments(
        prompt=request.prompt,
        context=request.context,
        flight_info=request.flight_info,
        images=request.images,
    )

    try:
        response = await run_in_threadpool(
            model.generate_content,
            prompt_segments,
        )
    except Exception as exc:  # google.generativeai에서 다양한 예외가 발생할 수 있음
        raise ExternalApiError(
            message=f"Gemini 요청 중 오류가 발생했습니다: {exc}"
        )

    if not response or not getattr(response, "text", "").strip():
        raise ExternalApiError(message="Gemini 응답이 비어 있습니다.")

    return response.text.strip()

