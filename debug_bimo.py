"""
BIMO 요약 디버깅 스크립트
LLM 응답을 확인하여 JSON 파싱 문제 해결
"""
import asyncio
from app.core.firebase import FirebaseService
from app.feature.llm.gemini_client import get_gemini_client
from app.feature.reviews.reviews_service import ReviewsService


async def debug_bimo_summary():
    print("=" * 80)
    print("BIMO 요약 디버깅")
    print("=" * 80)
    
    # 초기화
    firebase = FirebaseService()
    firebase.initialize()
    
    gemini_client = get_gemini_client()
    reviews_service = ReviewsService(firebase_service=firebase, gemini_client=gemini_client)
    
    # 리뷰 조회
    print("\n[1단계] 대한항공 리뷰 조회...")
    reviews = await reviews_service.get_reviews_by_airline("KE", limit=50)
    print(f"✓ 리뷰 개수: {len(reviews)}개")
    
    if not reviews:
        print("✗ 리뷰가 없습니다!")
        return
    
    # 리뷰 텍스트 준비
    review_lines = []
    for r in reviews[:10]:  # 처음 10개만
        text = r.text or ""
        review_lines.append(f"- {text} (평점: {r.overallRating}/5)")
    
    print(f"\n[2단계] 프롬프트 생성...")
    airline_name = reviews[0].airlineName if getattr(reviews[0], "airlineName", None) else "KE"
    
    prompt = f"""
다음은 {airline_name} 항공사에 대한 리뷰 {len(reviews)}개의 목록입니다.
각 리뷰는 텍스트와 평점을 포함합니다.

리뷰 목록:
{chr(10).join(review_lines)}

요구사항:
- 한국어로 응답합니다.
- JSON 문자열만 반환합니다 (설명 금지).
- 형태: {{"good_points": ["..."], "bad_points": ["..."]}}
- good/bad 각각 최대 5개, 짧고 핵심만.
"""
    
    print(f"\n프롬프트:\n{prompt[:500]}...")
    
    # LLM 호출
    print(f"\n[3단계] LLM 호출 중...")
    from app.feature.llm.llm_schemas import LLMChatRequest
    from app.feature.llm import llm_service
    
    system_instruction = (
        "You are an airline review analyst. Return concise JSON with good_points and bad_points in Korean."
    )
    
    request = LLMChatRequest(prompt=prompt, system_instruction=system_instruction)
    raw_response = await llm_service.generate_chat_completion(request)
    
    print(f"\n✓ LLM 응답 (원본):")
    print("=" * 80)
    print(raw_response)
    print("=" * 80)
    
    # JSON 파싱 시도
    print(f"\n[4단계] JSON 파싱 시도...")
    import json
    
    try:
        # 가능한 JSON 추출 시도
        response_text = raw_response.strip()
        
        # ```json ... ``` 제거
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
        
        print(f"정제된 텍스트:\n{response_text}")
        
        data = json.loads(response_text)
        good = data.get("good_points") or []
        bad = data.get("bad_points") or []
        
        print(f"\n✓ 파싱 성공!")
        print(f"Good Points: {good}")
        print(f"Bad Points: {bad}")
        
    except Exception as e:
        print(f"\n✗ 파싱 실패: {e}")
        print(f"에러 타입: {type(e).__name__}")


if __name__ == "__main__":
    asyncio.run(debug_bimo_summary())
