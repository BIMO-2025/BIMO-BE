"""
실제 사용 가능한 Gemini 모델 찾기
"""
import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)

print("=== 사용 가능한 Gemini 모델 찾기 ===\n")

# generateContent를 지원하는 모델만 필터링
available_models = []

try:
    for model in genai.list_models():
        if 'generateContent' in model.supported_generation_methods:
            # gemini로 시작하는 모델만
            if model.name.startswith('models/gemini'):
                available_models.append(model.name.replace('models/', ''))
                
    print(f"총 {len(available_models)}개의 Gemini 모델 발견:\n")
    
    # Flash 모델 우선
    flash_models = [m for m in available_models if 'flash' in m.lower()]
    pro_models = [m for m in available_models if 'pro' in m.lower() and 'flash' not in m.lower()]
    
    if flash_models:
        print("✅ Flash 모델 (빠르고 무료):")
        for m in flash_models[:5]:  # 상위 5개만
            print(f"   - {m}")
    
    if pro_models:
        print("\n✅ Pro 모델 (강력, 유료일 수 있음):")
        for m in pro_models[:3]:  # 상위 3개만
            print(f"   - {m}")
    
    # 첫 번째 Flash 모델로 테스트
    if flash_models:
        test_model = flash_models[0]
        print(f"\n🚀 '{test_model}' 모델로 테스트...\n")
        
        model = genai.GenerativeModel(test_model)
        response = model.generate_content("간단히 '테스트 성공'이라고만 답해줘")
        
        print(f"✅ 성공! 응답: {response.text}")
        print(f"\n💡 .env 파일에 설정할 모델명:")
        print(f"GEMINI_MODEL_NAME={test_model}")
        
except Exception as e:
    print(f"❌ 오류: {e}")
