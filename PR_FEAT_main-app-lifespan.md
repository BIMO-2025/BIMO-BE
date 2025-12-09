# feat: Add lifespan management for offline services with dependency injection

## 📋 개요

FastAPI의 lifespan 기능을 활용하여 오프라인 서비스들의 생명주기를 관리하고, 의존성 주입(Dependency Injection) 패턴을 적용하여 서비스 간 결합도를 낮추고 테스트 가능성을 향상시켰습니다.

## ✨ 주요 변경 사항

### 1. FastAPI Lifespan 컨텍스트 매니저 추가

애플리케이션 시작 시 서비스를 초기화하고, 종료 시 정리 작업을 수행하는 lifespan 함수를 구현했습니다.

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 서비스 초기화
    yield
    # 서비스 종료 및 정리
```

### 2. 오프라인 서비스 초기화

다음 서비스들을 애플리케이션 시작 시 초기화합니다:

#### NetworkMonitor
- 네트워크 상태 모니터링 시작
- 30초 간격으로 네트워크 상태 체크
- `app.state.network_monitor`에 저장

#### LocalDatabase
- 로컬 데이터베이스 인스턴스 생성
- 오프라인 데이터 저장소 초기화

#### SyncQueue
- 동기화 큐 인스턴스 생성
- 오프라인 상태에서의 변경사항을 추적

#### CacheService
- 캐시 서비스 인스턴스 생성
- 데이터 캐싱 기능 제공

#### OfflineService
- 위 서비스들을 의존성으로 주입받아 생성
- 의존성 주입 패턴 적용으로 테스트 용이성 향상

### 3. 의존성 주입 패턴 적용

`OfflineService`에 필요한 의존성을 생성자 주입 방식으로 전달:

```python
offline_service = OfflineService(
    local_db=local_db,
    network_monitor=network_monitor,
    sync_queue=sync_queue,
    cache_service=cache_service
)
```

이를 통해:
- 서비스 간 결합도 감소
- 단위 테스트 시 Mock 객체 주입 가능
- 서비스 교체 및 확장 용이

### 4. 애플리케이션 종료 시 정리

애플리케이션 종료 시:
- `NetworkMonitor`의 모니터링 중지
- 리소스 정리 및 연결 종료

## 📁 변경된 파일

### `app/main.py`
- `lifespan` 함수 추가
- FastAPI 앱 인스턴스에 `lifespan` 파라미터 추가
- 오프라인 서비스 초기화 로직 추가
- 서비스 종료 및 정리 로직 추가

## 🔧 기술적 세부사항

### Lifespan 동작 흐름

```
애플리케이션 시작
    ↓
NetworkMonitor 초기화 및 시작
    ↓
LocalDatabase 초기화
    ↓
SyncQueue 초기화
    ↓
CacheService 초기화
    ↓
OfflineService 생성 (의존성 주입)
    ↓
app.state에 서비스 저장
    ↓
애플리케이션 실행
    ...
    ↓
애플리케이션 종료 요청
    ↓
NetworkMonitor 중지
    ↓
리소스 정리
```

### 의존성 주입의 장점

1. **테스트 용이성**
   ```python
   # 테스트 시 Mock 객체 주입 가능
   mock_network_monitor = Mock()
   offline_service = OfflineService(
       local_db=mock_local_db,
       network_monitor=mock_network_monitor,
       ...
   )
   ```

2. **유연한 구성**
   - 서비스 구현체를 쉽게 교체 가능
   - 환경별로 다른 구현체 주입 가능

3. **명확한 의존성**
   - 생성자를 통해 의존성이 명시적으로 드러남
   - 코드 가독성 향상

### 서비스 상태 관리

서비스 인스턴스는 `app.state`에 저장되어 애플리케이션 전체에서 접근 가능:

```python
# 다른 곳에서 사용
network_monitor = app.state.network_monitor
offline_service = app.state.offline_service
```

## 📝 사용 예시

### 서비스 초기화 로그
```
🚀 Services initializing...
✅ Services started.
```

### 서비스 종료 로그
```
🛑 Services shutting down...
Services stopped.
```

## ✅ 테스트

- [ ] Lifespan 함수 단위 테스트 작성 필요
- [ ] 서비스 초기화 및 종료 통합 테스트 작성 필요
- [ ] 의존성 주입 동작 확인 테스트 작성 필요

## 🔄 향후 개선 사항

현재 코드에 TODO로 표시된 부분:
- `SyncQueue`의 DI 적용 필요 시 수정
- `CacheService`의 DI 적용 필요 시 수정

이 부분들은 향후 리팩토링을 통해 개선할 예정입니다.

## 🔗 관련 이슈

이 PR은 오프라인 기능의 아키텍처 개선 작업의 일부입니다.

## 📚 참고 문서

- [OFFLINE_FEATURE_DESIGN.md](../docs/OFFLINE_FEATURE_DESIGN.md)
- [OFFLINE_FEATURE_SUMMARY.md](../docs/OFFLINE_FEATURE_SUMMARY.md)
