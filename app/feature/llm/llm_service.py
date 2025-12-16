"""
LLM 관련 비즈니스 로직
"""

from typing import List, Optional

from app.feature.llm.gemini_client import GeminiClient
from app.feature.llm.llm_schemas import LLMChatRequest, FlightInfo, ImageAttachment
from app.feature.llm.prompt_builder import DEFAULT_SYSTEM_INSTRUCTION
from app.core.config import settings


class LLMService:
    """LLM 관련 비즈니스 로직을 처리하는 서비스 클래스"""
    
    def __init__(self, gemini_client: GeminiClient):
        """
        LLMService 초기화
        
        Args:
            gemini_client: Gemini 클라이언트 인스턴스
        """
        self.gemini_client = gemini_client
        self.model_name = settings.GEMINI_MODEL_NAME
    
    async def generate_chat_completion(self, request: LLMChatRequest) -> str:
        """
        Gemini 모델에 프롬프트를 전달하고 응답 텍스트를 반환합니다.
        
        Args:
            request: LLM 채팅 요청 객체
            
        Returns:
            생성된 응답 텍스트
        """
        system_instruction = request.system_instruction or DEFAULT_SYSTEM_INSTRUCTION
        
        prompt_segments = self._build_prompt_segments(
            prompt=request.prompt,
            context=request.context,
            flight_info=request.flight_info,
            images=request.images,
        )
        
        return await self.gemini_client.generate(
            prompt_segments=prompt_segments,
            system_instruction=system_instruction,
        )
    
    def _build_prompt_segments(
        self,
        prompt: str,
        context: Optional[List[str]],
        flight_info: Optional[FlightInfo],
        images: Optional[List[ImageAttachment]],
    ) -> List[object]:
        """
        Gemini SDK generate_content 호출 시 사용할 프롬프트 목록을 구성합니다.
        
        Args:
            prompt: 메인 프롬프트
            context: 추가 컨텍스트 리스트
            flight_info: 비행 정보
            images: 이미지 첨부 리스트
            
        Returns:
            프롬프트 세그먼트 리스트
        """
        segments: List[object] = []
        
        if context:
            segments.extend([ctx for ctx in context if ctx.strip()])
        
        if images:
            segments.extend(self._build_image_parts(images))
        
        if flight_info:
            compiled_info = self._format_flight_info(flight_info)
            if compiled_info:
                segments.append(compiled_info)
        
        segments.append(prompt)
        return segments
    
    def _build_image_parts(self, images: List[ImageAttachment]) -> List[object]:
        """
        Gemini 멀티모달 입력에 사용할 이미지 Part를 생성합니다.
        
        Args:
            images: 이미지 첨부 리스트
            
        Returns:
            이미지 Part 리스트
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
    
    def _format_flight_info(self, flight: FlightInfo) -> str:
        """
        FlightInfo 객체를 모델이 이해하기 쉬운 요약 문자열로 변환합니다.
        
        Args:
            flight: 비행 정보 객체
            
        Returns:
            포맷된 비행 정보 문자열
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


# ============================================
# 하위 호환성을 위한 레거시 함수
# (기존 코드와의 호환성을 위해 유지)
# ============================================

async def generate_chat_completion(request: LLMChatRequest) -> str:
    """
    [레거시 함수] Gemini 모델에 프롬프트를 전달하고 응답 텍스트를 반환합니다.
    
    Deprecated: LLMService 클래스 사용을 권장합니다.
    """
    from app.feature.llm.gemini_client import get_gemini_client
    client = get_gemini_client()
    service = LLMService(gemini_client=client)
    return await service.generate_chat_completion(request)
