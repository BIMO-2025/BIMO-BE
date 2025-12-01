"""
LLM 모듈 단위 테스트
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.feature.LLM import llm_service
from app.feature.LLM.llm_schemas import LLMChatRequest, FlightInfo, ImageAttachment


class TestLLMService:
    """llm_service 모듈 테스트"""

    @pytest.mark.asyncio
    async def test_generate_chat_completion_basic(self, mock_gemini_client):
        """기본 채팅 완성 테스트"""
        mock_gemini_client.generate = AsyncMock(return_value="테스트 응답")
        
        request = LLMChatRequest(prompt="테스트 프롬프트")
        
        result = await llm_service.generate_chat_completion(request)
        
        assert result == "테스트 응답"
        mock_gemini_client.generate.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_chat_completion_with_system_instruction(self, mock_gemini_client):
        """시스템 지시사항이 있는 경우"""
        mock_gemini_client.generate = AsyncMock(return_value="커스텀 응답")
        
        request = LLMChatRequest(
            prompt="테스트 프롬프트",
            system_instruction="당신은 항공사 전문가입니다."
        )
        
        result = await llm_service.generate_chat_completion(request)
        
        assert result == "커스텀 응답"
        # 시스템 지시사항이 전달되었는지 확인
        call_args = mock_gemini_client.generate.call_args
        assert call_args[1]["system_instruction"] == "당신은 항공사 전문가입니다."

    @pytest.mark.asyncio
    async def test_generate_chat_completion_with_context(self, mock_gemini_client):
        """컨텍스트가 있는 경우"""
        mock_gemini_client.generate = AsyncMock(return_value="컨텍스트 기반 응답")
        
        request = LLMChatRequest(
            prompt="질문",
            context=["추가 컨텍스트 정보"]
        )
        
        result = await llm_service.generate_chat_completion(request)
        
        assert result == "컨텍스트 기반 응답"

    @pytest.mark.asyncio
    async def test_generate_chat_completion_with_flight_info(self, mock_gemini_client):
        """비행 정보가 있는 경우"""
        mock_gemini_client.generate = AsyncMock(return_value="비행 정보 기반 응답")
        
        flight_info = FlightInfo(
            airline="대한항공",
            flight_number="KE001",
            departure_airport="ICN",
            arrival_airport="JFK"
        )
        
        request = LLMChatRequest(
            prompt="비행 정보 질문",
            flight_info=flight_info
        )
        
        result = await llm_service.generate_chat_completion(request)
        
        assert result == "비행 정보 기반 응답"

    @pytest.mark.asyncio
    async def test_generate_chat_completion_with_images(self, mock_gemini_client):
        """이미지가 있는 경우"""
        mock_gemini_client.generate = AsyncMock(return_value="이미지 기반 응답")
        
        images = [
            ImageAttachment(
                url="https://example.com/image.jpg",
                description="항공기 사진"
            )
        ]
        
        request = LLMChatRequest(
            prompt="이미지 분석",
            images=images
        )
        
        result = await llm_service.generate_chat_completion(request)
        
        assert result == "이미지 기반 응답"

