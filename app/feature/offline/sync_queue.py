"""
오프라인 큐 시스템 모듈
네트워크가 없을 때 요청을 큐에 저장하고, 네트워크 복구 시 동기화합니다.
"""

import json
import asyncio
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

from app.feature.offline.local_db import LocalDatabase
from app.core.network_monitor import NetworkMonitor, get_network_monitor
from app.core.firebase import db
from app.core.exceptions.exceptions import DatabaseError, CustomException


class QueueStatus(Enum):
    """큐 작업 상태"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class SyncQueue:
    """오프라인 동기화 큐 관리 클래스"""
    
    def __init__(self, local_db: Optional[LocalDatabase] = None):
        """
        동기화 큐 초기화
        
        Args:
            local_db: 로컬 데이터베이스 인스턴스
        """
        self.local_db = local_db or LocalDatabase()
        self.network_monitor = get_network_monitor()
        self._syncing: bool = False
        self._sync_task: Optional[asyncio.Task] = None
        
        # 네트워크 상태 변경 시 자동 동기화
        self.network_monitor.add_listener(self._on_network_status_changed)
    
    def _on_network_status_changed(self, status):
        """네트워크 상태 변경 시 자동 동기화 시작"""
        from app.core.network_monitor import NetworkStatus
        if status == NetworkStatus.ONLINE:
            # 온라인 복구 시 자동으로 동기화 시작
            asyncio.create_task(self.sync_all())
    
    async def enqueue(
        self,
        operation_type: str,
        collection_name: str,
        user_id: str,
        data: Dict[str, Any],
        document_id: Optional[str] = None
    ) -> int:
        """
        작업을 큐에 추가
        
        Args:
            operation_type: 작업 유형 ('create', 'update', 'delete')
            collection_name: Firestore 컬렉션 이름
            user_id: 사용자 ID
            data: 작업 데이터
            document_id: 문서 ID (update, delete 시 필수)
            
        Returns:
            큐 항목 ID
        """
        conn = self.local_db._get_connection()
        cursor = conn.cursor()
        
        try:
            now = datetime.utcnow().isoformat()
            cursor.execute("""
                INSERT INTO sync_queue 
                (operation_type, collection_name, document_id, data, user_id, created_at, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                operation_type,
                collection_name,
                document_id,
                json.dumps(data),
                user_id,
                now,
                QueueStatus.PENDING.value
            ))
            conn.commit()
            queue_id = cursor.lastrowid
            
            # 온라인 상태면 즉시 동기화 시도
            if self.network_monitor.is_online:
                asyncio.create_task(self.sync_all())
            
            return queue_id
        except Exception as e:
            conn.rollback()
            raise DatabaseError(message=f"큐에 작업 추가 실패: {e}")
        finally:
            conn.close()
    
    def get_pending_items(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        대기 중인 큐 항목 조회
        
        Args:
            limit: 조회할 항목 수
            
        Returns:
            큐 항목 목록
        """
        conn = self.local_db._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT id, operation_type, collection_name, document_id, 
                       data, user_id, created_at, retry_count, status
                FROM sync_queue 
                WHERE status = ? 
                ORDER BY created_at ASC 
                LIMIT ?
            """, (QueueStatus.PENDING.value, limit))
            
            rows = cursor.fetchall()
            items = []
            for row in rows:
                items.append({
                    "id": row["id"],
                    "operation_type": row["operation_type"],
                    "collection_name": row["collection_name"],
                    "document_id": row["document_id"],
                    "data": json.loads(row["data"]) if row["data"] else None,
                    "user_id": row["user_id"],
                    "created_at": row["created_at"],
                    "retry_count": row["retry_count"],
                    "status": row["status"]
                })
            
            return items
        except Exception as e:
            raise DatabaseError(message=f"큐 항목 조회 실패: {e}")
        finally:
            conn.close()
    
    async def sync_item(self, item_id: int) -> bool:
        """
        단일 큐 항목 동기화
        
        Args:
            item_id: 큐 항목 ID
            
        Returns:
            동기화 성공 여부
        """
        conn = self.local_db._get_connection()
        cursor = conn.cursor()
        
        try:
            # 항목 조회
            cursor.execute("""
                SELECT operation_type, collection_name, document_id, data, user_id
                FROM sync_queue 
                WHERE id = ? AND status = ?
            """, (item_id, QueueStatus.PENDING.value))
            
            row = cursor.fetchone()
            if not row:
                return False
            
            # 상태를 처리 중으로 변경
            cursor.execute("""
                UPDATE sync_queue 
                SET status = ? 
                WHERE id = ?
            """, (QueueStatus.PROCESSING.value, item_id))
            conn.commit()
            
            # Firestore에 동기화
            operation_type = row["operation_type"]
            collection_name = row["collection_name"]
            document_id = row["document_id"]
            data = json.loads(row["data"]) if row["data"] else {}
            user_id = row["user_id"]
            
            success = await self._sync_to_firestore(
                operation_type,
                collection_name,
                document_id,
                data,
                user_id
            )
            
            # 결과에 따라 상태 업데이트
            if success:
                cursor.execute("""
                    UPDATE sync_queue 
                    SET status = ? 
                    WHERE id = ?
                """, (QueueStatus.COMPLETED.value, item_id))
            else:
                # 재시도 횟수 증가
                cursor.execute("""
                    UPDATE sync_queue 
                    SET status = ?, retry_count = retry_count + 1
                    WHERE id = ?
                """, (QueueStatus.PENDING.value, item_id))
            
            conn.commit()
            return success
            
        except Exception as e:
            conn.rollback()
            # 실패 시 상태를 대기로 되돌림
            try:
                cursor.execute("""
                    UPDATE sync_queue 
                    SET status = ?, retry_count = retry_count + 1
                    WHERE id = ?
                """, (QueueStatus.PENDING.value, item_id))
                conn.commit()
            except:
                pass
            raise DatabaseError(message=f"동기화 실패: {e}")
        finally:
            conn.close()
    
    async def _sync_to_firestore(
        self,
        operation_type: str,
        collection_name: str,
        document_id: Optional[str],
        data: Dict[str, Any],
        user_id: str
    ) -> bool:
        """
        Firestore에 동기화
        
        Args:
            operation_type: 작업 유형
            collection_name: 컬렉션 이름
            document_id: 문서 ID
            data: 데이터
            user_id: 사용자 ID
            
        Returns:
            동기화 성공 여부
        """
        try:
            from fastapi.concurrency import run_in_threadpool
            
            collection_ref = db.collection(collection_name)
            
            if operation_type == "create":
                # 문서 ID가 없으면 자동 생성
                if document_id:
                    doc_ref = collection_ref.document(document_id)
                    await run_in_threadpool(doc_ref.set, data)
                else:
                    await run_in_threadpool(collection_ref.add, data)
                    
            elif operation_type == "update":
                if not document_id:
                    return False
                doc_ref = collection_ref.document(document_id)
                await run_in_threadpool(doc_ref.update, data)
                
            elif operation_type == "delete":
                if not document_id:
                    return False
                doc_ref = collection_ref.document(document_id)
                await run_in_threadpool(doc_ref.delete)
            else:
                return False
            
            return True
            
        except Exception as e:
            print(f"Firestore 동기화 오류: {e}")
            return False
    
    async def sync_all(self, max_items: int = 50) -> Dict[str, int]:
        """
        모든 대기 중인 항목 동기화
        
        Args:
            max_items: 최대 동기화할 항목 수
            
        Returns:
            동기화 결과 통계
        """
        if self._syncing:
            return {"status": "already_syncing"}
        
        if not self.network_monitor.is_online:
            return {"status": "offline", "message": "네트워크가 연결되지 않았습니다."}
        
        self._syncing = True
        stats = {
            "total": 0,
            "success": 0,
            "failed": 0
        }
        
        try:
            items = self.get_pending_items(limit=max_items)
            stats["total"] = len(items)
            
            for item in items:
                try:
                    success = await self.sync_item(item["id"])
                    if success:
                        stats["success"] += 1
                    else:
                        stats["failed"] += 1
                except Exception as e:
                    print(f"동기화 오류 (항목 ID: {item['id']}): {e}")
                    stats["failed"] += 1
                
                # 너무 빠른 요청 방지
                await asyncio.sleep(0.1)
            
            return stats
        finally:
            self._syncing = False
    
    def get_queue_stats(self) -> Dict[str, int]:
        """
        큐 통계 조회
        
        Returns:
            큐 통계 딕셔너리
        """
        conn = self.local_db._get_connection()
        cursor = conn.cursor()
        
        try:
            stats = {}
            
            # 상태별 개수
            for status in QueueStatus:
                cursor.execute("""
                    SELECT COUNT(*) FROM sync_queue WHERE status = ?
                """, (status.value,))
                stats[status.value] = cursor.fetchone()[0]
            
            # 총 개수
            cursor.execute("SELECT COUNT(*) FROM sync_queue")
            stats["total"] = cursor.fetchone()[0]
            
            return stats
        except Exception as e:
            raise DatabaseError(message=f"큐 통계 조회 실패: {e}")
        finally:
            conn.close()
    
    def clear_completed_items(self, older_than_days: int = 7):
        """
        완료된 항목 정리 (오래된 항목 삭제)
        
        Args:
            older_than_days: 삭제할 항목의 최소 경과 일수
        """
        conn = self.local_db._get_connection()
        cursor = conn.cursor()
        
        try:
            cutoff_date = datetime.utcnow().timestamp() - (older_than_days * 24 * 3600)
            cutoff_iso = datetime.fromtimestamp(cutoff_date).isoformat()
            
            cursor.execute("""
                DELETE FROM sync_queue 
                WHERE status = ? AND created_at < ?
            """, (QueueStatus.COMPLETED.value, cutoff_iso))
            
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise DatabaseError(message=f"완료된 항목 정리 실패: {e}")
        finally:
            conn.close()


# 전역 동기화 큐 인스턴스
_sync_queue: Optional[SyncQueue] = None


def get_sync_queue() -> SyncQueue:
    """
    전역 동기화 큐 인스턴스 반환
    
    Returns:
        SyncQueue 인스턴스
    """
    global _sync_queue
    if _sync_queue is None:
        _sync_queue = SyncQueue()
    return _sync_queue

