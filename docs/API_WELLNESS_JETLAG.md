# ✈️ Wellness 시차적응 계획 API 문서

프론트엔드 개발자를 위한 Wellness 시차적응(제트랙) 계획 생성 API 스키마 가이드입니다.

---

## 📋 목차

1. [기본 정보](#기본-정보)
2. [시차적응 계획 API](#시차적응-계획-api)
3. [스키마 정의](#스키마-정의)
4. [에러 응답](#에러-응답)
5. [사용 예시](#사용-예시)

---

## 🔧 기본 정보

### 공통 설정

- **Base URL**: API 서버 URL (예: `http://localhost:8000`)
- **Content-Type**: `application/json`
- **LLM 모델**: Google Gemini (기본값: `gemini-1.5-flash`)
- **환경 변수**: `GEMINI_API_KEY` 필요 (`.env` 파일에 설정)

### 기능 설명

LLM을 사용하여 사용자의 출발 시간, 도착 시간, 경유지, 도착지 시간대 등을 고려하여 최적의 피로도 관리를 위한 시차적응 계획을 생성합니다.

---

## ✈️ 시차적응 계획 API

### 기본 정보

- **엔드포인트**: `POST /wellness/jetlag-plan`
- **설명**: LLM을 사용하여 시차적응 계획을 생성합니다. 사용자의 출발 시간, 도착 시간, 경유지, 도착지 시간대 등을 고려하여 최적의 피로도 관리를 위한 시차적응 계획을 생성합니다.
- **인증**: 필요 없음 (추후 인증 추가 가능)

### 요청 스키마

```typescript
interface JetLagPlanRequest {
  flight_segments: FlightSegment[];            // 비행 구간 목록 (최소 1개, 필수)
  destination_timezone: string;                // 도착지 시간대 (필수, 예: "America/New_York")
  origin_timezone?: string;                    // 출발지 시간대 (선택, 예: "Asia/Seoul")
  user_sleep_pattern_start?: string;           // 사용자 평소 수면 시작 시간 (선택, HH:MM 형식)
  user_sleep_pattern_end?: string;             // 사용자 평소 수면 종료 시간 (선택, HH:MM 형식)
  trip_duration_days?: number;                 // 여행 기간 (선택, 기본값: 7일, 최소: 1일)
}

interface FlightSegment {
  departure_airport: string;                   // 출발 공항 코드 (예: ICN)
  arrival_airport: string;                     // 도착 공항 코드 (예: JFK)
  departure_time: string;                      // 출발 시간 (ISO 8601 형식)
  arrival_time: string;                        // 도착 시간 (ISO 8601 형식)
  flight_duration_hours?: number;              // 비행 시간 (시간 단위, 선택)
}
```

### 요청 예시

```json
{
  "flight_segments": [
    {
      "departure_airport": "ICN",
      "arrival_airport": "JFK",
      "departure_time": "2025-12-25T13:45:00Z",
      "arrival_time": "2025-12-25T18:20:00Z",
      "flight_duration_hours": 14.5
    }
  ],
  "destination_timezone": "America/New_York",
  "origin_timezone": "Asia/Seoul",
  "user_sleep_pattern_start": "23:00",
  "user_sleep_pattern_end": "07:00",
  "trip_duration_days": 7
}
```

### 응답 스키마

```typescript
interface JetLagPlanResponse {
  origin_timezone: string;                     // 출발지 시간대
  destination_timezone: string;                // 도착지 시간대
  time_difference_hours: number;               // 시차 (시간 단위)
  total_flight_duration_hours: number;         // 총 비행 시간 (시간 단위)
  daily_schedules: DailySchedule[];            // 일별 일정
  general_recommendations: string[];           // 일반적인 권장사항
  pre_flight_tips: string[];                   // 출발 전 팁
  post_arrival_tips: string[];                 // 도착 후 팁
  algorithm_explanation: string;               // LLM이 생성한 알고리즘 설명
}

interface DailySchedule {
  date: string;                                // 날짜 (YYYY-MM-DD)
  day_number: number;                          // 여행 시작일 기준 일수 (0부터 시작)
  local_timezone: string;                      // 현재 위치의 시간대
  sleep_window: string;                        // 권장 수면 시간대 (예: "22:00 - 06:00")
  meal_times: string[];                        // 권장 식사 시간 (HH:MM 형식)
  activities: string[];                        // 권장 활동 목록
  notes: string;                               // 특별 주의사항
}
```

### 응답 예시

```json
{
  "origin_timezone": "Asia/Seoul",
  "destination_timezone": "America/New_York",
  "time_difference_hours": -14,
  "total_flight_duration_hours": 14.5,
  "daily_schedules": [
    {
      "date": "2025-12-25",
      "day_number": 0,
      "local_timezone": "America/New_York",
      "sleep_window": "22:00 - 06:00",
      "meal_times": ["08:00", "13:00", "19:00"],
      "activities": ["가벼운 산책", "햇빛 쬐기"],
      "notes": "도착 첫날이므로 과도한 활동을 피하고 충분한 휴식을 취하세요."
    },
    {
      "date": "2025-12-26",
      "day_number": 1,
      "local_timezone": "America/New_York",
      "sleep_window": "22:00 - 06:00",
      "meal_times": ["08:00", "13:00", "19:00"],
      "activities": ["가벼운 운동", "자연광 노출"],
      "notes": "현지 시간에 맞춰 생활 패턴을 조정하세요."
    }
  ],
  "general_recommendations": [
    "도착지 시간대에 맞춰 즉시 현지 시간으로 생활하세요.",
    "도착 후 첫 3일은 충분한 수면을 취하세요.",
    "자연광을 충분히 쬐며 신체 리듬을 조정하세요."
  ],
  "pre_flight_tips": [
    "출발 전 며칠간 도착지 시간대에 맞춰 수면 패턴을 조정하세요.",
    "비행 전 충분한 수면을 취하세요."
  ],
  "post_arrival_tips": [
    "도착 후 즉시 현지 시간에 맞춰 식사와 활동을 시작하세요.",
    "낮잠은 20-30분 이내로 제한하세요."
  ],
  "algorithm_explanation": "이 계획은 시차적응(제트랙) 관리 전문 알고리즘에 기반하여 작성되었습니다. 출발 시간, 도착 시간, 경유지 정보를 모두 고려하여 최적의 수면 패턴과 활동 일정을 제안합니다..."
}
```

---

## 📝 스키마 정의

### FlightSegment

비행 구간 정보 스키마입니다.

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `departure_airport` | string | 필수 | 출발 공항 코드 (예: ICN) |
| `arrival_airport` | string | 필수 | 도착 공항 코드 (예: JFK) |
| `departure_time` | string | 필수 | 출발 시간 (ISO 8601) |
| `arrival_time` | string | 필수 | 도착 시간 (ISO 8601) |
| `flight_duration_hours` | number | 선택 | 비행 시간 (시간 단위) |

### JetLagPlanRequest

시차적응 계획 요청 스키마입니다.

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `flight_segments` | FlightSegment[] | 필수 | 비행 구간 목록 (최소 1개) |
| `destination_timezone` | string | 필수 | 도착지 시간대 (예: America/New_York) |
| `origin_timezone` | string | 선택 | 출발지 시간대 (예: Asia/Seoul) |
| `user_sleep_pattern_start` | string | 선택 | 사용자 평소 수면 시작 시간 (HH:MM 형식) |
| `user_sleep_pattern_end` | string | 선택 | 사용자 평소 수면 종료 시간 (HH:MM 형식) |
| `trip_duration_days` | number | 선택 | 여행 기간 (일 단위, 기본값: 7, 최소: 1) |

### DailySchedule

일별 일정 스키마입니다.

| 필드 | 타입 | 설명 |
|------|------|------|
| `date` | string | 날짜 (YYYY-MM-DD) |
| `day_number` | number | 여행 시작일 기준 일수 (0부터 시작) |
| `local_timezone` | string | 현재 위치의 시간대 |
| `sleep_window` | string | 권장 수면 시간대 (예: "22:00 - 06:00") |
| `meal_times` | string[] | 권장 식사 시간 (HH:MM 형식) |
| `activities` | string[] | 권장 활동 목록 |
| `notes` | string | 특별 주의사항 |

### JetLagPlanResponse

시차적응 계획 응답 스키마입니다.

| 필드 | 타입 | 설명 |
|------|------|------|
| `origin_timezone` | string | 출발지 시간대 |
| `destination_timezone` | string | 도착지 시간대 |
| `time_difference_hours` | number | 시차 (시간 단위) |
| `total_flight_duration_hours` | number | 총 비행 시간 (시간 단위) |
| `daily_schedules` | DailySchedule[] | 일별 일정 |
| `general_recommendations` | string[] | 일반적인 권장사항 |
| `pre_flight_tips` | string[] | 출발 전 팁 |
| `post_arrival_tips` | string[] | 도착 후 팁 |
| `algorithm_explanation` | string | LLM이 생성한 알고리즘 설명 |

---

## ⚠️ 에러 응답

모든 에러는 다음 형식으로 반환됩니다:

```typescript
interface ErrorResponse {
  detail: string;                              // 에러 메시지
  status_code: number;                         // HTTP 상태 코드
}
```

### 주요 에러 케이스

#### 1. Gemini API 오류 (502)

```json
{
  "detail": "Gemini 요청 중 오류가 발생했습니다: ...",
  "status_code": 502
}
```

**가능한 원인:**
- `GEMINI_API_KEY`가 설정되지 않았거나 잘못됨
- Gemini API 호출 제한 초과
- Gemini 서버 오류

#### 2. 빈 응답 오류 (502)

```json
{
  "detail": "Gemini 응답이 비어 있습니다.",
  "status_code": 502
}
```

#### 3. 잘못된 요청 (422)

```json
{
  "detail": [
    {
      "loc": ["body", "flight_segments"],
      "msg": "ensure this value has at least 1 items",
      "type": "value_error.list.min_items"
    }
  ],
  "status_code": 422
}
```

**가능한 원인:**
- 필수 필드 누락
- 잘못된 데이터 형식
- 유효성 검증 실패

#### 4. 시간대 오류 (422)

```json
{
  "detail": [
    {
      "loc": ["body", "destination_timezone"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ],
  "status_code": 422
}
```

#### 5. 설정 오류 (500)

```json
{
  "detail": "환경 변수 'GEMINI_API_KEY'가 설정되지 않았습니다. .env를 확인하세요.",
  "status_code": 500
}
```

---

## 💡 사용 예시

### React/TypeScript 예시

```typescript
// types.ts
interface JetLagPlanRequest {
  flight_segments: FlightSegment[];
  destination_timezone: string;
  origin_timezone?: string;
  user_sleep_pattern_start?: string;
  user_sleep_pattern_end?: string;
  trip_duration_days?: number;
}

interface FlightSegment {
  departure_airport: string;
  arrival_airport: string;
  departure_time: string;
  arrival_time: string;
  flight_duration_hours?: number;
}

interface JetLagPlanResponse {
  origin_timezone: string;
  destination_timezone: string;
  time_difference_hours: number;
  total_flight_duration_hours: number;
  daily_schedules: DailySchedule[];
  general_recommendations: string[];
  pre_flight_tips: string[];
  post_arrival_tips: string[];
  algorithm_explanation: string;
}

interface DailySchedule {
  date: string;
  day_number: number;
  local_timezone: string;
  sleep_window: string;
  meal_times: string[];
  activities: string[];
  notes: string;
}

// wellnessService.ts
const API_BASE_URL = "http://localhost:8000";

export const wellnessService = {
  async generateJetLagPlan(
    request: JetLagPlanRequest
  ): Promise<JetLagPlanResponse> {
    const response = await fetch(`${API_BASE_URL}/wellness/jetlag-plan`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "시차적응 계획 생성 실패");
    }

    return response.json();
  },
};

// 사용 예시
const handleGenerateJetLagPlan = async () => {
  try {
    const response = await wellnessService.generateJetLagPlan({
      flight_segments: [
        {
          departure_airport: "ICN",
          arrival_airport: "JFK",
          departure_time: "2025-12-25T13:45:00Z",
          arrival_time: "2025-12-25T18:20:00Z",
          flight_duration_hours: 14.5,
        },
      ],
      destination_timezone: "America/New_York",
      origin_timezone: "Asia/Seoul",
      user_sleep_pattern_start: "23:00",
      user_sleep_pattern_end: "07:00",
      trip_duration_days: 7,
    });

    console.log("시차적응 계획:", response);
    console.log("일별 일정:", response.daily_schedules);
    console.log("권장사항:", response.general_recommendations);
    console.log("출발 전 팁:", response.pre_flight_tips);
    console.log("도착 후 팁:", response.post_arrival_tips);
  } catch (error) {
    console.error("요청 실패:", error);
  }
};
```

### cURL 예시

```bash
curl -X POST "http://localhost:8000/wellness/jetlag-plan" \
  -H "Content-Type: application/json" \
  -d '{
    "flight_segments": [
      {
        "departure_airport": "ICN",
        "arrival_airport": "JFK",
        "departure_time": "2025-12-25T13:45:00Z",
        "arrival_time": "2025-12-25T18:20:00Z",
        "flight_duration_hours": 14.5
      }
    ],
    "destination_timezone": "America/New_York",
    "origin_timezone": "Asia/Seoul",
    "user_sleep_pattern_start": "23:00",
    "user_sleep_pattern_end": "07:00",
    "trip_duration_days": 7
  }'
```

---

## 📝 중요 사항

### 1. 환경 변수 설정

LLM API를 사용하기 위해서는 `.env` 파일에 다음 환경 변수를 설정해야 합니다:

```env
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL_NAME=gemini-1.5-flash  # 선택사항, 기본값: gemini-1.5-flash
```

### 2. 시간대 형식

- 시간대는 IANA Time Zone Database 형식을 사용합니다.
- 예: `Asia/Seoul`, `America/New_York`, `Europe/London`
- 전체 목록: https://en.wikipedia.org/wiki/List_of_tz_database_time_zones

### 3. 날짜/시간 형식

- `departure_time`과 `arrival_time`은 ISO 8601 형식을 사용합니다.
- 예: `2025-12-25T13:45:00Z` (UTC)
- 예: `2025-12-25T13:45:00+09:00` (한국 시간)

### 4. 수면 패턴 형식

- `user_sleep_pattern_start`와 `user_sleep_pattern_end`는 HH:MM 형식을 사용합니다.
- 예: `23:00`, `07:00`

### 5. LLM 응답 처리

- LLM 응답을 구조화된 데이터로 변환하여 반환합니다.
- `daily_schedules`는 LLM 응답을 파싱하여 생성되지만, 기본값이 제공될 수 있습니다.
- `algorithm_explanation`은 LLM이 생성한 원본 응답 텍스트를 포함합니다.

### 6. 비동기 처리

- 모든 LLM API는 비동기 처리를 지원합니다.
- 응답 시간이 수 초에서 수십 초까지 소요될 수 있으므로, 타임아웃을 적절히 설정해야 합니다.

### 7. 비행 구간 처리

- 여러 경유지가 있는 경우, `flight_segments` 배열에 모든 구간을 포함할 수 있습니다.
- 각 구간의 출발/도착 시간과 공항 정보를 정확히 제공하면 더 정확한 계획을 생성할 수 있습니다.

---

## 🔗 관련 파일

### Wellness 관련 파일

- Wellness 라우터: `app/feature/wellness/wellness_router.py`
- Wellness 스키마: `app/feature/wellness/wellness_schemas.py`
- Wellness 서비스: `app/feature/wellness/wellness_service.py`

### LLM 관련 파일

- LLM 서비스: `app/feature/LLM/llm_service.py`
- LLM 스키마: `app/feature/LLM/llm_schemas.py`
- Gemini 클라이언트: `app/feature/LLM/gemini_client.py`

### 설정 파일

- 환경 변수 설정: `app/core/config.py`
- 예외 처리: `app/core/exceptions/exceptions.py`

---

## 📚 관련 문서

- [LLM 챗 API 문서](./API_LLM_CHAT.md)

---

**문서 버전**: 1.0  
**최종 업데이트**: 2025-01-20

