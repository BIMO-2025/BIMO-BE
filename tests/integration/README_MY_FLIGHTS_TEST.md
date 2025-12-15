# MyFlights 실제 Firestore 테스트 가이드

## 개요

`test_my_flights_real_firestore.py`는 실제 Firestore 데이터베이스에 데이터를 저장하고 조회하는 End-to-End 통합 테스트입니다.

## 주의사항

⚠️ **이 테스트는 실제 Firebase 프로젝트를 사용합니다**
- 실제 Firestore에 테스트 데이터가 생성됩니다
- 테스트 후 자동으로 정리되지만, 실패 시 수동 정리가 필요할 수 있습니다
- Firebase 서비스 계정 키 파일(`firebase_service_key.json`)이 필요합니다

## 사전 요구사항

1. **Firebase 프로젝트 설정**
   - Firebase 프로젝트가 생성되어 있어야 합니다
   - 서비스 계정 키 파일이 `./firebase_service_key.json` 경로에 있어야 합니다
   - `.env` 파일에 `FIREBASE_SERVICE_ACCOUNT_KEY=./firebase_service_key.json` 설정

2. **환경 변수 설정**
   ```env
   API_SECRET_KEY=your-secret-key
   API_TOKEN_ALGORITHM=HS256
   API_TOKEN_EXPIRE_MINUTES=30
   FIREBASE_SERVICE_ACCOUNT_KEY=./firebase_service_key.json
   ```

## 테스트 실행 방법

### 전체 테스트 실행

```bash
# 특정 테스트 파일만 실행
pytest tests/integration/test_my_flights_real_firestore.py -v

# 상세한 출력과 함께 실행
pytest tests/integration/test_my_flights_real_firestore.py -v -s

# 특정 테스트만 실행
pytest tests/integration/test_my_flights_real_firestore.py::TestMyFlightsRealFirestore::test_create_my_flight_real_firestore -v
```

### 테스트 항목

1. **test_create_my_flight_real_firestore**
   - 직항 항공편을 실제 Firestore에 저장
   - API로 조회하여 확인
   - Firestore에서 직접 조회하여 데이터 일치 확인

2. **test_create_flight_with_stopover_real_firestore**
   - 경유 항공편 저장 및 검증

3. **test_get_my_flights_list_real_firestore**
   - 여러 비행 기록 생성 후 목록 조회
   - 최신순 정렬 확인

4. **test_update_my_flight_real_firestore**
   - 비행 기록 업데이트 테스트

5. **test_delete_my_flight_real_firestore**
   - 비행 기록 삭제 테스트

6. **test_unauthorized_access**
   - 권한 없는 사용자 접근 차단 테스트

## 테스트 플로우

```
1. 테스트용 사용자 ID 생성 (고유한 타임스탬프 기반)
   ↓
2. 테스트용 JWT 토큰 생성 (해당 사용자 ID 포함)
   ↓
3. POST /users/{user_id}/my-flights로 비행 기록 생성
   ↓
4. 생성된 flight_id 확인
   ↓
5. GET /users/{user_id}/my-flights/{flight_id}로 API 조회
   ↓
6. Firestore에서 직접 조회하여 데이터 일치 확인
   ↓
7. 테스트 후 자동 정리 (cleanup_test_data fixture)
```

## 테스트 데이터 정리

테스트는 `cleanup_test_data` fixture를 통해 자동으로 정리됩니다:
- 각 테스트 후 해당 사용자의 모든 myFlights 문서 삭제
- 테스트 실패 시에도 정리 시도

수동 정리가 필요한 경우:
```python
# Firestore 콘솔에서 직접 삭제하거나
# Firebase Admin SDK로 삭제
```

## 문제 해결

### Firebase 초기화 오류
```
AppConfigError: Firebase 서비스 키 파일이 유효하지 않습니다
```
→ `firebase_service_key.json` 파일 경로와 내용 확인

### 권한 오류 (403)
```
HTTPException: 이 리소스에 접근할 권한이 없습니다
```
→ JWT 토큰의 `sub` 필드와 경로의 `user_id`가 일치하는지 확인

### Firestore 조회 실패
```
AssertionError: Firestore에 문서가 존재하지 않습니다
```
→ Firebase 프로젝트 설정 확인
→ Firestore 규칙 확인 (테스트 환경에서는 읽기/쓰기 허용 필요)

## 예상 출력

성공적인 테스트 실행 시:
```
[TEST] 생성된 Flight ID: abc123xyz
[TEST] API 조회 성공: abc123xyz
[TEST] Firestore 직접 조회 성공: abc123xyz
[CLEANUP] 테스트 데이터 정리 완료: test-user-1234567890.123
```

## 다음 단계

테스트가 성공하면:
1. 실제 클라이언트 앱에서 동일한 플로우로 테스트
2. 실제 소셜 로그인을 통한 인증 플로우 테스트
3. 프로덕션 환경 배포 전 최종 검증

