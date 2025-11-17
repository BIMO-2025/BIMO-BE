from app.feature.LLM.gemini_client import gemini_client
from app.feature.LLM.llm_schemas import LLMChatRequest
from app.feature.LLM.prompt_builder import (
    DEFAULT_SYSTEM_INSTRUCTION,
    build_prompt_segments,
)


async def generate_chat_completion(request: LLMChatRequest) -> str:
    """
    Gemini 모델에 프롬프트를 전달하고 응답 텍스트를 반환합니다.
    """
    system_instruction = request.system_instruction or DEFAULT_SYSTEM_INSTRUCTION

    prompt_segments = build_prompt_segments(
        prompt=request.prompt,
        context=request.context,
        flight_info=request.flight_info,
        images=request.images,
    )

    return await gemini_client.generate(
        prompt_segments=prompt_segments,
        system_instruction=system_instruction,
    )

