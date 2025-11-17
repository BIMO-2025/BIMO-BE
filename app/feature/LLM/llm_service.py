import importlib
from typing import List, Optional

from fastapi.concurrency import run_in_threadpool

from app.core.config import GEMINI_API_KEY, GEMINI_MODEL_NAME
from app.core.exceptions.exceptions import AppConfigError, ExternalApiError
from app.feature.LLM.llm_schemas import LLMChatRequest

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


def _build_prompt_segments(prompt: str, context: Optional[List[str]]) -> List[str]:
    """
    Gemini SDK generate_content 호출 시 사용할 프롬프트 목록을 구성합니다.
    """
    segments: List[str] = []
    if context:
        segments.extend([ctx for ctx in context if ctx.strip()])
    segments.append(prompt)
    return segments


async def generate_chat_completion(request: LLMChatRequest) -> str:
    """
    Gemini 모델에 프롬프트를 전달하고 응답 텍스트를 반환합니다.
    """
    model = genai.GenerativeModel(
        model_name=MODEL_NAME,
        system_instruction=request.system_instruction,
    )

    prompt_segments = _build_prompt_segments(
        prompt=request.prompt,
        context=request.context,
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

