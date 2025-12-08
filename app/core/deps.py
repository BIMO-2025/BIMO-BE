from typing import Any
from fastapi import Request, Depends
from app.core.config import get_settings, Settings
# from app.core.network_monitor import NetworkMonitor # Circular import 방지를 위해 TYPE_CHECKING 사용 권장하지만, 일단 간단하게

# 순환 참조 방지를 위해 여기서는 TYPE_CHECKING을 사용하지 않고, 
# 실제 객체는 request.app.state에서 가져오므로 타입 힌트는 'Any'나 문자열로 처리하거나
# 필요한 곳에서 import하도록 합니다. 하지만 편의상 NetworkMonitor는 import가 필요할 수 있습니다.
# 구조상 NetworkMonitor가 deps를 import하지는 않을 것이므로 import 해도 됩니다.

def get_network_monitor(request: Request) -> Any:
    """
    App state에서 NetworkMonitor 인스턴스를 가져옵니다.
    반환 타입은 NetworkMonitor여야 하지만, 순환 참조 방지를 위해 Any로 둡니다.
    """
    return request.app.state.network_monitor

def get_offline_service(request: Request) -> Any:
    """
    App state에서 OfflineService 인스턴스를 가져옵니다.
    """
    return request.app.state.offline_service
