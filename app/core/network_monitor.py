"""
네트워크 상태 감지 모듈
Firebase 연결 상태를 모니터링하여 온라인/오프라인 상태를 감지합니다.
"""

import asyncio
from typing import Optional, Callable
from enum import Enum
import httpx

from app.core.firebase import db
from app.core.exceptions.exceptions import CustomException


class NetworkStatus(Enum):
    """네트워크 상태"""
    ONLINE = "online"
    OFFLINE = "offline"
    UNKNOWN = "unknown"


class NetworkMonitor:
    """네트워크 상태 모니터링 클래스"""
    
    def __init__(self):
        self._status: NetworkStatus = NetworkStatus.UNKNOWN
        self._listeners: list[Callable[[NetworkStatus], None]] = []
        self._check_interval: int = 30  # 초 단위
        self._monitoring: bool = False
        self._monitor_task: Optional[asyncio.Task] = None
    
    @property
    def status(self) -> NetworkStatus:
        """현재 네트워크 상태"""
        return self._status
    
    @property
    def is_online(self) -> bool:
        """온라인 상태 여부"""
        return self._status == NetworkStatus.ONLINE
    
    @property
    def is_offline(self) -> bool:
        """오프라인 상태 여부"""
        return self._status == NetworkStatus.OFFLINE
    
    def add_listener(self, callback: Callable[[NetworkStatus], None]):
        """
        네트워크 상태 변경 리스너 추가
        
        Args:
            callback: 상태 변경 시 호출될 콜백 함수
        """
        if callback not in self._listeners:
            self._listeners.append(callback)
    
    def remove_listener(self, callback: Callable[[NetworkStatus], None]):
        """
        네트워크 상태 변경 리스너 제거
        
        Args:
            callback: 제거할 콜백 함수
        """
        if callback in self._listeners:
            self._listeners.remove(callback)
    
    def _notify_listeners(self, new_status: NetworkStatus):
        """리스너들에게 상태 변경 알림"""
        for listener in self._listeners:
            try:
                listener(new_status)
            except Exception as e:
                # 리스너 오류는 무시하고 계속 진행
                print(f"네트워크 상태 리스너 오류: {e}")
    
    async def check_network_status(self) -> NetworkStatus:
        """
        네트워크 상태 확인
        
        Returns:
            현재 네트워크 상태
        """
        # 방법 1: Firebase 연결 상태 확인
        firebase_online = await self._check_firebase_connection()
        
        # 방법 2: 외부 API 헬스체크 (선택적)
        # 외부 API 체크는 느릴 수 있으므로 타임아웃 설정
        external_online = await self._check_external_connection()
        
        # 둘 중 하나라도 성공하면 온라인으로 간주
        if firebase_online or external_online:
            new_status = NetworkStatus.ONLINE
        else:
            new_status = NetworkStatus.OFFLINE
        
        # 상태 변경 시 리스너에게 알림
        if new_status != self._status:
            old_status = self._status
            self._status = new_status
            self._notify_listeners(new_status)
            print(f"네트워크 상태 변경: {old_status.value} -> {new_status.value}")
        
        return self._status
    
    async def _check_firebase_connection(self) -> bool:
        """
        Firebase 연결 상태 확인
        
        Returns:
            연결 성공 여부
        """
        try:
            # 간단한 Firestore 읽기 작업으로 연결 확인
            # 실제 데이터를 읽지 않고 메타데이터만 확인
            # 타임아웃: 5초
            await asyncio.wait_for(
                asyncio.to_thread(
                    lambda: list(db.collection("_health_check").limit(1).stream())
                ),
                timeout=5.0
            )
            return True
        except asyncio.TimeoutError:
            return False
        except Exception:
            # 네트워크 오류, 권한 오류 등은 모두 오프라인으로 간주
            return False
    
    async def _check_external_connection(self) -> bool:
        """
        외부 API 연결 확인 (Google DNS 등)
        
        Returns:
            연결 성공 여부
        """
        try:
            # Google DNS (8.8.8.8) 또는 Cloudflare DNS (1.1.1.1)로 연결 확인
            async with httpx.AsyncClient(timeout=3.0) as client:
                # 간단한 HTTP 요청으로 네트워크 연결 확인
                response = await client.get("https://www.google.com", follow_redirects=True)
                return response.status_code < 500
        except Exception:
            return False
    
    async def start_monitoring(self, interval: int = 30):
        """
        네트워크 상태 모니터링 시작
        
        Args:
            interval: 상태 확인 간격 (초 단위, 기본값: 30초)
        """
        if self._monitoring:
            return
        
        self._check_interval = interval
        self._monitoring = True
        
        # 초기 상태 확인
        await self.check_network_status()
        
        # 주기적으로 상태 확인
        self._monitor_task = asyncio.create_task(self._monitor_loop())
        print(f"네트워크 모니터링 시작 (간격: {interval}초)")
    
    async def stop_monitoring(self):
        """네트워크 상태 모니터링 중지"""
        self._monitoring = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        print("네트워크 모니터링 중지")
    

    async def _monitor_loop(self):
        """모니터링 루프"""
        while self._monitoring:
            try:
                await asyncio.sleep(self._check_interval)
                if self._monitoring:
                    await self.check_network_status()
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"네트워크 모니터링 오류: {e}")
                # 오류 발생 시 오프라인으로 간주
                if self._status != NetworkStatus.OFFLINE:
                    self._status = NetworkStatus.OFFLINE
                    self._notify_listeners(NetworkStatus.OFFLINE)


# Exports만 유지
__all__ = ["NetworkMonitor", "NetworkStatus"]
