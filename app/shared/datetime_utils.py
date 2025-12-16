"""
날짜/시간 관련 공통 유틸리티 함수
프로젝트 전반에서 반복되는 날짜/시간 파싱 로직을 중앙화
"""

from datetime import datetime
from typing import Union


def parse_iso_datetime(dt_input: Union[str, datetime]) -> datetime:
    """
    ISO 8601 형식의 문자열 또는 datetime 객체를 datetime으로 변환합니다.
    
    Args:
        dt_input: ISO 8601 문자열 (예: "2024-12-16T10:30:00Z") 또는 datetime 객체
        
    Returns:
        datetime 객체 (timezone-aware)
        
    Examples:
        >>> parse_iso_datetime("2024-12-16T10:30:00Z")
        datetime.datetime(2024, 12, 16, 10, 30, tzinfo=datetime.timezone.utc)
        
        >>> parse_iso_datetime(datetime(2024, 12, 16, 10, 30))
        datetime.datetime(2024, 12, 16, 10, 30)
    """
    if isinstance(dt_input, datetime):
        return dt_input
    
    if isinstance(dt_input, str):
        # "Z"를 "+00:00"으로 변환하여 timezone 인식
        normalized = dt_input.replace("Z", "+00:00")
        return datetime.fromisoformat(normalized)
    
    raise TypeError(f"Expected str or datetime, got {type(dt_input)}")


def parse_iso_duration(iso_duration: str) -> str:
    """
    ISO 8601 duration 형식(PT14H30M)을 간단한 HMM 형식(14H30M)으로 변환합니다.
    
    Args:
        iso_duration: ISO 8601 duration 문자열 (예: "PT14H30M", "PT2H", "PT45M")
        
    Returns:
        "HMM" 형식의 문자열 (예: "14H30M", "2H", "45M")
        빈 문자열이거나 None인 경우 "0M" 반환
        
    Examples:
        >>> parse_iso_duration("PT14H30M")
        "14H30M"
        
        >>> parse_iso_duration("PT2H")
        "2H"
        
        >>> parse_iso_duration("PT45M")
        "45M"
        
        >>> parse_iso_duration("")
        "0M"
    """
    if not iso_duration:
        return "0M"
    
    # "PT" prefix 제거
    duration_str = iso_duration.replace("PT", "")
    
    hours = 0
    minutes = 0
    
    # 시간(H) 추출
    if "H" in duration_str:
        try:
            hours_part = duration_str.split("H")[0]
            hours = int(hours_part)
        except (ValueError, IndexError):
            pass
    
    # 분(M) 추출
    if "M" in duration_str:
        try:
            # H 이후의 M 값 추출
            if "H" in duration_str:
                minutes_part = duration_str.split("H")[-1].split("M")[0]
            else:
                minutes_part = duration_str.split("M")[0]
            minutes = int(minutes_part)
        except (ValueError, IndexError):
            pass
    
    # 결과 포맷팅
    if hours > 0 and minutes > 0:
        return f"{hours}H{minutes}M"
    elif hours > 0:
        return f"{hours}H"
    elif minutes > 0:
        return f"{minutes}M"
    else:
        return "0M"


def parse_duration_seconds(seconds: int) -> str:
    """
    초 단위 duration을 HMM 형식으로 변환합니다.
    
    Args:
        seconds: 초 단위 시간
        
    Returns:
        "HMM" 형식의 문자열 (예: "14H30M", "45M")
        
    Examples:
        >>> parse_duration_seconds(52200)  # 14시간 30분
        "14H30M"
        
        >>> parse_duration_seconds(2700)  # 45분
        "45M"
        
        >>> parse_duration_seconds(0)
        "0M"
    """
    if not seconds or seconds <= 0:
        return "0M"
    
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    
    if hours > 0 and minutes > 0:
        return f"{hours}H{minutes}M"
    elif hours > 0:
        return f"{hours}H"
    elif minutes > 0:
        return f"{minutes}M"
    else:
        return "0M"
