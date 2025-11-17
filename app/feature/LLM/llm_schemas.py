from typing import List, Optional

from pydantic import BaseModel, Field


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


class LLMChatResponse(BaseModel):
    """
    Gemini 응답을 클라이언트에 전달하기 위한 스키마
    """

    model: str
    content: str

