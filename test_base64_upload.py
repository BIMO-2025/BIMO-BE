"""
Base64 이미지 업로드 API 테스트
"""

import requests
from PIL import Image
import io

# 1. 간단한 테스트 이미지 생성 (50x50 빨간색 사각형)
img = Image.new('RGB', (50, 50), color='red')
img_bytes = io.BytesIO()
img.save(img_bytes, format='PNG')
img_bytes.seek(0)

# 2. API 호출
url = 'http://localhost:8000/uploads/images/base64'
files = {'files': ('test.png', img_bytes, 'image/png')}

print("테스트 시작...")
print(f"URL: {url}")

try:
    response = requests.post(url, files=files)
    print(f"\n✅ 응답 상태 코드: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ 성공: {data['message']}")
        print(f"✅ 이미지 개수: {data['count']}")
        
        if data['images']:
            base64_str = data['images'][0]
            print(f"\n✅ Base64 문자열 길이: {len(base64_str)} 문자")
            print(f"✅ 시작 부분: {base64_str[:80]}...")
            
            # Base64 형식 확인
            if base64_str.startswith('data:image/jpeg;base64,'):
                print("✅ Base64 Data URL 형식 확인됨!")
            else:
                print("❌ Base64 형식이 아닙니다!")
        else:
            print("❌ 이미지가 반환되지 않았습니다!")
    else:
        print(f"❌ 에러: {response.text}")
        
except Exception as e:
    print(f"❌ 연결 실패: {e}")
