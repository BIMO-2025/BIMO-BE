import importlib
from typing import List, Dict, Any
import httpx
from fastapi.concurrency import run_in_threadpool

from app.core.config import settings
from app.core.exceptions.exceptions import AppConfigError, ExternalApiError


class OllamaClient:
    """
    Ollama API 초기화 및 요청 실행을 담당하는 어댑터.
    로컬에서 실행되는 오픈소스 LLM을 사용합니다.
    """

    def __init__(
        self,
        base_url: str | None = None,
        model_name: str | None = None,
    ) -> None:
        if base_url is None:
            base_url = settings.OLLAMA_BASE_URL
        if model_name is None:
            model_name = settings.OLLAMA_MODEL_NAME
        
        self.base_url = base_url or "http://localhost:11434"
        self.model_name = model_name or "llama3.2:3b"
        
        # HTTP 클라이언트 초기화
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=300.0,  # Ollama는 로컬이지만 모델 로딩에 시간이 걸릴 수 있음
        )

    async def generate(
        self,
        prompt_segments: List[object],
        system_instruction: str,
    ) -> str:
        """
        Ollama API를 통해 텍스트를 생성합니다.
        
        Args:
            prompt_segments: 프롬프트 세그먼트 리스트 (텍스트, 이미지 등)
            system_instruction: 시스템 지시사항
            
        Returns:
            생성된 텍스트
            
        Raises:
            ExternalApiError: Ollama API 호출 실패 시
        """
        # prompt_segments를 텍스트로 변환
        # Gemini는 리스트를 받지만, Ollama는 문자열만 받음
        prompt_text = self._convert_segments_to_text(prompt_segments)
        
        # Ollama API 요청 페이로드 구성
        payload = {
            "model": self.model_name,
            "prompt": prompt_text,
            "system": system_instruction,
            "stream": False,  # 스트리밍 비활성화
            "options": {
                "temperature": 0.7,
                "top_p": 0.9,
            }
        }
        
        try:
            response = await self._client.post(
                "/api/generate",
                json=payload,
            )
            response.raise_for_status()
            
            result = response.json()
            generated_text = result.get("response", "")
            
            if not generated_text or not generated_text.strip():
                raise ExternalApiError(
                    provider="Ollama",
                    detail="Ollama 응답이 비어 있습니다.",
                )
            
            return generated_text.strip()
            
        except httpx.HTTPStatusError as exc:
            raise ExternalApiError(
                provider="Ollama",
                detail=f"Ollama HTTP 오류 (상태 코드: {exc.response.status_code}): {exc}",
            ) from exc
        except httpx.RequestError as exc:
            raise ExternalApiError(
                provider="Ollama",
                detail=f"Ollama 연결 오류: {exc}. Ollama 서버가 실행 중인지 확인하세요 (http://localhost:11434)",
            ) from exc
        except Exception as exc:
            raise ExternalApiError(
                provider="Ollama",
                detail=f"Ollama 요청 중 예상치 못한 오류가 발생했습니다: {exc}",
            ) from exc

    def _convert_segments_to_text(self, segments: List[object]) -> str:
        """
        프롬프트 세그먼트를 텍스트로 변환합니다.
        
        Gemini는 [text, image, text] 형태의 세그먼트를 지원하지만,
        Ollama의 텍스트 전용 모델은 문자열만 받습니다.
        
        Args:
            segments: 프롬프트 세그먼트 리스트
            
        Returns:
            변환된 텍스트 문자열
        """
        text_parts = []
        
        for segment in segments:
            if isinstance(segment, str):
                text_parts.append(segment)
            elif isinstance(segment, dict):
                # Gemini 이미지 딕셔너리 형태: {"mime_type": "...", "data": "..."}
                # 텍스트 전용 모델이므로 이미지는 건너뜀
                # 나중에 Vision 모델 사용 시 이 부분 수정 필요
                text_parts.append("[이미지가 첨부되었지만 텍스트 전용 모델로 처리 중입니다]")
            else:
                # 기타 객체는 문자열로 변환
                text_parts.append(str(segment))
        
        return "\n".join(text_parts)

    async def close(self):
        """HTTP 클라이언트 종료"""
        await self._client.aclose()


# =============================================================================
# 하위 호환성을 위한 모듈 레벨 변수
# =============================================================================

# Lazy initialization을 위한 변수
_ollama_client = None


def get_ollama_client() -> OllamaClient:
    """
    Ollama 클라이언트 인스턴스를 반환합니다.
    
    Returns:
        OllamaClient 인스턴스
    """
    global _ollama_client
    if _ollama_client is None:
        _ollama_client = OllamaClient()
    return _ollama_client


__all__ = ["OllamaClient", "get_ollama_client"]
