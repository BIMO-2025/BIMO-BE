"""
오프라인 기능 통합 서비스
오프라인/온라인 상태에 따라 적절한 데이터 소스를 선택하여 작업을 수행합니다.
"""

from typing import Optional, List, Dict, Any, Callable
from datetime import datetime

from app.feature.offline.local_db import LocalDatabase
from app.core.network_monitor import NetworkMonitor
from app.feature.offline.sync_queue import SyncQueue
from app.feature.offline.cache_service import CacheService
from app.core.exceptions.exceptions import DatabaseError, CustomException


class OfflineService:
    """오프라인 기능 통합 서비스 클래스"""
    
    def __init__(
        self,
        local_db: LocalDatabase,
        network_monitor: NetworkMonitor,
        sync_queue: SyncQueue,
        cache_service: CacheService
    ):
        """
        오프라인 서비스 초기화
        
        Args:
            local_db: 로컬 데이터베이스 인스턴스
            network_monitor: 네트워크 모니터 인스턴스
            sync_queue: 동기화 큐 인스턴스
            cache_service: 캐시 서비스 인스턴스
        """
        self.local_db = local_db
        self.network_monitor = network_monitor
        self.sync_queue = sync_queue
        self.cache_service = cache_service
    
    async def read_with_fallback(
        self,
        cache_key: str,
        fetch_func: Callable,
        cache_ttl_hours: int = 24
    ) -> Any:
        """
        읽기 작업: 온라인 시 Firestore에서 조회, 오프라인 시 로컬 캐시에서 조회
        
        Args:
            cache_key: 캐시 키
            fetch_func: Firestore에서 데이터를 가져올 함수 (비동기)
            cache_ttl_hours: 캐시 유효 시간
            
        Returns:
            데이터
        """
        return await self.cache_service.get_or_fetch(
            cache_key=cache_key,
            fetch_func=fetch_func,
            cache_ttl_hours=cache_ttl_hours,
            force_refresh=False
        )
    
    async def write_with_queue(
        self,
        operation_type: str,
        collection_name: str,
        user_id: str,
        data: Dict[str, Any],
        document_id: Optional[str] = None,
        online_write_func: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """
        쓰기 작업: 온라인 시 즉시 Firestore에 저장, 오프라인 시 큐에 추가
        
        Args:
            operation_type: 작업 유형 ('create', 'update', 'delete')
            collection_name: Firestore 컬렉션 이름
            user_id: 사용자 ID
            data: 작업 데이터
            document_id: 문서 ID (update, delete 시 필수)
            online_write_func: 온라인 상태일 때 실행할 함수 (선택적)
            
        Returns:
            작업 결과
        """
        if self.network_monitor.is_online:
            # 온라인 상태: 즉시 Firestore에 저장
            if online_write_func:
                try:
                    result = await online_write_func()
                    # 성공 시 로컬 DB에도 저장 (캐시 업데이트)
                    if operation_type == "create" and document_id:
                        # 생성 작업의 경우 결과에서 ID 추출
                        if isinstance(result, dict) and "id" in result:
                            document_id = result["id"]
                        await self._update_local_cache(
                            collection_name, document_id, data, user_id
                        )
                    return result
                except Exception as e:
                    # Firestore 저장 실패 시 큐에 추가
                    print(f"Firestore 저장 실패, 큐에 추가: {e}")
                    queue_id = await self.sync_queue.enqueue(
                        operation_type, collection_name, user_id, data, document_id
                    )
                    return {
                        "status": "queued",
                        "queue_id": queue_id,
                        "message": "네트워크 오류로 큐에 추가되었습니다."
                    }
            else:
                # online_write_func이 없으면 큐에만 추가
                queue_id = await self.sync_queue.enqueue(
                    operation_type, collection_name, user_id, data, document_id
                )
                return {
                    "status": "queued",
                    "queue_id": queue_id
                }
        else:
            # 오프라인 상태: 로컬 DB에 저장하고 큐에 추가
            queue_id = await self.sync_queue.enqueue(
                operation_type, collection_name, user_id, data, document_id
            )
            
            # 로컬 DB에도 저장 (오프라인에서도 조회 가능하도록)
            await self._save_to_local_db(
                collection_name, document_id or "temp", data, user_id
            )
            
            return {
                "status": "offline_saved",
                "queue_id": queue_id,
                "message": "오프라인 상태입니다. 네트워크 복구 시 자동으로 동기화됩니다."
            }
    
    async def _save_to_local_db(
        self,
        collection_name: str,
        document_id: str,
        data: Dict[str, Any],
        user_id: str
    ):
        """
        로컬 DB에 데이터 저장
        
        Args:
            collection_name: 컬렉션 이름
            document_id: 문서 ID
            data: 데이터
            user_id: 사용자 ID
        """
        try:
            if collection_name == "myFlights" or collection_name == "users/{userId}/myFlights":
                # 비행 정보 저장
                self.local_db.save_my_flight(
                    user_id=user_id,
                    flight_id=document_id,
                    flight_data=data,
                    synced=False
                )
        except Exception as e:
            # 로컬 저장 실패는 무시 (큐에만 저장되어도 동기화 가능)
            print(f"로컬 DB 저장 실패: {e}")
    
    async def _update_local_cache(
        self,
        collection_name: str,
        document_id: str,
        data: Dict[str, Any],
        user_id: str
    ):
        """
        로컬 캐시 업데이트
        
        Args:
            collection_name: 컬렉션 이름
            document_id: 문서 ID
            data: 데이터
            user_id: 사용자 ID
        """
        try:
            if collection_name == "myFlights" or collection_name == "users/{userId}/myFlights":
                # 비행 정보 캐시 업데이트
                self.local_db.save_my_flight(
                    user_id=user_id,
                    flight_id=document_id,
                    flight_data=data,
                    synced=True
                )
        except Exception as e:
            print(f"로컬 캐시 업데이트 실패: {e}")
    
    def get_sync_status(self) -> Dict[str, Any]:
        """
        동기화 상태 조회
        
        Returns:
            동기화 상태 정보
        """
        queue_stats = self.sync_queue.get_queue_stats()
        
        return {
            "network_status": self.network_monitor.status.value,
            "is_online": self.network_monitor.is_online,
            "queue_stats": queue_stats,
            "pending_count": queue_stats.get("pending", 0),
            "processing_count": queue_stats.get("processing", 0),
            "completed_count": queue_stats.get("completed", 0),
            "failed_count": queue_stats.get("failed", 0)
        }
    

    async def sync_now(self) -> Dict[str, Any]:
        """
        수동 동기화 실행
        
        Returns:
            동기화 결과
        """
        return await self.sync_queue.sync_all()

