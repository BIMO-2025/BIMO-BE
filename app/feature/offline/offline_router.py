"""
오프라인 기능 API 라우터
동기화 상태 조회 및 수동 동기화 기능을 제공합니다.
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any

from app.core.offline import get_offline_service
from app.core.exceptions.exceptions import CustomException

router = APIRouter(prefix="/offline", tags=["offline"])


@router.get("/status")
async def get_sync_status() -> Dict[str, Any]:
    """
    동기화 상태 조회
    
    Returns:
        {
            "network_status": "online" | "offline" | "unknown",
            "is_online": bool,
            "queue_stats": {
                "pending": int,
                "processing": int,
                "completed": int,
                "failed": int,
                "total": int
            },
            "pending_count": int,
            "processing_count": int,
            "completed_count": int,
            "failed_count": int
        }
    """
    try:
        offline_service = get_offline_service()
        status = offline_service.get_sync_status()
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"상태 조회 실패: {str(e)}")


@router.post("/sync")
async def sync_now() -> Dict[str, Any]:
    """
    수동 동기화 실행
    대기 중인 모든 큐 항목을 동기화합니다.
    
    Returns:
        {
            "status": "success" | "already_syncing" | "offline",
            "total": int,
            "success": int,
            "failed": int
        }
    """
    try:
        offline_service = get_offline_service()
        result = await offline_service.sync_now()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"동기화 실패: {str(e)}")

