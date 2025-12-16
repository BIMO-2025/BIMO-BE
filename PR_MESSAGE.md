# 🔧 OCR 이미지 전달 형식 수정 및 디버깅 개선

## 📋 변경 사항

### 1. OCR 이미지 전달 형식 수정
- **문제**: `ImageAttachment` 객체를 직접 전달하여 Gemini API 호출이 실패하던 문제
- **해결**: Gemini API가 기대하는 딕셔너리 형식(`{"mime_type": "image/jpeg", "data": base64_data}`)으로 변경
- **영향**: OCR 기능이 정상적으로 작동하도록 수정

### 2. Windows 인코딩 오류 수정
- **문제**: 한글 파일명 처리 시 `cp949` 인코딩 오류 발생
- **해결**: 파일명을 UTF-8로 안전하게 인코딩하여 처리
- **영향**: 한글 파일명이 포함된 이미지 업로드 시 오류 해결

### 3. OCR 디버깅 로그 추가
- Gemini API 호출 시작/완료 시점 로그 추가
- JSON 파싱 과정 상세 로그 추가
- 필수 필드 검증 실패 시 누락 필드 정보 출력
- 예외 발생 시 전체 스택 트레이스 출력

### 4. 에러 메시지 개선
- OCR 추출 실패 시 구체적인 에러 메시지 반환
- 클라이언트에 유용한 디버깅 정보 제공

### 5. OCR 테스트 엔드포인트 추가
- `POST /reviews/verify/ocr-test`: 인증 없이 OCR 기능만 테스트 가능
- Swagger UI에서 쉽게 테스트 가능

## 🔍 수정된 파일

- `app/core/image_utils.py`: Windows 인코딩 오류 수정
- `app/feature/reviews/review_verification.py`: OCR 이미지 전달 형식 수정, 디버깅 로그 추가
- `app/feature/reviews/reviews_router.py`: OCR 테스트 엔드포인트 추가, 에러 처리 개선

## 🧪 테스트 방법

1. **OCR 테스트 엔드포인트** (`POST /reviews/verify/ocr-test`)
   - Swagger UI에서 이미지 업로드
   - 서버 콘솔에서 상세 로그 확인

2. **리뷰 인증 엔드포인트** (`POST /reviews/verify`)
   - 탑승권 이미지 업로드
   - 사용자의 myFlights와 비교하여 인증 결과 반환

## 📝 관련 이슈

- OCR 기능이 0.1초만에 응답하여 실제 API 호출이 되지 않던 문제 해결
- 한글 파일명 이미지 업로드 시 인코딩 오류 해결

