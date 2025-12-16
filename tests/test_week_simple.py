"""
주차 계산 로직 간단 테스트
"""
from datetime import datetime, timedelta, timezone

def get_week_date_range(year: int, month: int, week: int):
    """월요일~일요일 기준 주차 계산"""
    if week < 1:
        raise ValueError("week는 1 이상이어야 합니다.")
    
    # 해당 월의 1일
    first_day = datetime(year, month, 1, tzinfo=timezone.utc)
    
    # 1일의 요일 (0=월요일, 6=일요일)
    first_weekday = first_day.weekday()
    
    # 해당 월의 첫 월요일 찾기
    if first_weekday == 0:
        first_monday = first_day
    else:
        days_until_monday = (7 - first_weekday) % 7
        first_monday = first_day + timedelta(days=days_until_monday)
    
    # 요청한 주차의 월요일
    target_monday = first_monday + timedelta(weeks=week - 1)
    
    # 해당 주의 일요일
    target_sunday = target_monday + timedelta(days=6, hours=23, minutes=59, seconds=59)
    
    # 다음 달로 넘어가는지 확인
    if month == 12:
        next_month_first = datetime(year + 1, 1, 1, tzinfo=timezone.utc)
    else:
        next_month_first = datetime(year, month + 1, 1, tzinfo=timezone.utc)
    
    if target_sunday >= next_month_first:
        target_sunday = next_month_first - timedelta(seconds=1)
    
    return target_monday, target_sunday

print("=" * 70)
print("주차 계산 테스트 (월요일~일요일 기준)")
print("=" * 70)

# 2025년 12월 테스트
print("\n2025년 12월:")
print(f"12월 1일: {datetime(2025, 12, 1).strftime('%A')}")

for week in range(1, 6):
    try:
        start, end = get_week_date_range(2025, 12, week)
        weekday_names = ['월', '화', '수', '목', '금', '토', '일']
        start_wd = weekday_names[start.weekday()]
        end_wd = weekday_names[end.weekday()]
        
        print(f"\n{week}주차:")
        print(f"  시작: {start.strftime('%Y-%m-%d')} ({start_wd})")
        print(f"  종료: {end.strftime('%Y-%m-%d')} ({end_wd})")
        print(f"  ✅ 월요일~일요일" if start.weekday() == 0 else f"  ⚠️  월요일로 시작하지 않음")
    except:
        break

# 현재 주차 확인
print("\n" + "=" * 70)
now = datetime.now(timezone.utc)
print(f"현재 날짜: {now.strftime('%Y-%m-%d (%A)')}")

# 현재가 어느 주차인지 계산
first_monday = datetime(now.year, now.month, 1, tzinfo=timezone.utc)
first_weekday = first_monday.weekday()
if first_weekday != 0:
    first_monday = first_monday + timedelta(days=(7 - first_weekday) % 7)

current_week = ((now - first_monday).days // 7) + 1
if current_week >= 1:
    print(f"현재 주차: {now.year}년 {now.month}월 {current_week}주차")
    start, end = get_week_date_range(now.year, now.month, current_week)
    print(f"주차 기간: {start.strftime('%m/%d')} ~ {end.strftime('%m/%d')}")
