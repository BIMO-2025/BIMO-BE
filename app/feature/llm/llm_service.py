from app.feature.llm.ollama_client import get_ollama_client
from app.feature.llm.llm_schemas import LLMChatRequest
from app.feature.llm.prompt_builder import (
    DEFAULT_SYSTEM_INSTRUCTION,
    build_prompt_segments,
)

# 사용 중인 모델 이름 (환경 변수에서 가져옴)
from app.core.config import settings
MODEL_NAME = settings.OLLAMA_MODEL_NAME


async def generate_chat_completion(request: LLMChatRequest) -> str:
    """
    Ollama 모델에 프롬프트를 전달하고 응답 텍스트를 반환합니다.
    """
    system_instruction = request.system_instruction or DEFAULT_SYSTEM_INSTRUCTION

    prompt_segments = build_prompt_segments(
        prompt=request.prompt,
        context=request.context,
        flight_info=request.flight_info,
        images=request.images,
    )
    
    # Ollama 클라이언트 가져오기
    client = get_ollama_client()

    return await client.generate(

        prompt_segments=prompt_segments,
        system_instruction=system_instruction,
    )
