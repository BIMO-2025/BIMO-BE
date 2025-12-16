"""
리뷰 요약 비즈니스 로직 (LLM 활용)
"""

import json
from typing import List, Optional

from app.feature.reviews.reviews_schemas import ReviewSchema, BIMOSummaryResponse
from app.feature.llm.llm_service import LLMService
from app.feature.llm.llm_schemas import LLMChatRequest


class ReviewSummaryService:
    """LLM을 사용하여 리뷰를 요약하는 서비스 클래스"""

    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service

    async def generate_bimo_summary(
        self, 
        reviews: List[ReviewSchema], 
        airline_code: str, 
        airline_name: str
    ) -> BIMOSummaryResponse:
        """
        리뷰 목록을 바탕으로 Good/Bad 포인트를 추출합니다.
        
        Args:
            reviews: 리뷰 목록 (최신순 권장)
            airline_code: 항공사 코드
            airline_name: 항공사 이름
            
        Returns:
            BIMOSummaryResponse
        """
        if not reviews:
            return BIMOSummaryResponse(
                airline_code=airline_code,
                airline_name=airline_name,
                good_points=[],
                bad_points=[],
                review_count=0,
            )

        # 요약에 사용할 리뷰 텍스트 추출 (최대 50개)
        review_lines = []
        for r in reviews[:50]:
            text = r.text or ""
            review_lines.append(f"- {text} (평점: {r.overallRating}/5)")

        prompt = f"""
다음은 {airline_name} 항공사에 대한 리뷰 {len(review_lines)}개의 목록입니다.
각 리뷰는 텍스트와 평점을 포함합니다.

리뷰 목록:
{chr(10).join(review_lines)}

요구사항:
- 한국어로 응답합니다.
- JSON 문자열만 반환합니다 (설명 금지).
- 형태: {{"good_points": ["..."], "bad_points": ["..."]}}
- good/bad 각각 최대 5개, 짧고 핵심만.
"""

        system_instruction = (
            "You are an airline review analyst. Return concise JSON with good_points and bad_points in Korean."
        )

        request = LLMChatRequest(
            prompt=prompt, 
            system_instruction=system_instruction
        )

        raw_response = await self.llm_service.generate_chat_completion(request)
        good_points, bad_points = self._safe_parse_json(raw_response)

        return BIMOSummaryResponse(
            airline_code=airline_code,
            airline_name=airline_name,
            good_points=good_points,
            bad_points=bad_points,
            review_count=len(reviews),
        )

    async def summarize_reviews_text(
        self, 
        reviews: List[ReviewSchema], 
        airline_name: str
    ) -> str:
        """
        리뷰 목록을 바탕으로 간단한 텍스트 요약을 생성합니다.
        
        Args:
            reviews: 리뷰 목록
            airline_name: 항공사 이름
            
        Returns:
            요약된 텍스트
        """
        if not reviews:
            return f"{airline_name} 항공사에 대한 리뷰가 아직 없습니다."

        # 요약에 사용할 리뷰 텍스트 추출 (최대 50개)
        review_text_chunk = "\n".join([r.text for r in reviews[:50] if r.text])

        prompt = f"""
다음은 {airline_name} 항공사에 대한 최근 리뷰들입니다:
{review_text_chunk}

이 리뷰들을 바탕으로 항공사의 장단점을 포함하여 3~5문장으로 요약해주세요. 
한국어로 작성하고, 공손하고 객관적인 어조를 유지하세요.
"""
        
        system_instruction = (
            "You are a helpful assistant implementing airline review summarization. "
            "Provide balanced insights highlighting both strengths and areas for improvement."
        )
        
        request = LLMChatRequest(
            prompt=prompt,
            system_instruction=system_instruction
        )
        
        summary = await self.llm_service.generate_chat_completion(request)
        return summary

    def _safe_parse_json(self, raw_text: str) -> tuple[List[str], List[str]]:
        """LLM 응답에서 JSON을 안전하게 파싱"""
        try:
            # 원본 텍스트 정제
            text = raw_text.strip()
            
            # 마크다운 코드 블록 제거
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()
            
            # JSON 파싱
            data = json.loads(text)
            good = data.get("good_points") or []
            bad = data.get("bad_points") or []
            
            return list(good), list(bad)
        except Exception as e:
            # 에러 로깅은 호출 측에서 처리하거나 여기서 로거 사용
            print(f"JSON 파싱 실패: {e}")
            return [], []
