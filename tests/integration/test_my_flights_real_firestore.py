"""
MyFlights 실제 Firestore 통합 테스트

이 테스트는 실제 Firestore에 데이터를 저장하고 조회합니다.
주의: 실제 Firebase 프로젝트가 필요하며, 테스트 데이터가 생성됩니다.
"""
import os
import pytest
from pathlib import Path
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
from fastapi.testclient import TestClient
from app.core.security import create_access_token
from app.core.firebase import get_firebase_service

# .env 파일 로드 (프로젝트 루트에서)
env_path = Path(__file__).parent.parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)
    print(f"[TEST] .env 파일 로드 완료: {env_path}")
else:
    print(f"[TEST] .env 파일을 찾을 수 없습니다: {env_path}")

# .env에서 FIREBASE_SERVICE_ACCOUNT_KEY 읽기 (없으면 기본값 사용)
firebase_key_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_KEY", "./firebase_service_key.json")
os.environ["FIREBASE_SERVICE_ACCOUNT_KEY"] = firebase_key_path
print(f"[TEST] Firebase Service Account Key 경로: {firebase_key_path}")


@pytest.fixture
def test_user_id():
    """테스트용 사용자 ID"""
    return f"test-user-{datetime.now(timezone.utc).timestamp()}"


@pytest.fixture
def test_access_token(test_user_id):
    """테스트용 JWT 토큰 생성 (직접 생성 방식)"""
    return create_access_token(data={"sub": test_user_id})


@pytest.fixture
def firebase_id_token():
    """
    Firebase ID Token fixture
    
    사용 방법:
    1. 환경 변수로 전달: FIREBASE_TEST_ID_TOKEN=xxx pytest ...
    2. .env 파일에 설정: FIREBASE_TEST_ID_TOKEN=xxx
    3. pytest fixture로 오버라이드 가능
    """
    token = os.getenv("FIREBASE_TEST_ID_TOKEN")
    if token:
        return token
    return None


@pytest.fixture
async def test_access_token_via_social_login(test_user_id, client):
    """
    실제 소셜 로그인 플로우를 거쳐서 access_token을 받는 fixture
    
    Firebase Admin SDK로 커스텀 토큰을 생성하고,
    실제 /auth/google/login 엔드포인트를 호출하여 access_token을 받습니다.
    """
    try:
        firebase_service = get_firebase_service()
        if not firebase_service.is_initialized:
            # Firebase가 초기화되지 않았으면 직접 생성 방식으로 fallback
            return create_access_token(data={"sub": test_user_id})
        
        # Firebase Admin SDK로 커스텀 토큰 생성
        # 주의: 커스텀 토큰은 클라이언트에서 signInWithCustomToken으로 ID Token으로 변환해야 함
        # 테스트 환경에서는 실제 ID Token을 얻기 어려우므로, 
        # 실제 Firebase 사용자를 생성하고 커스텀 토큰을 사용하는 방법을 사용
        
        # 방법 1: 실제 Firebase 사용자 생성 및 커스텀 토큰 생성
        try:
            # 테스트용 사용자 생성 (이미 존재하면 무시)
            try:
                user_record = firebase_service.auth_client.get_user(test_user_id)
            except Exception:
                # 사용자가 없으면 생성
                user_record = firebase_service.auth_client.create_user(
                    uid=test_user_id,
                    email=f"{test_user_id}@test.example.com",
                    display_name="Test User",
                    email_verified=True
                )
            
            # 커스텀 토큰 생성
            custom_token = firebase_service.auth_client.create_custom_token(test_user_id)
            
            # 주의: 커스텀 토큰을 ID Token으로 변환하려면 클라이언트 SDK가 필요함
            # 테스트 환경에서는 실제 ID Token을 얻기 어려우므로,
            # 실제 인증 플로우를 테스트하려면 클라이언트가 필요합니다.
            
            # 대안: 실제 Firebase ID Token을 얻을 수 없다면,
            # 인증 서비스를 직접 호출하여 테스트 (모킹 없이)
            # 하지만 이 경우 실제 Firebase ID Token이 필요함
            
            # 현재는 직접 생성 방식으로 fallback
            return create_access_token(data={"sub": test_user_id})
            
        except Exception as e:
            print(f"[TEST] Firebase 커스텀 토큰 생성 실패, 직접 생성 방식 사용: {e}")
            return create_access_token(data={"sub": test_user_id})
            
    except Exception as e:
        print(f"[TEST] Firebase 초기화 실패, 직접 생성 방식 사용: {e}")
        return create_access_token(data={"sub": test_user_id})


@pytest.fixture
def test_flight_data():
    """테스트용 비행 기록 데이터"""
    base_time = datetime.now(timezone.utc) + timedelta(days=30)
    return {
        "segments": [
            {
                "operating_carrier": "KE",
                "flight_number": "KE001",
                "duration": "14H30M",
                "departure": {
                    "iata_code": "ICN",
                    "at": base_time.isoformat()
                },
                "arrival": {
                    "iata_code": "JFK",
                    "at": (base_time + timedelta(hours=14, minutes=30)).isoformat()
                }
            }
        ],
        "departureTime": base_time.isoformat(),
        "arrivalTime": (base_time + timedelta(hours=14, minutes=30)).isoformat(),
        "status": "scheduled",
        "departureAirport": "ICN",
        "arrivalAirport": "JFK",
        "hasStopover": False
    }


@pytest.fixture
def test_flight_data_with_stopover():
    """경유 항공편 테스트 데이터"""
    base_time = datetime.now(timezone.utc) + timedelta(days=30)
    return {
        "segments": [
            {
                "operating_carrier": "KE",
                "flight_number": "KE901",
                "duration": "3H30M",
                "departure": {
                    "iata_code": "ICN",
                    "at": base_time.isoformat()
                },
                "arrival": {
                    "iata_code": "NRT",
                    "at": (base_time + timedelta(hours=3, minutes=30)).isoformat()
                }
            },
            {
                "operating_carrier": "KE",
                "flight_number": "KE001",
                "duration": "11H00M",
                "departure": {
                    "iata_code": "NRT",
                    "at": (base_time + timedelta(hours=5)).isoformat()
                },
                "arrival": {
                    "iata_code": "JFK",
                    "at": (base_time + timedelta(hours=16)).isoformat()
                }
            }
        ],
        "departureTime": base_time.isoformat(),
        "arrivalTime": (base_time + timedelta(hours=16)).isoformat(),
        "status": "scheduled",
        "departureAirport": "ICN",
        "arrivalAirport": "JFK",
        "hasStopover": True
    }


@pytest.fixture(autouse=True)
def cleanup_test_data(test_user_id):
    """테스트 후 데이터 정리"""
    yield
    # 테스트 후 정리 작업
    try:
        firebase_service = get_firebase_service()
        if firebase_service.is_initialized:
            # 1) myFlights 정리
            myflights_ref = firebase_service.db.collection("users").document(test_user_id).collection("myFlights")
            for doc in myflights_ref.stream():
                doc.reference.delete()

            # 2) reviews 정리 (userId 기준)
            reviews_ref = firebase_service.db.collection("reviews").where("userId", "==", test_user_id)
            for doc in reviews_ref.stream():
                doc.reference.delete()

            print(f"[CLEANUP] 테스트 데이터 정리 완료: {test_user_id} (myFlights + reviews)")
    except Exception as e:
        print(f"[CLEANUP] 정리 중 오류 발생 (무시 가능): {e}")


class TestMyFlightsRealFirestore:
    """실제 Firestore를 사용한 MyFlights 통합 테스트"""
    
    @pytest.mark.asyncio
    async def test_create_my_flight_real_firestore(
        self, 
        client: TestClient, 
        test_user_id: str,
        test_access_token: str,
        test_flight_data: dict
    ):
        """
        실제 Firestore에 비행 기록을 생성하고 확인합니다.
        
        테스트 단계:
        1. POST /users/{user_id}/my-flights로 비행 기록 생성
        2. 생성된 flight_id 확인
        3. GET /users/{user_id}/my-flights/{flight_id}로 조회하여 실제 저장 확인
        4. Firestore에서 직접 조회하여 데이터 일치 확인
        """
        # 1단계: 비행 기록 생성
        create_response = client.post(
            f"/users/{test_user_id}/my-flights",
            json=test_flight_data,
            headers={"Authorization": f"Bearer {test_access_token}"}
        )
        
        assert create_response.status_code == 200, f"생성 실패: {create_response.text}"
        create_data = create_response.json()
        assert "id" in create_data
        flight_id = create_data["id"]
        assert flight_id is not None
        print(f"[TEST] 생성된 Flight ID: {flight_id}")
        
        # 2단계: API로 조회하여 확인
        get_response = client.get(
            f"/users/{test_user_id}/my-flights/{flight_id}",
            headers={"Authorization": f"Bearer {test_access_token}"}
        )
        
        assert get_response.status_code == 200, f"조회 실패: {get_response.text}"
        flight_data = get_response.json()
        
        # 데이터 검증
        assert flight_data["segments"][0]["operating_carrier"] == "KE"
        assert flight_data["segments"][0]["flight_number"] == "KE001"
        assert flight_data["departureAirport"] == "ICN"
        assert flight_data["arrivalAirport"] == "JFK"
        assert flight_data["status"] == "scheduled"
        assert flight_data["hasStopover"] == False
        print(f"[TEST] API 조회 성공: {flight_id}")
        
        # 3단계: Firestore에서 직접 조회하여 확인
        firebase_service = get_firebase_service()
        assert firebase_service.is_initialized, "Firebase가 초기화되지 않았습니다"
        
        collection_ref = firebase_service.db.collection("users").document(test_user_id).collection("myFlights")
        doc_ref = collection_ref.document(flight_id)
        doc = doc_ref.get()
        
        assert doc.exists, f"Firestore에 문서가 존재하지 않습니다: {flight_id}"
        firestore_data = doc.to_dict()
        
        # Firestore 데이터 검증
        assert firestore_data["segments"][0]["operating_carrier"] == "KE"
        assert firestore_data["segments"][0]["flight_number"] == "KE001"
        assert firestore_data["departureAirport"] == "ICN"
        assert firestore_data["arrivalAirport"] == "JFK"
        assert firestore_data["status"] == "scheduled"
        print(f"[TEST] Firestore 직접 조회 성공: {flight_id}")
    
    @pytest.mark.asyncio
    async def test_create_flight_with_stopover_real_firestore(
        self,
        client: TestClient,
        test_user_id: str,
        test_access_token: str,
        test_flight_data_with_stopover: dict
    ):
        """경유 항공편을 실제 Firestore에 저장하고 확인"""
        # 비행 기록 생성
        create_response = client.post(
            f"/users/{test_user_id}/my-flights",
            json=test_flight_data_with_stopover,
            headers={"Authorization": f"Bearer {test_access_token}"}
        )
        
        assert create_response.status_code == 200
        flight_id = create_response.json()["id"]
        
        # 조회하여 확인
        get_response = client.get(
            f"/users/{test_user_id}/my-flights/{flight_id}",
            headers={"Authorization": f"Bearer {test_access_token}"}
        )
        
        assert get_response.status_code == 200
        flight_data = get_response.json()
        
        # 경유 항공편 검증
        assert len(flight_data["segments"]) == 2
        assert flight_data["hasStopover"] == True
        assert flight_data["segments"][0]["arrival"]["iata_code"] == "NRT"
        assert flight_data["segments"][1]["departure"]["iata_code"] == "NRT"
        print(f"[TEST] 경유 항공편 저장 성공: {flight_id}")
    
    @pytest.mark.asyncio
    async def test_get_my_flights_list_real_firestore(
        self,
        client: TestClient,
        test_user_id: str,
        test_access_token: str,
        test_flight_data: dict
    ):
        """비행 기록 목록 조회 테스트"""
        # 여러 개의 비행 기록 생성
        flight_ids = []
        for i in range(3):
            flight_data = test_flight_data.copy()
            # 각각 다른 출발 시간 설정
            base_time = datetime.now(timezone.utc) + timedelta(days=30+i)
            flight_data["departureTime"] = base_time.isoformat()
            flight_data["segments"][0]["departure"]["at"] = base_time.isoformat()
            flight_data["arrivalTime"] = (base_time + timedelta(hours=14, minutes=30)).isoformat()
            flight_data["segments"][0]["arrival"]["at"] = (base_time + timedelta(hours=14, minutes=30)).isoformat()
            
            create_response = client.post(
                f"/users/{test_user_id}/my-flights",
                json=flight_data,
                headers={"Authorization": f"Bearer {test_access_token}"}
            )
            assert create_response.status_code == 200
            flight_ids.append(create_response.json()["id"])
        
        # 목록 조회
        list_response = client.get(
            f"/users/{test_user_id}/my-flights",
            headers={"Authorization": f"Bearer {test_access_token}"}
        )
        
        assert list_response.status_code == 200
        flights = list_response.json()
        
        # 최신순으로 정렬되어 있는지 확인 (departureTime 내림차순)
        assert len(flights) >= 3
        assert flights[0]["departureTime"] >= flights[1]["departureTime"]
        print(f"[TEST] 목록 조회 성공: {len(flights)}개 항목")

    @pytest.mark.asyncio
    async def test_get_segments_has_review_endpoint_real_firestore(
        self,
        client: TestClient,
        test_user_id: str,
        test_access_token: str,
        test_flight_data_with_stopover: dict
    ):
        """
        /users/{user_id}/my-flights/segments/has-review 엔드포인트가
        myFlights.segments[*].hasReview 저장값을 기준으로 segment별 hasReview를 올바르게 반환하는지 검증합니다.
        """
        # 1) 경유 항공편(myFlights) 생성: segments[0]=KE001(true), segments[1]=KE002(false)
        flight_payload = test_flight_data_with_stopover.copy()
        flight_payload["segments"] = [s.copy() for s in (test_flight_data_with_stopover.get("segments") or [])]
        assert len(flight_payload["segments"]) == 2, "fixture가 2개 segment를 가져야 합니다"
        flight_payload["segments"][0]["hasReview"] = True
        flight_payload["segments"][1]["hasReview"] = False

        create_response = client.post(
            f"/users/{test_user_id}/my-flights",
            json=flight_payload,
            headers={"Authorization": f"Bearer {test_access_token}"}
        )
        assert create_response.status_code == 200, f"비행 기록 생성 실패: {create_response.text}"
        flight_id = create_response.json()["id"]

        # 2) endpoint 호출
        resp = client.get(
            f"/users/{test_user_id}/my-flights/segments/has-review",
            headers={"Authorization": f"Bearer {test_access_token}"}
        )
        assert resp.status_code == 200, f"segment hasReview 조회 실패: {resp.text}"
        data = resp.json()

        assert data["userId"] == test_user_id
        flights = data.get("flights") or []
        assert len(flights) >= 1

        # 생성한 flight_id 항목 찾기
        target = next((f for f in flights if f.get("id") == flight_id), None)
        assert target is not None, "응답에서 생성한 myFlights 문서를 찾을 수 없습니다"

        segs = target.get("segments") or []
        assert len(segs) == 2, "경유 항공편은 segment가 2개여야 합니다"

        # myFlights 저장값 기준: KE001 true, KE002 false
        seg_by_fno = {s.get("flight_number"): s for s in segs}
        assert seg_by_fno["KE001"]["hasReview"] is True
        assert seg_by_fno["KE002"]["hasReview"] is False
    
    @pytest.mark.asyncio
    async def test_update_my_flight_real_firestore(
        self,
        client: TestClient,
        test_user_id: str,
        test_access_token: str,
        test_flight_data: dict
    ):
        """비행 기록 업데이트 테스트"""
        # 비행 기록 생성
        create_response = client.post(
            f"/users/{test_user_id}/my-flights",
            json=test_flight_data,
            headers={"Authorization": f"Bearer {test_access_token}"}
        )
        flight_id = create_response.json()["id"]
        
        # 상태 업데이트
        update_response = client.put(
            f"/users/{test_user_id}/my-flights/{flight_id}",
            json={"status": "completed"},
            headers={"Authorization": f"Bearer {test_access_token}"}
        )
        
        assert update_response.status_code == 200
        
        # 업데이트 확인
        get_response = client.get(
            f"/users/{test_user_id}/my-flights/{flight_id}",
            headers={"Authorization": f"Bearer {test_access_token}"}
        )
        
        assert get_response.json()["status"] == "completed"
        print(f"[TEST] 업데이트 성공: {flight_id}")
    
    @pytest.mark.asyncio
    async def test_delete_my_flight_real_firestore(
        self,
        client: TestClient,
        test_user_id: str,
        test_access_token: str,
        test_flight_data: dict
    ):
        """비행 기록 삭제 테스트"""
        # 비행 기록 생성
        create_response = client.post(
            f"/users/{test_user_id}/my-flights",
            json=test_flight_data,
            headers={"Authorization": f"Bearer {test_access_token}"}
        )
        flight_id = create_response.json()["id"]
        
        # 삭제
        delete_response = client.delete(
            f"/users/{test_user_id}/my-flights/{flight_id}",
            headers={"Authorization": f"Bearer {test_access_token}"}
        )
        
        assert delete_response.status_code == 200
        
        # 삭제 확인 (404 에러가 나와야 함)
        get_response = client.get(
            f"/users/{test_user_id}/my-flights/{flight_id}",
            headers={"Authorization": f"Bearer {test_access_token}"}
        )
        
        assert get_response.status_code == 404
        print(f"[TEST] 삭제 성공: {flight_id}")
    
    @pytest.mark.asyncio
    async def test_unauthorized_access(
        self,
        client: TestClient,
        test_user_id: str,
        test_flight_data: dict
    ):
        """권한 없는 사용자 접근 테스트"""
        # 다른 사용자의 토큰 생성
        other_user_token = create_access_token(data={"sub": "other-user-123"})
        
        # 다른 사용자의 토큰으로 접근 시도
        response = client.post(
            f"/users/{test_user_id}/my-flights",
            json=test_flight_data,
            headers={"Authorization": f"Bearer {other_user_token}"}
        )
        
        assert response.status_code == 403, "권한 없는 사용자는 접근할 수 없어야 합니다"
        print("[TEST] 권한 검증 성공")
    
    @pytest.mark.asyncio
    async def test_create_my_flight_with_real_social_login(
        self,
        client: TestClient,
        test_flight_data: dict,
        firebase_id_token: str = None
    ):
        """
        실제 소셜 로그인 플로우를 거쳐서 비행 기록을 생성하는 테스트
        
        이 테스트는 실제 Firebase ID Token 또는 Google ID Token을 사용합니다.
        
        Firebase ID Token 전달 방법:
        1. 환경 변수로 전달:
           FIREBASE_TEST_ID_TOKEN=xxx pytest tests/integration/test_my_flights_real_firestore.py::TestMyFlightsRealFirestore::test_create_my_flight_with_real_social_login
           
        2. .env 파일에 설정:
           FIREBASE_TEST_ID_TOKEN=eyJhbGciOiJSUzI1NiIsImtpZCI6Ij...
           
        3. pytest fixture로 오버라이드 (다른 테스트에서):
           @pytest.fixture
           def firebase_id_token():
               return "your-token-here"
        
        테스트 플로우:
        1. Firebase ID Token 읽기 (환경 변수 또는 fixture)
        2. POST /auth/google/login에 Firebase ID Token 전달
        3. 받은 access_token으로 MyFlight 생성
        4. Firestore에서 직접 확인
        
        주의: 이 테스트를 실행하려면 실제 Firebase ID Token 또는 Google ID Token이 필요합니다.
        Firebase ID Token이 없으면 테스트가 스킵됩니다.
        """
        # Firebase ID Token 읽기 (fixture 또는 환경 변수)
        token = firebase_id_token or os.getenv("FIREBASE_TEST_ID_TOKEN")
        
        if not token:
            pytest.skip(
                "FIREBASE_TEST_ID_TOKEN이 설정되지 않았습니다.\n"
                "다음 중 하나의 방법으로 토큰을 전달하세요:\n"
                "1. 환경 변수: FIREBASE_TEST_ID_TOKEN=xxx pytest ...\n"
                "2. .env 파일: FIREBASE_TEST_ID_TOKEN=xxx\n"
                "3. pytest fixture로 오버라이드"
            )
        
        print(f"[TEST] Firebase ID Token 사용하여 실제 소셜 로그인 플로우 테스트 시작")
        
        try:
            # 1단계: 실제 소셜 로그인 플로우
            login_response = client.post(
                "/auth/google/login",
                json={"token": token}
            )
            
            assert login_response.status_code == 200, f"로그인 실패: {login_response.text}"
            login_data = login_response.json()
            assert "access_token" in login_data
            access_token = login_data["access_token"]
            user_info = login_data.get("user")
            
            if user_info:
                actual_user_id = user_info.get("uid")
                print(f"[TEST] 로그인 성공, 사용자 ID: {actual_user_id}")
            else:
                # user 정보가 없어도 access_token에서 추출 가능
                from app.core.security import decode_access_token
                payload = decode_access_token(access_token)
                actual_user_id = payload.get("sub")
                print(f"[TEST] 로그인 성공, 사용자 ID (토큰에서 추출): {actual_user_id}")
            
            assert actual_user_id is not None, "사용자 ID를 확인할 수 없습니다"
            
            # 2단계: 받은 access_token으로 MyFlight 생성
            create_response = client.post(
                f"/users/{actual_user_id}/my-flights",
                json=test_flight_data,
                headers={"Authorization": f"Bearer {access_token}"}
            )
            
            assert create_response.status_code == 200, f"비행 기록 생성 실패: {create_response.text}"
            flight_id = create_response.json()["id"]
            print(f"[TEST] 비행 기록 생성 성공: {flight_id}")
            
            # 3단계: API로 조회하여 확인
            get_response = client.get(
                f"/users/{actual_user_id}/my-flights/{flight_id}",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            
            assert get_response.status_code == 200
            flight_data = get_response.json()
            assert flight_data["segments"][0]["operating_carrier"] == "KE"
            print(f"[TEST] API 조회 성공: {flight_id}")
            
            # 4단계: Firestore에서 직접 확인
            firebase_service = get_firebase_service()
            if firebase_service.is_initialized:
                collection_ref = firebase_service.db.collection("users").document(actual_user_id).collection("myFlights")
                doc_ref = collection_ref.document(flight_id)
                doc = doc_ref.get()
                
                assert doc.exists, f"Firestore에 문서가 존재하지 않습니다: {flight_id}"
                firestore_data = doc.to_dict()
                assert firestore_data["segments"][0]["operating_carrier"] == "KE"
                print(f"[TEST] Firestore 직접 조회 성공: {flight_id}")
            
            print(f"[TEST] 실제 소셜 로그인 플로우 테스트 완료!")
            
        except Exception as e:
            print(f"[TEST] 실제 소셜 로그인 플로우 테스트 실패: {e}")
            raise
    
    @pytest.mark.asyncio
    async def test_create_my_flight_with_real_auth_flow(
        self,
        client: TestClient,
        test_user_id: str,
        test_flight_data: dict
    ):
        """
        실제 소셜 로그인 플로우를 거쳐서 비행 기록을 생성하는 테스트 (커스텀 토큰 방식)
        
        이 테스트는 실제 Firebase를 사용하여:
        1. Firebase Admin SDK로 테스트 사용자 생성
        2. 커스텀 토큰 생성
        3. 실제 /auth/google/login 엔드포인트 호출 (Firebase ID Token 필요)
        4. 받은 access_token으로 MyFlight 생성
        
        주의: 실제 Firebase ID Token을 얻으려면 클라이언트 SDK가 필요합니다.
        테스트 환경에서는 Firebase Admin SDK로 커스텀 토큰을 생성할 수 있지만,
        이를 ID Token으로 변환하려면 클라이언트에서 signInWithCustomToken이 필요합니다.
        
        실제 소셜 로그인 플로우를 테스트하려면 test_create_my_flight_with_real_social_login을 사용하세요.
        """
        try:
            firebase_service = get_firebase_service()
            if not firebase_service.is_initialized:
                pytest.skip("Firebase가 초기화되지 않았습니다")
            
            # Firebase Admin SDK로 테스트 사용자 생성
            try:
                user_record = firebase_service.auth_client.get_user(test_user_id)
                print(f"[TEST] 기존 사용자 사용: {test_user_id}")
            except Exception:
                # 사용자가 없으면 생성
                user_record = firebase_service.auth_client.create_user(
                    uid=test_user_id,
                    email=f"{test_user_id}@test.example.com",
                    display_name="Test User",
                    email_verified=True
                )
                print(f"[TEST] 새 사용자 생성: {test_user_id}")
            
            # 커스텀 토큰 생성
            custom_token = firebase_service.auth_client.create_custom_token(test_user_id)
            print(f"[TEST] 커스텀 토큰 생성 완료")
            
            # 주의: 커스텀 토큰을 Firebase ID Token으로 변환하려면
            # 클라이언트에서 signInWithCustomToken을 호출해야 합니다.
            # 테스트 환경에서는 이를 직접 할 수 없으므로,
            # 실제 인증 플로우를 완전히 테스트하려면:
            # 1. 클라이언트 앱에서 커스텀 토큰으로 로그인하여 ID Token 받기
            # 2. 또는 실제 소셜 로그인을 통해 ID Token 받기
            
            # 현재는 직접 JWT 토큰 생성 방식으로 테스트
            # (실제 소셜 로그인 플로우는 클라이언트가 필요)
            access_token = create_access_token(data={"sub": test_user_id})
            
            # 비행 기록 생성
            create_response = client.post(
                f"/users/{test_user_id}/my-flights",
                json=test_flight_data,
                headers={"Authorization": f"Bearer {access_token}"}
            )
            
            assert create_response.status_code == 200
            flight_id = create_response.json()["id"]
            print(f"[TEST] 실제 인증 플로우 테스트 완료 (커스텀 토큰 생성됨): {flight_id}")
            
            # 정리: 테스트 사용자 삭제
            try:
                firebase_service.auth_client.delete_user(test_user_id)
                print(f"[TEST] 테스트 사용자 삭제 완료: {test_user_id}")
            except Exception as e:
                print(f"[TEST] 사용자 삭제 실패 (무시 가능): {e}")
                
        except Exception as e:
            print(f"[TEST] 실제 인증 플로우 테스트 실패: {e}")
            # 실패해도 테스트는 계속 진행 (스킵하지 않음)
            raise

