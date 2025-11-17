from typing import List, Optional

from app.feature.LLM.llm_schemas import FlightInfo, ImageAttachment

DEFAULT_SYSTEM_INSTRUCTION = (
    "You are an airline experience concierge. "
    "Extract structured flight metadata from any provided boarding pass images "
    "(airline, flight number, route, date, seat class/number, meal info, loyalty tier). "
    "Combine that with user prompts to provide concise reviews about the airline, "
    "seat comfort, in-flight meals, cabin service, and helpful travel tips. "
    "If critical data is missing from both the images and text, clearly state "
    "the limitation and suggest which detail is needed."
)


def build_prompt_segments(
    prompt: str,
    context: Optional[List[str]],
    flight_info: Optional[FlightInfo],
    images: Optional[List[ImageAttachment]],
) -> List[object]:
    """
    Gemini SDK generate_content 호출 시 사용할 프롬프트 목록을 구성합니다.
    """
    segments: List[object] = []
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

