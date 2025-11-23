import importlib
from typing import List

from fastapi.concurrency import run_in_threadpool

from app.core.config import GEMINI_API_KEY, GEMINI_MODEL_NAME
from app.core.exceptions.exceptions import AppConfigError, ExternalApiError


class GeminiClient:
    """
    google-generativeai SDK 초기화 및 요청 실행을 담당하는 어댑터.
    """

    def __init__(
        self,
        api_key: str | None = GEMINI_API_KEY,
        model_name: str | None = GEMINI_MODEL_NAME,
    ) -> None:
        self._genai = self._import_sdk()
        self._configure(api_key)
        self.model_name = model_name or "gemini-1.5-flash"

    @staticmethod
    def _import_sdk():
        try:
            return importlib.import_module("google.generativeai")
        except ModuleNotFoundError as exc:
            raise AppConfigError(
                "필수 패키지 'google-generativeai'가 설치되지 않았습니다. "
                "pip install google-generativeai 로 설치하세요."
            ) from exc

    def _configure(self, api_key: str | None) -> None:
        if not api_key:
            raise AppConfigError(
                "환경 변수 'GEMINI_API_KEY'가 설정되지 않았습니다. .env를 확인하세요."
            )

        self._genai.configure(api_key=api_key)

    async def generate(
        self,
        prompt_segments: List[object],
        system_instruction: str,
    ) -> str:
        model = self._genai.GenerativeModel(
            model_name=self.model_name,
            system_instruction=system_instruction,
        )

        try:
            response = await run_in_threadpool(
                model.generate_content,
                prompt_segments,
            )
        except Exception as exc:
            raise ExternalApiError(
                message=f"Gemini 요청 중 오류가 발생했습니다: {exc}"
            )

        text = getattr(response, "text", "")
        if not text or not text.strip():
            raise ExternalApiError(message="Gemini 응답이 비어 있습니다.")

        return text.strip()


gemini_client = GeminiClient()

__all__ = ["GeminiClient", "gemini_client"]

