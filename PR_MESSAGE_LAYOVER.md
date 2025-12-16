# ✈️ Layover Flight Timeline Generation with Timeshifter Research

## 📌 Summary

경유 항공편의 구간별 정보와 경유 대기 시간을 고려한 타임라인 생성 기능을 추가했습니다. Harvard Medical School의 Timeshifter 연구를 기반으로 과학적 근거가 포함된 시차 적응 권장사항을 제공합니다.

## 🎯 Changes

### 1. 스키마 확장 ([`flight_timeline_schemas.py`](https://github.com/YOUR_REPO/blob/feat/layover-flight-timeline/app/feature/wellness/flight_timeline_schemas.py))

#### 새로운 스키마 추가

**`FlightSegmentInfo`** - 비행 구간 정보
```python
class FlightSegmentInfo(BaseModel):
    origin: str              # 구간 출발 공항 (예: ICN)
    destination: str         # 구간 도착 공항 (예: NRT)
    departure_time: datetime
    arrival_time: datetime
    duration: str           # 구간 비행 시간 (예: "3h 30m")
```

**`LayoverInfo`** - 경유 대기 정보
```python
class LayoverInfo(BaseModel):
    airport: str            # 경유 공항 코드
    duration_hours: float   # 대기 시간 (시간 단위)
    start_time: datetime    # 경유 시작 (도착 시간)
    end_time: datetime      # 경유 종료 (다음 출발 시간)
```

#### `FlightTimelineRequest` 확장
```python
# 기존 필드 유지 (하위 호환성)
segments: Optional[List[FlightSegmentInfo]] = None
layovers: Optional[List[LayoverInfo]] = None
has_stopover: Optional[bool] = None
```

#### `TimelineEvent` 타입 추가
- 기존: `TAKEOFF, MEAL, SLEEP, WORK, ENTERTAINMENT, FREE_TIME, LANDING`
- **추가**: `LAYOVER, CONNECTION`

---

### 2. 경유 정보 자동 처리 로직 ([`flight_timeline_service.py`](https://github.com/YOUR_REPO/blob/feat/layover-flight-timeline/app/feature/wellness/flight_timeline_service.py))

#### `_calculate_layover_info` 함수
```python
def _calculate_layover_info(segments: List[FlightSegmentInfo]) -> List[LayoverInfo]:
    """구간 정보로부터 경유 대기 정보 자동 계산"""
```

**동작 방식:**
1. `segments`가 제공되면 각 구간 사이의 시간차를 계산
2. 현재 구간 도착 시간 ~ 다음 구간 출발 시간 = 경유 대기 시간
3. `LayoverInfo` 객체 자동 생성

**예시:**
- 구간 1: ICN → NRT (10:00 → 13:30)
- 구간 2: NRT → JFK (15:30 → 02:30)
- **계산된 경유**: NRT에서 2시간 대기 (13:30 ~ 15:30)

---

### 3. Timeshifter 과학적 근거 반영

Harvard Medical School과 Dr. Steven Lockley의 연구를 기반으로 한 시차 적응 전략을 LLM 프롬프트에 포함했습니다.

#### 🌞 빛 노출 (Light Exposure) - 가장 핵심적인 요소

**과학적 원리:**
- 빛은 생체시계(Circadian Rhythm)를 조절하는 **가장 강력한 신호**입니다
- 시상하부의 시교차상핵(SCN)이 빛 신호를 받아 생체시계를 조정합니다
- 올바른 타이밍의 빛 노출로 생체시계를 앞당기거나 늦출 수 있습니다

**이동 방향별 전략:**

| 이동 방향 | 빛 노출 시간 | 빛 차단 시간 | 목적 |
|----------|-------------|-------------|------|
| **동쪽 이동** (예: 한국→미국 동부) | 오전 (아침 햇빛) | 오후/저녁 | 생체시계 앞당김 |
| **서쪽 이동** (예: 미국→한국) | 저녁 (늦은 햇빛) | 오전 | 생체시계 늦춤 |

**프롬프트 적용:**
```
동쪽 이동: 오전 빛 노출 권장 (+), 저녁 빛 차단 권장 (-)
서쪽 이동: 저녁 빛 노출 권장 (+), 오전 빛 차단 권장 (-)
```

#### 📊 Phase Response Curve (PRC)

**과학적 원리:**
- PRC는 하루 24시간 주기 중 특정 시점에 빛을 받으면 생체시계가 어떻게 변화하는지 나타내는 곡선입니다
- **생체 시간** (내부 시계)과 **실제 시간** (외부 환경)의 관계를 설명합니다

**PRC의 핵심 구간:**
1. **지연 구간 (Delay Zone)**: 저녁~자정 전 빛 노출 → 생체시계가 늦춰짐 (서쪽 이동에 유리)
2. **전진 구간 (Advance Zone)**: 자정 후~아침 빛 노출 → 생체시계가 앞당겨짐 (동쪽 이동에 유리)
3. **무영향 구간 (Dead Zone)**: 한낮 빛 노출 → 생체시계 변화 거의 없음

**Timeshifter의 혁신:**
- 개인의 현재 생체시계 위상을 추정
- PRC를 기반으로 **정확한 타이밍**에 빛 노출/차단 지시
- 잘못된 타이밍의 빛 노출은 오히려 시차증을 악화시킬 수 있음

**프롬프트 적용:**
```
빛 노출 타이밍에 따라 생체시계가 앞당겨지거나 늦춰짐
→ LLM이 목적지 시간대를 고려하여 적절한 빛 노출 시간을 권장
```

#### 😴 수면 스케줄 (Sleep Schedule)

**과학적 원리:**
- 수면-각성 주기는 생체시계의 가장 명확한 출력 신호입니다
- 목적지 시간대에 맞춘 수면은 시차 적응을 가속화합니다
- **앵커 수면 (Anchor Sleep)**: 시차 적응 중에도 일정 시간 수면을 유지하여 생체리듬 안정화

**Timeshifter 전략:**
1. **출발 전**: 점진적으로 수면 시간 조정 (1-2일 전부터)
2. **비행 중**: 목적지 야간 시간에 수면 시도
3. **도착 후**: 현지 수면 시간 엄격히 준수

**프롬프트 적용:**
```
목적지 시간대에 맞춘 수면으로 시차 적응 가속화
→ LLM이 비행 중 수면 타이밍을 목적지 야간 시간에 맞춤
```

#### 🧭 구간별 전략

**경유지에서의 핵심 원칙:**
- 경유지 현지 시간이 아닌 **최종 목적지 시간대**를 기준으로 조절
- 경유 시간이 길어도 일관된 전략 유지

**예시: ICN → NRT(경유 2시간) → JFK**
- NRT는 단순 환승지일 뿐
- 전체 여정을 **ICN → JFK (미국 동부 시간)** 기준으로 빛/수면 조절
- 경유 중에도 JFK 시간대를 염두에 둔 활동 권장

**프롬프트 적용:**
```
경유지에서도 최종 목적지 시간대 기준으로 조절
→ LLM이 경유 중 활동을 최종 목적지 기준으로 제안
```

---

### 4. 경유 시간별 맞춤 권장사항

Timeshifter 연구와 항공 건강 가이드라인을 종합하여 경유 대기 시간별로 구체적인 권장사항을 프롬프트에 포함했습니다.

#### 📋 경유 시간별 전략표

| 경유 시간 | 권장 활동 | 과학적 근거 |
|----------|---------|-----------|
| **2시간 미만** | 라운지 휴식, 가벼운 스트레칭 | 짧은 시간이므로 이동/환승에 집중 |
| **2-6시간** | 목적지 시간대에 따라 수면/활동 조절, 샤워 활용 | PRC 기반 빛 노출 전략 적용 가능 시간 |
| **6시간 이상** | 공항 호텔/수면실 이용, 본격적인 휴식 | 앵커 수면으로 생체리듬 안정화 |
| **24시간 이상 (스톱오버)** | 현지 활동, 야외 햇빛 노출 | 시차 적응 본격 시작, 빛 노출 최대 활용 |

#### 🌟 프롬프트 구조

```python
**경유 시간별 권장사항:**
- 2시간 미만: 라운지 휴식, 가벼운 스트레칭
- 2-6시간: 목적지 시간대에 따라 수면/활동 조절, 샤워 시설 활용
- 6시간 이상: 공항 호텔 또는 수면실 이용, 본격적인 휴식
- 24시간 이상(스톱오버): 현지 활동, 야외 햇빛 노출로 시차 적응 시작
```

---

### 5. LLM 프롬프트 구조

#### 비행 정보 섹션
```
**비행 정보:**
- 출발지/도착지
- 출발/도착 시간
- 좌석 등급, 비행 목표
```

#### 구간/경유 정보 (segments 제공 시)
```
**비행 구간 정보:**
구간 1: ICN → NRT
- 출발: 2025-12-25 10:00
- 도착: 2025-12-25 13:30
- 비행 시간: 3h 30m

**경유 대기 정보:**
경유지 1: NRT
- 대기 시간: 2.0시간
- 13:30 ~ 15:30
```

#### 과학적 근거 섹션
```
**과학적 근거 (Timeshifter 연구):**
1. 빛 노출 (가장 중요!) - 생체시계 조절의 핵심
2. Phase Response Curve (PRC) - 타이밍의 중요성
3. 수면 스케줄 - 목적지 시간대 적응
4. 구간별 전략 - 최종 목적지 기준 조절
```

#### 권장사항 섹션
```
**경유 시간별 권장사항:**
- 2시간/6시간/24시간 기준 전략
```

---

### 6. 테스트 ([`test_flight_timeline_layover.py`](https://github.com/YOUR_REPO/blob/feat/layover-flight-timeline/tests/test_flight_timeline_layover.py))

#### 작성된 테스트

1. **`test_calculate_single_layover`**
   - 1회 경유 (ICN → NRT → JFK)
   - 경유 시간 자동 계산 검증

2. **`test_calculate_multiple_layovers`**
   - 2회 경유 (ICN → DXB → LHR → JFK)
   - 다중 경유 처리 검증

3. **`test_direct_flight_backward_compatibility`**
   - 직항 항공편 하위 호환성
   - 기존 API 정상 작동 확인

4. **`test_layover_flight_with_segments`**
   - 경유 항공편 통합 테스트
   - segments 제공 시 전체 플로우 검증

---

## 🔄 Backward Compatibility

✅ **완벽한 하위 호환성 유지**
- `segments`, `layovers`, `has_stopover` 모두 **Optional** 필드
- 기존 직항 항공편 요청은 수정 없이 작동
- 새로운 경유 기능은 opt-in 방식

---

## 💡 Usage Example

### 직항 항공편 (기존 방식)
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

### 경유 항공편 (신규 기능)
```json
{
  "origin": "ICN",
  "destination": "JFK",
  "departure_time": "2025-12-25T10:00:00Z",
  "arrival_time": "2025-12-26T02:30:00Z",
  "seat_class": "ECONOMY",
  "flight_goal": "SLEEP_FOCUS",
  "segments": [
    {
      "origin": "ICN",
      "destination": "NRT",
      "departure_time": "2025-12-25T10:00:00Z",
      "arrival_time": "2025-12-25T13:30:00Z",
      "duration": "3h 30m"
    },
    {
      "origin": "NRT",
      "destination": "JFK",
      "departure_time": "2025-12-25T15:30:00Z",
      "arrival_time": "2025-12-26T02:30:00Z",
      "duration": "11h 0m"
    }
  ]
}
```

**LLM이 생성하는 타임라인:**
- NRT 경유 2시간 동안의 활동 (라운지, 스트레칭)
- JFK(미국 동부) 시간대 기준 빛 노출 전략
- 구간별 맞춤 수면/활동 권장사항
- Timeshifter 연구 기반 과학적 설명

---

## 🧪 Testing

```bash
# 신규 테스트 실행
pytest tests/test_flight_timeline_layover.py -v

# 전체 타임라인 테스트
pytest tests/test_timeline*.py -v
```

---

## 📚 References

- [Timeshifter Research](https://www.timeshifter.com/science)
- Harvard Medical School - Dr. Steven Lockley
- Phase Response Curve (PRC) studies
- Circadian Rhythm and Jet Lag Management

---

## 🎯 Key Benefits

1. ✅ **과학적 근거 기반** - Harvard 연구를 바탕으로 한 신뢰성 있는 권장사항
2. ✅ **정확한 경유 처리** - 구간별 시간을 정확히 고려한 타임라인
3. ✅ **맞춤형 전략** - 경유 시간/이동 방향에 따른 세밀한 조정
4. ✅ **하위 호환성** - 기존 기능에 영향 없음
5. ✅ **확장 가능성** - 향후 더 복잡한 여정 지원 가능

---

## 📝 Commits

- `d29dadb` - feat: Add layover flight schemas for timeline generation
- `0146390` - feat: Enhance flight timeline with Timeshifter research
- `51ac9e3` - test: Add tests for layover flight timeline generation
