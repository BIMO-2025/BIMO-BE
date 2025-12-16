"""
사용자 비행 기록 (myFlights) 관련 비즈니스 로직
경로: users/{userId}/myFlights/{myFlightId}
"""

from typing import List, Optional
from datetime import datetime
from fastapi.concurrency import run_in_threadpool
from google.cloud.firestore_v1.base_query import FieldFilter

from app.core.firebase import FirebaseService
from app.feature.flights.flights_schemas import MyFlightSchema
from app.core.exceptions.exceptions import (
    DatabaseError,
    CustomException,
)


class MyFlightsService:
    """사용자 비행 기록 관련 비즈니스 로직을 처리하는 서비스 클래스"""
    
    def __init__(self, firebase_service: FirebaseService):
        """
        MyFlightsService 초기화
        
        Args:
            firebase_service: Firebase 서비스 인스턴스
        """
        self.db = firebase_service.db
    
    def _get_collection(self, user_id: str):
        """
        사용자별 myFlights 서브컬렉션 참조 반환
        
        Args:
            user_id: 사용자 ID
            
        Returns:
            Firestore CollectionReference
        """
        return self.db.collection("users").document(user_id).collection("myFlights")

    async def create_flight(self, user_id: str, flight_data: MyFlightSchema) -> str:
        """
        사용자의 비행 기록을 생성합니다.
        
        Args:
            user_id: 사용자 ID
            flight_data: 비행 기록 데이터
            
        Returns:
            생성된 비행 기록 ID
            
        Raises:
            DatabaseError: 데이터베이스 오류 발생 시
        """
        try:
            collection_ref = self._get_collection(user_id)
            
            # Pydantic 모델을 딕셔너리로 변환
            flight_dict = flight_data.model_dump(exclude_none=True)
            
            # Firestore에 저장 (자동 ID 생성)
            doc_ref = collection_ref.document()
            doc_ref.set(flight_dict)
            
            return doc_ref.id
        except Exception as e:
            if isinstance(e, CustomException):
                raise e
            raise DatabaseError(message=f"비행 기록 생성 중 오류 발생: {e}")

    async def get_flights(
        self,
        user_id: str,
        status: Optional[str] = None,
        limit: int = 20
    ) -> List[MyFlightSchema]:
        """
        사용자의 비행 기록 목록을 조회합니다.
        
        Args:
            user_id: 사용자 ID
            status: 비행 상태 필터 ("scheduled" 또는 "completed")
            limit: 조회할 최대 개수
            
        Returns:
            비행 기록 목록 (departureTime 내림차순 정렬)
        """
        try:
            collection_ref = self._get_collection(user_id)
            
            # 쿼리 생성
            query = collection_ref.order_by("departureTime", direction="DESCENDING")
            
            # 상태 필터 적용
            if status:
                query = query.where(filter=FieldFilter("status", "==", status))
            
            # 제한 적용
            query = query.limit(limit)
            
            # 쿼리 실행
            docs = await run_in_threadpool(lambda: list(query.stream()))
            
            # 결과 변환
            flights = []
            for doc in docs:
                flight_data = doc.to_dict()
                flights.append(MyFlightSchema(**flight_data))
            
            return flights
        except Exception as e:
            if isinstance(e, CustomException):
                raise e
            raise DatabaseError(message=f"비행 기록 조회 중 오류 발생: {e}")

    async def get_flight_by_id(self, user_id: str, flight_id: str) -> Optional[MyFlightSchema]:
        """
        특정 비행 기록을 조회합니다.
        
        Args:
            user_id: 사용자 ID
            flight_id: 비행 기록 ID
            
        Returns:
            비행 기록 데이터 (없으면 None)
        """
        try:
            collection_ref = self._get_collection(user_id)
            doc_ref = collection_ref.document(flight_id)
            doc = await run_in_threadpool(doc_ref.get)
            
            if not doc.exists:
                return None
            
            flight_data = doc.to_dict()
            return MyFlightSchema(**flight_data)
        except Exception as e:
            if isinstance(e, CustomException):
                raise e
            raise DatabaseError(message=f"비행 기록 조회 중 오류 발생: {e}")

    async def update_flight(
        self,
        user_id: str,
        flight_id: str,
        update_data: dict
    ) -> bool:
        """
        비행 기록을 업데이트합니다.
        
        Args:
            user_id: 사용자 ID
            flight_id: 비행 기록 ID
            update_data: 업데이트할 데이터 (dict)
            
        Returns:
            업데이트 성공 여부
        """
        try:
            collection_ref = self._get_collection(user_id)
            doc_ref = collection_ref.document(flight_id)
            
            # 업데이트 실행
            await run_in_threadpool(doc_ref.update, update_data)
            
            return True
        except Exception as e:
            if isinstance(e, CustomException):
                raise e
            raise DatabaseError(message=f"비행 기록 업데이트 중 오류 발생: {e}")

    async def delete_flight(self, user_id: str, flight_id: str) -> bool:
        """
        비행 기록을 삭제합니다.
        
        Args:
            user_id: 사용자 ID
            flight_id: 비행 기록 ID
            
        Returns:
            삭제 성공 여부
        """
        try:
            collection_ref = self._get_collection(user_id)
            doc_ref = collection_ref.document(flight_id)
            
            # 삭제 실행
            await run_in_threadpool(doc_ref.delete)
            
            return True
        except Exception as e:
            if isinstance(e, CustomException):
                raise e
            raise DatabaseError(message=f"비행 기록 삭제 중 오류 발생: {e}")

    async def link_review_to_flight(self, user_id: str, flight_id: str, review_id: str) -> bool:
        """
        비행 기록에 리뷰를 연결합니다.
        
        Args:
            user_id: 사용자 ID
            flight_id: 비행 기록 ID
            review_id: 리뷰 ID
            
        Returns:
            연결 성공 여부
        """
        try:
            return await self.update_flight(user_id, flight_id, {"reviewId": review_id})
        except Exception as e:
            if isinstance(e, CustomException):
                raise e
            raise DatabaseError(message=f"리뷰 연결 중 오류 발생: {e}")

    async def update_segment_review_status(
        self,
        user_id: str,
        airline_code: str,
        flight_number: Optional[str],
        has_review: bool
    ) -> bool:
        """
        특정 항공편 segment의 리뷰 작성 여부를 업데이트합니다.
        
        Args:
            user_id: 사용자 ID
            airline_code: 항공사 코드 (예: "KE")
            flight_number: 항공편 번호 (예: "KE901", 선택사항)
            has_review: 리뷰 작성 여부 (True: 리뷰 작성됨, False: 리뷰 없음)
            
        Returns:
            업데이트 성공 여부 (매칭되는 항공편이 없어도 True 반환)
        """
        try:
            # flight_number가 없으면 업데이트하지 않음
            if not flight_number:
                return True
            
            # 사용자의 모든 myFlights 조회
            collection_ref = self._get_collection(user_id)
            docs = await run_in_threadpool(lambda: list(collection_ref.stream()))
            
            # 매칭되는 segment 찾기 및 업데이트
            updated_count = 0
            airline_code_upper = airline_code.upper()
            flight_number_upper = flight_number.upper()
            
            for doc in docs:
                flight_data = doc.to_dict()
                segments = flight_data.get("segments", [])
                
                # segments 배열에서 매칭되는 segment 찾기
                updated = False
                for i, segment in enumerate(segments):
                    segment_carrier = segment.get("operating_carrier", "").upper()
                    segment_flight = segment.get("flight_number", "").upper()
                    
                    # airlineCode와 flightNumber로 매칭
                    if segment_carrier == airline_code_upper and segment_flight == flight_number_upper:
                        segments[i]["hasReview"] = has_review
                        updated = True
                
                # 매칭되는 segment가 있으면 document 업데이트
                if updated:
                    doc_ref = collection_ref.document(doc.id)
                    segments_to_update = flight_data["segments"]
                    await run_in_threadpool(
                        doc_ref.update,
                        {"segments": segments_to_update}
                    )
                    updated_count += 1
            
            # 매칭되는 항공편이 없어도 에러 발생하지 않음 (silent fail)
            return True
            
        except Exception as e:
            # 에러가 발생해도 리뷰 생성/삭제는 성공한 것으로 간주
            # 로깅은 나중에 추가 가능
            return True








