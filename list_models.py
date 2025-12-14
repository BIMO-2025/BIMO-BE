"""
사용 가능한 Gemini 모델 목록 확인
"""
import os
from dotenv import load_dotenv
import google.generativeai as genai

# 환경 변수 로드
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("❌ GEMINI_API_KEY 환경 변수가 설정되지 않았습니다.")
    exit(1)

print(f"✅ API 키 확인됨 (길이: {len(api_key)})")
print(f"✅ google-generativeai 버전: {genai.__version__}\n")

# API 설정
genai.configure(api_key=api_key)

print("📋 사용 가능한 모델 목록:\n")
print("=" * 80)

try:
    models = genai.list_models()
    
    for model in models:
        print(f"\n모델명: {model.name}")
        print(f"  - 지원 메서드: {', '.join(model.supported_generation_methods)}")
        print(f"  - 설명: {model.display_name}")
        
    print("\n" + "=" * 80)
    print("\n✅ generateContent를 지원하는 모델:")
    
    for model in models:
        if 'generateContent' in model.supported_generation_methods:
            print(f"  - {model.name}")
            
except Exception as e:
    print(f"❌ 모델 목록 조회 실패: {e}")
    print("\n💡 API 키가 유효한지 확인해주세요:")
    print("   https://aistudio.google.com/app/apikey")
