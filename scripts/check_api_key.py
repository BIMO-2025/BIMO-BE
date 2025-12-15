"""
API 키 설정 확인 스크립트
"""
import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

print("=== API 키 진단 ===\n")

if not api_key:
    print("❌ GEMINI_API_KEY 환경 변수를 찾을 수 없습니다.")
    print("   .env 파일에서 GEMINI_API_KEY를 확인하세요.")
else:
    print(f"✅ API 키 발견")
    print(f"   - 길이: {len(api_key)}")
    print(f"   - 시작: {api_key[:10]}...")
    print(f"   - 끝: ...{api_key[-5:]}")
    
    # 공백 확인
    if api_key != api_key.strip():
        print("⚠️  경고: API 키에 앞뒤 공백이 포함되어 있습니다!")
        print(f"   원본 길이: {len(api_key)}, 공백 제거 후: {len(api_key.strip())}")
    
    # 줄바꿈 확인
    if '\n' in api_key or '\r' in api_key:
        print("⚠️  경고: API 키에 줄바꿈 문자가 포함되어 있습니다!")
    
    # 따옴표 확인
    if api_key.startswith('"') or api_key.startswith("'"):
        print("⚠️  경고: API 키가 따옴표로 시작합니다!")
        print(f"   첫 문자: {repr(api_key[0])}")
    
    # 올바른 형식 확인 (Gemini API 키는 보통 'AI'로 시작)
    if not api_key.startswith('AI'):
        print("⚠️  경고: Gemini API 키는 보통 'AI'로 시작해야 합니다.")
        print(f"   현재 시작: {api_key[:5]}")

print("\n=== .env 파일 형식 확인 ===")
print("올바른 형식 예시:")
print("GEMINI_API_KEY=AIzaSyAbc123...")
print("\n잘못된 형식 예시:")
print('GEMINI_API_KEY="AIzaSyAbc123..."  # 따옴표 필요 없음')
print('GEMINI_API_KEY=AIzaSyAbc123... # 뒤에 공백이나 주석 없어야 함')
