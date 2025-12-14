"""
Gemini API 간단 테스트 스크립트
"""
import os
import sys
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# Google Generative AI import 테스트
try:
    import google.generativeai as genai
    print(f"✅ google-generativeai 버전: {genai.__version__}")
except ImportError as e:
    print(f"❌ google-generativeai import 실패: {e}")
    sys.exit(1)

# API 키 확인
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("❌ GEMINI_API_KEY 환경 변수가 설정되지 않았습니다.")
    sys.exit(1)

print(f"✅ GEMINI_API_KEY 설정됨 (길이: {len(api_key)})")

# Gemini 설정
try:
    genai.configure(api_key=api_key)
    print("✅ Gemini API 설정 완료")
except Exception as e:
    print(f"❌ Gemini API 설정 실패: {e}")
    sys.exit(1)

# 모델 초기화
model_name = os.getenv("GEMINI_MODEL_NAME", "gemini-1.5-flash")
print(f"📝 사용 모델: {model_name}")

try:
    model = genai.GenerativeModel(model_name)
    print(f"✅ 모델 '{model_name}' 초기화 성공")
except Exception as e:
    print(f"❌ 모델 초기화 실패: {e}")
    sys.exit(1)

# 간단한 테스트 프롬프트
test_prompt = "안녕하세요! 간단하게 '테스트 성공'이라고만 답변해주세요."

print("\n🚀 Gemini API 테스트 시작...")
print(f"프롬프트: {test_prompt}\n")

try:
    response = model.generate_content(test_prompt)
    print("✅ Gemini API 호출 성공!")
    print(f"응답: {response.text}")
    print("\n🎉 모든 테스트 통과!")
except Exception as e:
    print(f"❌ Gemini API 호출 실패: {e}")
    sys.exit(1)
