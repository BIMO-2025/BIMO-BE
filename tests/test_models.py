"""
사용 가능한 Gemini 모델로 간단 테스트
"""
import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)

print(f"google-generativeai version: {genai.__version__}\n")

# 테스트할 모델들 (최신 버전)
test_models = [
    "gemini-2.0-flash-exp",
    "gemini-1.5-flash-latest", 
    "gemini-1.5-pro-latest",
    "gemini-2.5-flash-latest"
]

prompt = "안녕! '테스트 성공'이라고만 답변해줘."

print("=== 사용 가능한 모델 테스트 ===\n")

for model_name in test_models:
    try:
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(prompt)
        print(f"✅ {model_name}")
        print(f"   응답: {response.text[:50]}\n")
        break  # 첫 번째 성공한 모델로 테스트 완료
    except Exception as e:
        print(f"❌ {model_name}: {str(e)[:80]}")
