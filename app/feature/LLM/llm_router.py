from fastapi import APIRouter

from app.feature.LLM import llm_schemas, llm_service

router = APIRouter(
    prefix="/llm",
    tags=["LLM"],
)


@router.post("/chat", response_model=llm_schemas.LLMChatResponse)
async def chat_with_gemini(
    request: llm_schemas.LLMChatRequest,
):
    """
    Gemini(Google) LLM에게 프롬프트를 전달하고 응답을 반환합니다.
    """
    content = await llm_service.generate_chat_completion(request)
    return llm_schemas.LLMChatResponse(
        model=llm_service.MODEL_NAME,
        content=content,
    )

