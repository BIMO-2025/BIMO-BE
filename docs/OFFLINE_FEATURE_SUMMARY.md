# 오프라인 기능 구현 요약

## 구현 완료 사항

### 1. 핵심 모듈

#### ✅ 로컬 데이터베이스 (`app/core/offline/local_db.py`)
- SQLite 기반 로컬 데이터베이스
- 비행 정보, 리뷰 캐시, 시차적응 계획, 사용자 프로필 저장
- 오프라인 큐 테이블 포함

#### ✅ 네트워크 상태 감지 (`app/core/offline/network_monitor.py`)
- Firebase 연결 상태 모니터링
- 외부 API 헬스체크
- 주기적 상태 확인 (기본 30초)
- 상태 변경 리스너 지원

#### ✅ 동기화 큐 시스템 (`app/core/offline/sync_queue.py`)
- 오프라인 요청을 큐에 저장
- 네트워크 복구 시 자동 동기화
- 수동 동기화 지원
- 재시도 메커니즘

#### ✅ 캐싱 서비스 (`app/core/offline/cache_service.py`)
- 온라인 조회 데이터 자동 캐싱
- 오프라인에서 캐시 조회
- TTL 기반 캐시 만료

#### ✅ 오프라인 통합 서비스 (`app/core/offline/offline_service.py`)
- 읽기/쓰기 작업의 통합 인터페이스
- 네트워크 상태에 따른 자동 분기
- 동기화 상태 조회

### 2. API 엔드포인트

#### ✅ 오프라인 기능 라우터 (`app/feature/offline/offline_router.py`)
- `GET /offline/status`: 동기화 상태 조회
- `POST /offline/sync`: 수동 동기화 실행

### 3. 통합

#### ✅ 메인 애플리케이션 (`app/main.py`)
- 애플리케이션 시작 시 네트워크 모니터링 자동 시작
- 종료 시 모니터링 정리

## 사용 방법

### 기본 패턴

#### 읽기 작업
```python
from app.core.offline import get_offline_service

offline_service = get_offline_service()

# 오프라인 지원 조회
data = await offline_service.read_with_fallback(
    cache_key="reviews:KE",
    fetch_func=fetch_from_firestore,
    cache_ttl_hours=24
)
```

#### 쓰기 작업
```python
result = await offline_service.write_with_queue(
    operation_type="create",
    collection_name="users/{userId}/myFlights",
    user_id=user_id,
    data=flight_data,
    online_write_func=save_to_firestore
)
```

## 동작 흐름

### 읽기 작업 흐름
```
1. 네트워크 상태 확인
2. 온라인 → Firestore 조회 → 로컬 캐시 저장 → 반환
3. 오프라인 → 로컬 캐시 조회 → 반환 (없으면 오류)
```

### 쓰기 작업 흐름
```
1. 네트워크 상태 확인
2. 온라인 → Firestore 저장 → 로컬 캐시 업데이트
3. 오프라인 → 로컬 DB 저장 → 큐에 추가 → 네트워크 복구 시 자동 동기화
```

## 주요 특징

1. **자동 동기화**: 네트워크 복구 시 자동으로 큐의 작업을 동기화
2. **캐싱**: 온라인에서 조회한 데이터를 자동으로 캐시하여 오프라인에서 사용
3. **투명한 처리**: 서비스 레이어에서 네트워크 상태를 신경 쓸 필요 없음
4. **에러 처리**: 오프라인 상태에서도 명확한 에러 메시지 제공

## 다음 단계

### 서비스 레이어 통합
각 서비스(리뷰, 비행 정보, 시차적응 등)에 오프라인 지원을 추가해야 합니다.

예시는 `docs/OFFLINE_FEATURE_USAGE.md`를 참고하세요.

### 테스트
- 오프라인 모드 테스트
- 동기화 테스트
- 네트워크 상태 변경 테스트

## 제한사항

1. **LLM 기능**: 오프라인에서 사용 불가 (리뷰 요약, 시차적응 계획 생성)
2. **실시간 데이터**: 오프라인에서는 캐시된 데이터만 조회 가능
3. **이미지 업로드**: 오프라인에서 작성한 리뷰의 이미지는 온라인 복구 후 업로드 필요

## 파일 구조

```
app/
├── core/
│   └── offline/
│       ├── __init__.py
│       ├── local_db.py          # 로컬 SQLite DB
│       ├── network_monitor.py   # 네트워크 상태 감지
│       ├── sync_queue.py         # 동기화 큐
│       ├── cache_service.py      # 캐싱 서비스
│       └── offline_service.py    # 통합 서비스
└── feature/
    └── offline/
        ├── __init__.py
        └── offline_router.py    # API 라우터

docs/
├── OFFLINE_FEATURE_DESIGN.md    # 설계 문서
├── OFFLINE_FEATURE_USAGE.md     # 사용 가이드
└── OFFLINE_FEATURE_SUMMARY.md   # 요약 (이 파일)
```

## 데이터베이스 스키마

로컬 SQLite 데이터베이스에는 다음 테이블이 생성됩니다:

- `my_flights`: 사용자 비행 정보
- `reviews_cache`: 리뷰 캐시
- `jetlag_plans`: 시차적응 계획
- `user_profiles`: 사용자 프로필 캐시
- `sync_queue`: 동기화 큐

데이터베이스 파일은 프로젝트 루트에 `bimo_offline.db`로 생성됩니다.

