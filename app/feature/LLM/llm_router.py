from fastapi import APIRouter

from app.feature.LLM import llm_schemas, llm_service

router = APIRouter(
    prefix="/llm",
    tags=["LLM"],
)


@router.post("/chat", response_model=llm_schemas.LLMChatResponse)
async def chat_with_gemini(request: llm_schemas.LLMChatRequest):
    """
    탑승권 사진 및 사용자 요청을 기반으로 항공사 리뷰/팁을 생성합니다.
    """
    content = await llm_service.generate_chat_completion(request)
    return llm_schemas.LLMChatResponse(
        model=llm_service.MODEL_NAME,
        content=content,
    )

