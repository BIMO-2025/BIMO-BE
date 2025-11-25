# 오프라인 기능 사용 가이드

## 개요
이 문서는 오프라인 기능을 서비스 레이어에서 어떻게 사용하는지 설명합니다.

## 기본 사용법

### 1. 읽기 작업 (조회)

온라인 상태에서는 Firestore에서 조회하고 캐시에 저장하며, 오프라인 상태에서는 캐시에서 조회합니다.

```python
from app.core.offline import get_offline_service

offline_service = get_offline_service()

# 리뷰 조회 예시
async def get_reviews_offline_support(airline_code: str):
    async def fetch_from_firestore():
        # 실제 Firestore 조회 로직
        query = reviews_collection.where("airlineCode", "==", airline_code).limit(10)
        docs = await run_in_threadpool(lambda: list(query.stream()))
        reviews = [ReviewSchema(**doc.to_dict()) for doc in docs]
        return [review.model_dump() for review in reviews]
    
    # 오프라인 지원 조회
    cache_key = f"reviews:{airline_code}"
    reviews = await offline_service.read_with_fallback(
        cache_key=cache_key,
        fetch_func=fetch_from_firestore,
        cache_ttl_hours=24
    )
    return reviews
```

### 2. 쓰기 작업 (생성/수정/삭제)

온라인 상태에서는 즉시 Firestore에 저장하고, 오프라인 상태에서는 큐에 추가하여 나중에 동기화합니다.

```python
from app.core.offline import get_offline_service

offline_service = get_offline_service()

# 비행 정보 저장 예시
async def save_my_flight_offline_support(user_id: str, flight_data: dict):
    async def save_to_firestore():
        # 실제 Firestore 저장 로직
        doc_ref = db.collection("users").document(user_id).collection("myFlights")
        doc = await run_in_threadpool(doc_ref.add, flight_data)
        return {"id": doc.id, **flight_data}
    
    # 오프라인 지원 저장
    result = await offline_service.write_with_queue(
        operation_type="create",
        collection_name="users/{userId}/myFlights",
        user_id=user_id,
        data=flight_data,
        online_write_func=save_to_firestore
    )
    
    # result 상태 확인
    if result.get("status") == "offline_saved":
        # 오프라인 상태에서 저장됨
        print("오프라인 상태입니다. 네트워크 복구 시 자동으로 동기화됩니다.")
    elif result.get("status") == "queued":
        # 네트워크 오류로 큐에 추가됨
        print(f"큐에 추가되었습니다. ID: {result.get('queue_id')}")
    
    return result
```

### 3. 동기화 상태 확인

```python
from app.core.offline import get_offline_service

offline_service = get_offline_service()

# 동기화 상태 조회
status = offline_service.get_sync_status()
print(f"네트워크 상태: {status['network_status']}")
print(f"대기 중인 작업: {status['pending_count']}개")
```

### 4. 수동 동기화

```python
from app.core.offline import get_offline_service

offline_service = get_offline_service()

# 수동으로 동기화 실행
result = await offline_service.sync_now()
print(f"동기화 완료: {result['success']}개 성공, {result['failed']}개 실패")
```

## 서비스 레이어 통합 예시

### 리뷰 서비스에 오프라인 지원 추가

```python
# app/feature/reviews/reviews_service.py

from app.core.offline import get_offline_service
from app.core.offline.local_db import LocalDatabase

offline_service = get_offline_service()
local_db = LocalDatabase()

async def get_reviews_by_airline(airline_code: str, limit: int = 10) -> List[ReviewSchema]:
    """항공사 코드로 리뷰를 조회 (오프라인 지원)"""
    
    async def fetch_from_firestore():
        """Firestore에서 리뷰 조회"""
        query = reviews_collection.where("airlineCode", "==", airline_code).limit(limit)
        docs = await run_in_threadpool(lambda: list(query.stream()))
        
        reviews = []
        for doc in docs:
            review_data = doc.to_dict()
            review_data["id"] = doc.id
            reviews.append(ReviewSchema(**review_data))
        
        return [review.model_dump() for review in reviews]
    
    try:
        # 오프라인 지원 조회
        cache_key = f"reviews:{airline_code}"
        reviews_data = await offline_service.read_with_fallback(
            cache_key=cache_key,
            fetch_func=fetch_from_firestore,
            cache_ttl_hours=24
        )
        
        # ReviewSchema 객체로 변환
        return [ReviewSchema(**review) for review in reviews_data]
    except DatabaseError as e:
        # 오프라인 상태에서 캐시도 없는 경우
        raise e
    except Exception as e:
        raise DatabaseError(message=f"리뷰 조회 중 오류 발생: {e}")
```

### 비행 정보 서비스에 오프라인 지원 추가

```python
# app/feature/flights/flights_service.py (새로 생성)

from app.core.offline import get_offline_service
from app.core.offline.local_db import LocalDatabase
from app.core.firebase import db
from fastapi.concurrency import run_in_threadpool

offline_service = get_offline_service()
local_db = LocalDatabase()

async def get_my_flights(user_id: str) -> List[Dict[str, Any]]:
    """사용자의 비행 정보 조회 (오프라인 지원)"""
    
    async def fetch_from_firestore():
        """Firestore에서 비행 정보 조회"""
        flights_ref = db.collection("users").document(user_id).collection("myFlights")
        docs = await run_in_threadpool(lambda: list(flights_ref.stream()))
        
        flights = []
        for doc in docs:
            flight_data = doc.to_dict()
            flight_data["id"] = doc.id
            flights.append(flight_data)
        
        return flights
    
    try:
        # 온라인: Firestore에서 조회 + 로컬 캐시 저장
        # 오프라인: 로컬 DB에서 조회
        if offline_service.network_monitor.is_online:
            flights = await fetch_from_firestore()
            # 로컬 DB에 저장
            for flight in flights:
                local_db.save_my_flight(
                    user_id=user_id,
                    flight_id=flight["id"],
                    flight_data=flight,
                    synced=True
                )
            return flights
        else:
            # 오프라인: 로컬 DB에서 조회
            return local_db.get_my_flights(user_id)
    except Exception as e:
        raise DatabaseError(message=f"비행 정보 조회 중 오류 발생: {e}")

async def save_my_flight(user_id: str, flight_data: Dict[str, Any]) -> Dict[str, Any]:
    """비행 정보 저장 (오프라인 지원)"""
    
    async def save_to_firestore():
        """Firestore에 비행 정보 저장"""
        flights_ref = db.collection("users").document(user_id).collection("myFlights")
        doc = await run_in_threadpool(flights_ref.add, flight_data)
        return {"id": doc.id, **flight_data}
    
    try:
        result = await offline_service.write_with_queue(
            operation_type="create",
            collection_name=f"users/{user_id}/myFlights",
            user_id=user_id,
            data=flight_data,
            online_write_func=save_to_firestore
        )
        return result
    except Exception as e:
        raise DatabaseError(message=f"비행 정보 저장 중 오류 발생: {e}")
```

## 네트워크 모니터링 시작

애플리케이션 시작 시 네트워크 모니터링을 시작해야 합니다.

```python
# app/main.py

from app.core.offline import get_network_monitor

@app.on_event("startup")
async def startup_event():
    # 네트워크 모니터링 시작
    network_monitor = get_network_monitor()
    await network_monitor.start_monitoring(interval=30)
    print("네트워크 모니터링이 시작되었습니다.")

@app.on_event("shutdown")
async def shutdown_event():
    # 네트워크 모니터링 중지
    network_monitor = get_network_monitor()
    await network_monitor.stop_monitoring()
    print("네트워크 모니터링이 중지되었습니다.")
```

## API 엔드포인트 추가

동기화 상태를 확인하고 수동으로 동기화할 수 있는 API를 추가할 수 있습니다.

```python
# app/feature/offline/offline_router.py (새로 생성)

from fastapi import APIRouter, Depends
from app.core.offline import get_offline_service

router = APIRouter(prefix="/offline", tags=["offline"])

@router.get("/status")
async def get_sync_status():
    """동기화 상태 조회"""
    offline_service = get_offline_service()
    return offline_service.get_sync_status()

@router.post("/sync")
async def sync_now():
    """수동 동기화 실행"""
    offline_service = get_offline_service()
    result = await offline_service.sync_now()
    return result
```

## 주의사항

1. **LLM 기능**: LLM 기반 기능(리뷰 요약, 시차적응 계획 생성)은 오프라인에서 사용할 수 없습니다.
2. **실시간 데이터**: 오프라인 상태에서는 캐시된 데이터를 보여주므로 최신 데이터가 아닐 수 있습니다.
3. **큐 크기**: 큐가 너무 커지지 않도록 주기적으로 완료된 항목을 정리해야 합니다.
4. **에러 처리**: 오프라인 상태에서도 사용자에게 명확한 메시지를 제공해야 합니다.

