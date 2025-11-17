from typing import List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


class FlightInfo(BaseModel):
    """
    사용자가 요청한 항공편 메타데이터.
    모델에게 보다 구체적인 리뷰 맥락을 제공합니다.
    """

    airline: Optional[str] = Field(
        default=None, description="항공사명 (예: Korean Air, Delta)"
    )
    flight_number: Optional[str] = Field(
        default=None, description="항공편 번호 (예: KE123)"
    )
    seat_class: Optional[str] = Field(
        default=None, description="좌석 등급 (예: 비즈니스, 이코노미)"
    )
    seat_number: Optional[str] = Field(
        default=None, description="좌석 번호 (예: 12A)"
    )
    departure_airport: Optional[str] = Field(
        default=None, description="출발 공항 또는 도시 (예: ICN, Seoul)"
    )
    arrival_airport: Optional[str] = Field(
        default=None, description="도착 공항 또는 도시 (예: JFK, New York)"
    )
    departure_date: Optional[str] = Field(
        default=None, description="출발 날짜 (ISO8601 또는 자연어 허용)"
    )
    meal_preference: Optional[str] = Field(
        default=None, description="기내식/식단 정보 (예: 채식, 한식)"
    )


class ImageAttachment(BaseModel):
    """
    사용자로부터 전달된 항공권/탑승권 등의 이미지 정보.
    """

    mime_type: Optional[str] = Field(
        default="image/png",
        description="이미지 MIME 타입 (예: image/jpeg, image/png)",
    )
    base64_data: Optional[str] = Field(
        default=None,
        description="Base64로 인코딩된 이미지 데이터",
    )
    url: Optional[str] = Field(
        default=None,
        description="원격 이미지 URL (사전 서명 URL 등)",
    )

    @model_validator(mode="after")
    def validate_source(self):
        if not (self.base64_data or self.url):
            raise ValueError("base64_data 또는 url 중 하나는 반드시 필요합니다.")
        return self


class LLMChatRequest(BaseModel):
    """
    Gemini 모델에게 전달될 기본 채팅 요청 스키마
    """

    prompt: str = Field(..., min_length=1, description="사용자 질문/명령 프롬프트")
    context: Optional[List[str]] = Field(
        default=None,
        description="대화 문맥이나 참고 문장 목록",
    )
    system_instruction: Optional[str] = Field(
        default=None,
        description="모델의 응답 톤/역할을 제한하는 시스템 인스트럭션",
    )
    flight_info: Optional[FlightInfo] = Field(
        default=None,
        description="사용자가 조회하려는 항공편 정보",
    )
    images: Optional[List[ImageAttachment]] = Field(
        default=None,
        description="항공편 정보를 담고 있는 이미지 목록 (탑승권, 좌석표 등)",
    )


class LLMChatResponse(BaseModel):
    """
    Gemini 응답을 클라이언트에 전달하기 위한 스키마
    """

    model: str
    content: str

