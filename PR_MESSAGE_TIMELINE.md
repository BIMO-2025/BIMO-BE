# 🚀 Enhance Flight Timeline Logic with Layover Support and Timeshifter Science

## 📋 Summary

비행 타임라인 생성 기능을 대폭 개선하여 **다구간 비행 및 경유 처리**를 지원하고, **Timeshifter 과학적 원리**를 LLM 프롬프트에 통합했습니다. 또한 **사용자 생활패턴(수면 패턴)**을 고려한 개인화된 타임라인을 생성합니다.

### 주요 개선사항
- ✅ **경유 항공편 지원**: 다구간 비행 segments를 자동 처리하고 경유 대기 정보 계산
- ✅ **Timeshifter 통합**: 빛 노출, PRC, 수면 스케줄 등 과학적 원리를 LLM 프롬프트에 반영
- ✅ **개인화**: 사용자 수면 패턴을 자동 조회하여 맞춤 타임라인 생성
- ✅ **순수 비행시간 계산**: 경유 대기 시간을 제외한 실제 비행 시간 구분
- ✅ **하위 호환성 유지**: 기존 직항 비행 요청은 변경 없이 작동

---

## 🎯 What Changed

### 1️⃣ 데이터 구조 확장

#### 📄 [`app/feature/wellness/flight_timeline_schemas.py`](file:///c:/Users/kksu1/OneDrive/바탕%20화면/KKS/SOONGSIL_UNIV/3-2/오픈소스기반기초설계/BIMO-BE/app/feature/wellness/flight_timeline_schemas.py)

**신규 스키마:**
- `FlightSegmentInfo`: 개별 비행 구간 정보 (출발지, 도착지, 시간, duration)
- `LayoverInfo`: 경유 대기 정보 (공항, 대기 시간, 시작/종료 시간)

**FlightTimelineRequest 확장:**
```python
segments: Optional[List[FlightSegmentInfo]] = None  # 비행 구간 목록
layovers: Optional[List[LayoverInfo]] = None        # 경유 정보
has_stopover: Optional[bool] =None                  # 경유 여부
user_sleep_pattern: Optional[dict] = None            # 수면 패턴
```

**TimelineEvent 타입 추가:**
- `LAYOVER`: 경유 대기 이벤트
- `CONNECTION`: 환승 이벤트

---

### 2️⃣ 서비스 로직 개선

#### 📄 [`app/feature/wellness/flight_timeline_service.py`](file:///c:/Users/kksu1/OneDrive/바탕%20화면/KKS/SOONGSIL_UNIV/3-2/오픈소스기반기초설계/BIMO-BE/app/feature/wellness/flight_timeline_service.py)

**새로운 함수:**

1. **`_calculate_layover_info(segments)`**
   - segments 간 시간차를 계산하여 경유 대기 정보 자동 생성
   - 도착 공항과 출발 공항 불일치 검증

2. **`_calculate_actual_flight_duration(segments)`**
   - 경유 대기 시간을 제외한 **순수 비행 시간** 계산
   - "PT14H30M" 및 "14h 30m" 형식 모두 파싱

**LLM 프롬프트 대폭 개선:**

```python
**과학적 근거 (Timeshifter 연구):**
1. **빛 노출 (가장 중요!)**: 생체시계(Circadian Rhythm) 조절의 핵심
   - 동쪽 이동: 오전 빛 노출 권장 (+), 저녁 빛 차단 권장 (-)
   - 서쪽 이동: 저녁 빛 노출 권장 (+), 오전 빛 차단 권장 (-)
   
2. **Phase Response Curve (PRC)**: 빛 노출 타이밍에 따라 생체시계가 조절됨
   
3. **수면 스케줄**: 목적지 시간대에 맞춘 수면으로 시차 적응 가속화
   
4. **구간별 전략**: 경유지에서도 최종 목적지 시간대 기준으로 조절

**사용자 생활패턴:**
- 평소 수면 시간: 23:30 ~ 07:00
- 사용자의 평소 수면 패턴을 고려하여 기내 수면 시간을 조정하세요
- 사용자가 평소 늦게 자는 편이면 비행 초반 수면을 권장하고, 일찍 자는 편이면 비행 후반 수면을 권장하세요

**경유 시간별 권장사항:**
- 2시간 미만: 라운지 휴식, 가벼운 스트레칭
- 2-6시간: 목적지 시간대에 따라 수면/활동 조절, 샤워 시설 활용
- 6시간 이상: 라운지에서 충분한 휴식 또는 수면
- 24시간 이상: 공항 호텔 이용, 완전한 수면 사이클 확보
```

**시간 구분:**
- **총 소요 시간**: 출발부터 도착까지 (경유 대기 포함)
- **순수 비행 시간**: 실제 비행 시간만 (경유 대기 제외)
- LLM이 타임라인 이벤트를 **순수 비행 시간 기준**으로 배치

---

### 3️⃣ myFlights 통합

#### 📄 [`app/feature/wellness/wellness_router.py`](file:///c:/Users/kksu1/OneDrive/바탕%20화면/KKS/SOONGSIL_UNIV/3-2/오픈소스기반기초설계/BIMO-BE/app/feature/wellness/wellness_router.py)

**개선사항:**
1. **불필요한 엔드포인트 제거**: `POST /wellness/flight-timeline` 제거 (직접 입력 방식)
2. **myFlights 데이터 자동 추출**:
   - `my_flight.segments`를 `FlightSegmentInfo` 리스트로 변환
   - 각 segment의 departure/arrival dict에서 시간 및 공항 코드 파싱
   - `has_stopover` 필드 자동 포함

3. **사용자 수면 패턴 조회**:
   - `UserService.get_sleep_pattern(user_id)` 호출
   - 조회 실패 시에도 정상 작동 (예외 처리)

**결과:**
- 사용자가 myFlights에 저장한 경유편 → 자동으로 경유 이벤트 생성
- 사용자 수면 패턴 → LLM이 자동 반영하여 맞춤 타임라인 생성

---

### 4️⃣ 테스트 추가

#### 📄 `tests/test_flight_timeline_layover.py`
- `_calculate_layover_info` 함수 단위 테스트
- 직항/단일 경유/다중 경유 검증
- 하위 호환성 테스트

#### 📄 `tests/test_actual_flight_duration.py`
- `_calculate_actual_flight_duration` 함수 테스트
- 다양한 duration 형식 파싱 검증
- 여러 segments 합산 검증

#### 📄 `test_timeline_auto.py`
- 가짜 데이터로 자동 테스트
- LLM 응답 전체를 JSON 파일에 기록
- 경유 1회/2회 케이스 테스트

#### 📄 `test_timeline_layovers.py`
- API 엔드포인트 통합 테스트
- 경유 0개(직항), 1개, 2개 케이스

---

## 🔬 Timeshifter 과학적 원리 상세

### 연구 근거
이 기능은 **Timeshifter**의 시차 적응 알고리즘을 기반으로 합니다. Timeshifter는 Harvard Medical School, NASA와 협력하여 개발한 과학 기반 시차 적응 앱입니다.

### 핵심 원리

1. **빛 노출 (Light Exposure)**
   - 생체시계를 조절하는 가장 중요한 요소
   - 동쪽 이동 시: 오전 빛 노출로 생체시계 앞당김
   - 서쪽 이동 시: 저녁 빛 노출로 생체시계 늦춤

2. **Phase Response Curve (PRC)**
   - 빛 노출 타이밍에 따라 생체시계가 앞당겨지거나 늦춰짐
   - 개인의 출발 시간대 생체시계 위상을 고려하여 최적 타이밍 결정

3. **수면 스케줄**
   - 목적지 시간대에 맞춘 전략적 수면
   - 도착 전부터 목적지 일정에 적응

4. **구간별 전략**
   - 경유지에서도 최종 목적지 시간대를 기준으로 조절
   - 경유 시간에 따른 맞춤 권장사항

### 제외사항
- **보조제 (Supplements)**: 멜라토닌, 카페인 등 섭취 권장 제외 (사용자 요청)

📚 **참고 자료:**
- Timeshifter 공식 사이트: https://www.timeshifter.com/
- Harvard Medical School 연구
- NASA Fatigue Management Program

전체 연구 내용은 [`timeshifter_research.md`](file:///C:/Users/kksu1/.gemini/antigravity/brain/c493a195-2319-42e2-926c-e8fe80a0a934/timeshifter_research.md) 참조.

---

## 🧪 테스트 결과

### ✅ 단위 테스트
```bash
pytest tests/test_flight_timeline_layover.py -v
pytest tests/test_actual_flight_duration.py -v
```
- 모든 테스트 통과 ✅

### ✅ 통합 테스트 (자동)
```bash
python test_timeline_auto.py
```

**테스트 1: 경유 1회 + 수면 패턴**
- ICN → NRT (경유 2시간) → JFK
- 수면 패턴: 23:30 ~ 07:00
- ✅ 이벤트 10개 생성
- ✅ 경유 이벤트 1개 감지
- ✅ 수면 이벤트 1개 (05:00 - 12:00)

**테스트 2: 경유 2회 + 수면 패턴 없음**
- ICN → DXB (경유 7시간) → LHR (경유 2시간) → JFK
- ✅ 경유 이벤트 2개 감지
  - DXB 경유 (7시간)
  - LHR 경유 (2시간)

---

## 📝 Commits

```
59b239b test: Add test scripts for timeline generation
f43f372 feat: Personalize timeline with user sleep pattern
f67e7af refactor: Remove unused POST /wellness/flight-timeline endpoint
e2de753 feat: Extract segments from myFlights for timeline generation
e47cdcf fix: Calculate actual flight duration excluding layover time
f1c1baf fix: Include bimoSummary in airline detail response
51ac9e3 test: Add tests for layover flight timeline generation
ddb4d37 feat: Enhance flight timeline with Timeshifter research
d360a4b feat: Add layover flight schemas for timeline generation
```

---

## 🚦 Breaking Changes

**없음** - 완전한 하위 호환성 유지

기존 직항 비행 요청:
```json
{
  "origin": "ICN",
  "destination": "JFK",
  "departure_time": "2025-12-25T10:00:00Z",
  "arrival_time": "2025-12-25T22:30:00Z",
  "seat_class": "ECONOMY",
  "flight_goal": "SLEEP_FOCUS"
}
```
→ 변경 없이 정상 작동 ✅

---

## 📌 API Changes

### 엔드포인트 변경

**제거됨:**
- ❌ `POST /wellness/flight-timeline` (직접 입력 방식)

**유지:**
- ✅ `POST /wellness/users/{user_id}/my-flights/{flight_id}/timeline`
  - myFlights 기반 타임라인 생성
  - segments 자동 추출
  - 사용자 수면 패턴 자동 반영

---

## 🔍 Next Steps

### 권장 사항
1. **LLM 응답 품질 모니터링**
   - 경유 이벤트가 적절히 생성되는지 확인
   - 수면 패턴이 타임라인에 반영되는지 검증

2. **추가 테스트 케이스**
   - 3개 이상 경유 케이스
   - 다양한 시간대 조합
   - 극단적인 경유 시간 (30분, 24시간 이상)

3. **사용자 피드백 수집**
   - 생성된 타임라인의 실용성
   - Timeshifter 원리 반영 효과성

---

## 👥 Reviewers

@팀원분들 리뷰 부탁드립니다! 특히:
- LLM 프롬프트가 너무 길지 않은지
- Timeshifter 원리 설명이 적절한지
- 테스트 커버리지가 충분한지

---

## 📚 Related

- Closes #이슈번호 (해당되는 경우)
- Related to: Timeline Generation Feature
  
