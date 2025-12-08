"""
오프라인 데이터 캐싱 서비스
온라인 상태에서 조회한 데이터를 로컬에 캐시하고, 오프라인에서 사용합니다.
"""

from typing import Optional, List, Dict, Any, Callable
from datetime import datetime, timedelta

from app.feature.offline.local_db import LocalDatabase
from app.core.network_monitor import NetworkMonitor, get_network_monitor
from app.core.exceptions.exceptions import DatabaseError


class CacheService:
    """오프라인 캐싱 서비스 클래스"""
    
    def __init__(self, local_db: Optional[LocalDatabase] = None):
        """
        캐싱 서비스 초기화
        
        Args:
            local_db: 로컬 데이터베이스 인스턴스
        """
        self.local_db = local_db or LocalDatabase()
        self.network_monitor = get_network_monitor()
    
    async def get_or_fetch(
        self,
        cache_key: str,
        fetch_func: Callable,
        cache_ttl_hours: int = 24,
        force_refresh: bool = False
    ) -> Any:
        """
        캐시에서 조회하거나, 없으면 fetch_func을 호출하여 가져온 후 캐시에 저장
        
        Args:
            cache_key: 캐시 키
            fetch_func: 데이터를 가져올 함수 (비동기)
            cache_ttl_hours: 캐시 유효 시간 (시간 단위)
            force_refresh: 강제 새로고침 여부
            
        Returns:
            데이터
        """
        # 강제 새로고침이 아니고 오프라인 상태면 캐시에서 조회
        if not force_refresh and self.network_monitor.is_offline:
            cached_data = self._get_from_cache(cache_key)
            if cached_data:
                return cached_data
            # 캐시에 없으면 오프라인 상태임을 알림
            raise DatabaseError(
                message="오프라인 상태에서 데이터를 찾을 수 없습니다. 네트워크 연결을 확인해주세요."
            )
        
        # 온라인 상태이거나 강제 새로고침인 경우
        if self.network_monitor.is_online or force_refresh:
            try:
                # 실제 데이터 가져오기
                data = await fetch_func()
                
                # 캐시에 저장
                self._save_to_cache(cache_key, data, cache_ttl_hours)
                
                return data
            except Exception as e:
                # 온라인 상태에서 가져오기 실패 시, 캐시에서 조회 시도
                if not force_refresh:
                    cached_data = self._get_from_cache(cache_key)
                    if cached_data:
                        return cached_data
                raise
        
        # 네트워크 상태를 알 수 없는 경우
        # 먼저 캐시에서 조회 시도
        cached_data = self._get_from_cache(cache_key)
        if cached_data:
            return cached_data
        
        # 캐시에 없으면 온라인 상태로 가정하고 시도
        try:
            data = await fetch_func()
            self._save_to_cache(cache_key, data, cache_ttl_hours)
            return data
        except Exception:
            # 실패 시 오프라인 상태로 간주
            raise DatabaseError(
                message="네트워크 연결을 확인할 수 없습니다. 오프라인 모드로 전환되었습니다."
            )
    
    def _get_from_cache(self, cache_key: str) -> Optional[Any]:
        """
        캐시에서 데이터 조회
        
        Args:
            cache_key: 캐시 키
            
        Returns:
            캐시된 데이터 또는 None
        """
        # cache_key 형식: "collection:key" (예: "reviews:KE", "jetlag_plan:user123:key456")
        parts = cache_key.split(":", 1)
        if len(parts) != 2:
            return None
        
        cache_type = parts[0]
        key = parts[1]
        
        try:
            if cache_type == "reviews":
                # 리뷰 캐시 조회
                return self.local_db.get_cached_reviews(key)
            elif cache_type == "jetlag_plan":
                # 시차적응 계획 캐시 조회
                # key 형식: "user_id:plan_key"
                user_id, plan_key = key.split(":", 1)
                return self.local_db.get_jetlag_plan(user_id, plan_key)
            elif cache_type == "user_profile":
                # 사용자 프로필 캐시 조회
                return self.local_db.get_cached_user_profile(key)
            else:
                return None
        except Exception:
            return None
    
    def _save_to_cache(self, cache_key: str, data: Any, ttl_hours: int):
        """
        데이터를 캐시에 저장
        
        Args:
            cache_key: 캐시 키
            data: 저장할 데이터
            ttl_hours: 캐시 유효 시간
        """
        parts = cache_key.split(":", 1)
        if len(parts) != 2:
            return
        
        cache_type = parts[0]
        key = parts[1]
        
        try:
            if cache_type == "reviews":
                # 리뷰 캐시 저장
                if isinstance(data, list):
                    self.local_db.cache_reviews(key, data, ttl_hours)
            elif cache_type == "jetlag_plan":
                # 시차적응 계획 캐시 저장
                # key 형식: "user_id:plan_key"
                user_id, plan_key = key.split(":", 1)
                if isinstance(data, dict):
                    self.local_db.save_jetlag_plan(user_id, plan_key, data, ttl_days=ttl_hours // 24)
            elif cache_type == "user_profile":
                # 사용자 프로필 캐시 저장
                if isinstance(data, dict):
                    self.local_db.cache_user_profile(key, data, ttl_hours)
        except Exception as e:
            # 캐시 저장 실패는 무시 (주요 기능에 영향 없음)
            print(f"캐시 저장 실패: {e}")
    
    def invalidate_cache(self, cache_key: str):
        """
        특정 캐시 무효화
        
        Args:
            cache_key: 캐시 키
        """
        # 구현: 해당 캐시 항목 삭제
        # 현재는 TTL 기반으로 자동 만료되므로 별도 구현 불필요
        pass
    
    def clear_all_cache(self):
        """모든 캐시 삭제"""
        self.local_db.clear_expired_cache()


# 전역 캐시 서비스 인스턴스
_cache_service: Optional[CacheService] = None


def get_cache_service() -> CacheService:
    """
    전역 캐시 서비스 인스턴스 반환
    
    Returns:
        CacheService 인스턴스
    """
    global _cache_service
    if _cache_service is None:
        _cache_service = CacheService()
    return _cache_service

