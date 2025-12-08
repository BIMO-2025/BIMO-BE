"""
로컬 SQLite 데이터베이스 관리 모듈
오프라인 상태에서 데이터를 저장하고 조회합니다.
"""

import sqlite3
import json
from typing import Optional, List, Dict, Any
from datetime import datetime
from pathlib import Path
import os

from app.core.exceptions.exceptions import DatabaseError


class LocalDatabase:
    """로컬 SQLite 데이터베이스 관리 클래스"""
    
    def __init__(self, db_path: Optional[str] = None):
        """
        로컬 데이터베이스 초기화
        
        Args:
            db_path: 데이터베이스 파일 경로 (기본값: 프로젝트 루트/bimo_offline.db)
        """
        if db_path is None:
            # 프로젝트 루트 디렉토리에 데이터베이스 파일 생성
            project_root = Path(__file__).parent.parent.parent
            db_path = str(project_root / "bimo_offline.db")
        
        self.db_path = db_path
        self._ensure_db_directory()
        self._init_database()
    
    def _ensure_db_directory(self):
        """데이터베이스 파일이 위치할 디렉토리가 존재하는지 확인"""
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)
    
    def _init_database(self):
        """데이터베이스 테이블 초기화"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # 사용자 비행 정보 테이블
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS my_flights (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    flight_number TEXT NOT NULL,
                    airline_code TEXT NOT NULL,
                    departure_time TEXT NOT NULL,
                    arrival_time TEXT NOT NULL,
                    status TEXT NOT NULL,
                    review_id TEXT,
                    data TEXT NOT NULL,  -- 전체 데이터 JSON
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    synced INTEGER DEFAULT 0  -- 0: 미동기화, 1: 동기화됨
                )
            """)
            
            # 리뷰 캐시 테이블
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS reviews_cache (
                    id TEXT PRIMARY KEY,
                    airline_code TEXT NOT NULL,
                    data TEXT NOT NULL,  -- 리뷰 데이터 JSON
                    cached_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL
                )
            """)
            
            # 시차적응 계획 테이블
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS jetlag_plans (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    plan_key TEXT NOT NULL,  -- 요청 파라미터 기반 고유 키
                    data TEXT NOT NULL,  -- 계획 데이터 JSON
                    created_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL
                )
            """)
            
            # 사용자 프로필 캐시 테이블
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_profiles (
                    user_id TEXT PRIMARY KEY,
                    data TEXT NOT NULL,  -- 사용자 데이터 JSON
                    cached_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL
                )
            """)
            
            # 오프라인 큐 테이블 (sync_queue.py에서도 사용)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sync_queue (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    operation_type TEXT NOT NULL,  -- 'create', 'update', 'delete'
                    collection_name TEXT NOT NULL,  -- Firestore 컬렉션 이름
                    document_id TEXT,
                    data TEXT,  -- 작업 데이터 JSON
                    user_id TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    retry_count INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'pending'  -- 'pending', 'processing', 'completed', 'failed'
                )
            """)
            
            # 인덱스 생성
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_my_flights_user_id 
                ON my_flights(user_id)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_my_flights_synced 
                ON my_flights(synced)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_reviews_cache_airline 
                ON reviews_cache(airline_code)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_jetlag_plans_user_id 
                ON jetlag_plans(user_id)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_sync_queue_status 
                ON sync_queue(status)
            """)
            
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise DatabaseError(message=f"로컬 데이터베이스 초기화 실패: {e}")
        finally:
            conn.close()
    
    def _get_connection(self) -> sqlite3.Connection:
        """데이터베이스 연결 반환"""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row  # 딕셔너리 형태로 결과 반환
        return conn
    
    # ========== MyFlights 관련 메서드 ==========
    
    def save_my_flight(
        self, 
        user_id: str, 
        flight_id: str, 
        flight_data: Dict[str, Any],
        synced: bool = False
    ) -> bool:
        """
        사용자 비행 정보를 로컬 DB에 저장
        
        Args:
            user_id: 사용자 ID
            flight_id: 비행 ID
            flight_data: 비행 데이터 딕셔너리
            synced: 동기화 여부
            
        Returns:
            저장 성공 여부
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            now = datetime.utcnow().isoformat()
            cursor.execute("""
                INSERT OR REPLACE INTO my_flights 
                (id, user_id, flight_number, airline_code, departure_time, 
                 arrival_time, status, review_id, data, created_at, updated_at, synced)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                flight_id,
                user_id,
                flight_data.get("flightNumber", ""),
                flight_data.get("airlineCode", ""),
                flight_data.get("departureTime", ""),
                flight_data.get("arrivalTime", ""),
                flight_data.get("status", "scheduled"),
                flight_data.get("reviewId"),
                json.dumps(flight_data),
                now,
                now,
                1 if synced else 0
            ))
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            raise DatabaseError(message=f"비행 정보 저장 실패: {e}")
        finally:
            conn.close()
    
    def get_my_flights(self, user_id: str) -> List[Dict[str, Any]]:
        """
        사용자의 비행 정보 목록 조회
        
        Args:
            user_id: 사용자 ID
            
        Returns:
            비행 정보 목록
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT data FROM my_flights 
                WHERE user_id = ? 
                ORDER BY departure_time DESC
            """, (user_id,))
            
            rows = cursor.fetchall()
            flights = []
            for row in rows:
                flights.append(json.loads(row["data"]))
            
            return flights
        except Exception as e:
            raise DatabaseError(message=f"비행 정보 조회 실패: {e}")
        finally:
            conn.close()
    
    def get_my_flight(self, user_id: str, flight_id: str) -> Optional[Dict[str, Any]]:
        """
        특정 비행 정보 조회
        
        Args:
            user_id: 사용자 ID
            flight_id: 비행 ID
            
        Returns:
            비행 정보 또는 None
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT data FROM my_flights 
                WHERE id = ? AND user_id = ?
            """, (flight_id, user_id))
            
            row = cursor.fetchone()
            if row:
                return json.loads(row["data"])
            return None
        except Exception as e:
            raise DatabaseError(message=f"비행 정보 조회 실패: {e}")
        finally:
            conn.close()
    
    def delete_my_flight(self, user_id: str, flight_id: str) -> bool:
        """
        비행 정보 삭제
        
        Args:
            user_id: 사용자 ID
            flight_id: 비행 ID
            
        Returns:
            삭제 성공 여부
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                DELETE FROM my_flights 
                WHERE id = ? AND user_id = ?
            """, (flight_id, user_id))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            conn.rollback()
            raise DatabaseError(message=f"비행 정보 삭제 실패: {e}")
        finally:
            conn.close()
    
    def mark_flight_synced(self, flight_id: str) -> bool:
        """
        비행 정보를 동기화 완료로 표시
        
        Args:
            flight_id: 비행 ID
            
        Returns:
            업데이트 성공 여부
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                UPDATE my_flights 
                SET synced = 1, updated_at = ? 
                WHERE id = ?
            """, (datetime.utcnow().isoformat(), flight_id))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            conn.rollback()
            raise DatabaseError(message=f"동기화 상태 업데이트 실패: {e}")
        finally:
            conn.close()
    
    # ========== 리뷰 캐시 관련 메서드 ==========
    
    def cache_reviews(self, airline_code: str, reviews: List[Dict[str, Any]], ttl_hours: int = 24):
        """
        리뷰 데이터를 캐시에 저장
        
        Args:
            airline_code: 항공사 코드
            reviews: 리뷰 목록
            ttl_hours: 캐시 유효 시간 (시간 단위, 기본값: 24시간)
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            now = datetime.utcnow()
            expires_at = (now.timestamp() + ttl_hours * 3600)
            expires_iso = datetime.fromtimestamp(expires_at).isoformat()
            
            # 기존 캐시 삭제
            cursor.execute("""
                DELETE FROM reviews_cache WHERE airline_code = ?
            """, (airline_code,))
            
            # 새 캐시 저장
            for review in reviews:
                review_id = review.get("id", "")
                cursor.execute("""
                    INSERT INTO reviews_cache (id, airline_code, data, cached_at, expires_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    review_id,
                    airline_code,
                    json.dumps(review),
                    now.isoformat(),
                    expires_iso
                ))
            
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise DatabaseError(message=f"리뷰 캐시 저장 실패: {e}")
        finally:
            conn.close()
    
    def get_cached_reviews(self, airline_code: str) -> Optional[List[Dict[str, Any]]]:
        """
        캐시된 리뷰 조회
        
        Args:
            airline_code: 항공사 코드
            
        Returns:
            리뷰 목록 또는 None (캐시 없음/만료)
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            now = datetime.utcnow().isoformat()
            cursor.execute("""
                SELECT data FROM reviews_cache 
                WHERE airline_code = ? AND expires_at > ?
                ORDER BY cached_at DESC
            """, (airline_code, now))
            
            rows = cursor.fetchall()
            if not rows:
                return None
            
            reviews = []
            for row in rows:
                reviews.append(json.loads(row["data"]))
            
            return reviews
        except Exception as e:
            raise DatabaseError(message=f"리뷰 캐시 조회 실패: {e}")
        finally:
            conn.close()
    
    # ========== 시차적응 계획 관련 메서드 ==========
    
    def save_jetlag_plan(
        self, 
        user_id: str, 
        plan_key: str, 
        plan_data: Dict[str, Any],
        ttl_days: int = 30
    ) -> bool:
        """
        시차적응 계획을 로컬 DB에 저장
        
        Args:
            user_id: 사용자 ID
            plan_key: 계획 고유 키 (요청 파라미터 기반)
            plan_data: 계획 데이터
            ttl_days: 유효 기간 (일 단위)
            
        Returns:
            저장 성공 여부
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            now = datetime.utcnow()
            expires_at = (now.timestamp() + ttl_days * 24 * 3600)
            expires_iso = datetime.fromtimestamp(expires_at).isoformat()
            
            cursor.execute("""
                INSERT OR REPLACE INTO jetlag_plans 
                (id, user_id, plan_key, data, created_at, expires_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                f"{user_id}_{plan_key}",
                user_id,
                plan_key,
                json.dumps(plan_data),
                now.isoformat(),
                expires_iso
            ))
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            raise DatabaseError(message=f"시차적응 계획 저장 실패: {e}")
        finally:
            conn.close()
    
    def get_jetlag_plan(self, user_id: str, plan_key: str) -> Optional[Dict[str, Any]]:
        """
        시차적응 계획 조회
        
        Args:
            user_id: 사용자 ID
            plan_key: 계획 고유 키
            
        Returns:
            계획 데이터 또는 None
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            now = datetime.utcnow().isoformat()
            cursor.execute("""
                SELECT data FROM jetlag_plans 
                WHERE user_id = ? AND plan_key = ? AND expires_at > ?
            """, (user_id, plan_key, now))
            
            row = cursor.fetchone()
            if row:
                return json.loads(row["data"])
            return None
        except Exception as e:
            raise DatabaseError(message=f"시차적응 계획 조회 실패: {e}")
        finally:
            conn.close()
    
    # ========== 사용자 프로필 캐시 ==========
    
    def cache_user_profile(self, user_id: str, profile_data: Dict[str, Any], ttl_hours: int = 24):
        """
        사용자 프로필을 캐시에 저장
        
        Args:
            user_id: 사용자 ID
            profile_data: 프로필 데이터
            ttl_hours: 캐시 유효 시간 (시간 단위)
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            now = datetime.utcnow()
            expires_at = (now.timestamp() + ttl_hours * 3600)
            expires_iso = datetime.fromtimestamp(expires_at).isoformat()
            
            cursor.execute("""
                INSERT OR REPLACE INTO user_profiles 
                (user_id, data, cached_at, expires_at)
                VALUES (?, ?, ?, ?)
            """, (
                user_id,
                json.dumps(profile_data),
                now.isoformat(),
                expires_iso
            ))
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise DatabaseError(message=f"사용자 프로필 캐시 저장 실패: {e}")
        finally:
            conn.close()
    
    def get_cached_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        캐시된 사용자 프로필 조회
        
        Args:
            user_id: 사용자 ID
            
        Returns:
            프로필 데이터 또는 None
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            now = datetime.utcnow().isoformat()
            cursor.execute("""
                SELECT data FROM user_profiles 
                WHERE user_id = ? AND expires_at > ?
            """, (user_id, now))
            
            row = cursor.fetchone()
            if row:
                return json.loads(row["data"])
            return None
        except Exception as e:
            raise DatabaseError(message=f"사용자 프로필 캐시 조회 실패: {e}")
        finally:
            conn.close()
    
    # ========== 유틸리티 메서드 ==========
    
    def clear_expired_cache(self):
        """만료된 캐시 데이터 정리"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            now = datetime.utcnow().isoformat()
            
            # 만료된 리뷰 캐시 삭제
            cursor.execute("""
                DELETE FROM reviews_cache WHERE expires_at <= ?
            """, (now,))
            
            # 만료된 시차적응 계획 삭제
            cursor.execute("""
                DELETE FROM jetlag_plans WHERE expires_at <= ?
            """, (now,))
            
            # 만료된 사용자 프로필 캐시 삭제
            cursor.execute("""
                DELETE FROM user_profiles WHERE expires_at <= ?
            """, (now,))
            
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise DatabaseError(message=f"캐시 정리 실패: {e}")
        finally:
            conn.close()

