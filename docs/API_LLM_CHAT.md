# 💬 LLM 챗 API 문서

프론트엔드 개발자를 위한 LLM (Large Language Model) 챗 API 스키마 가이드입니다.

---

## 📋 목차

1. [기본 정보](#기본-정보)
2. [LLM 챗 API](#llm-챗-api)
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

### 지원 기능

- 텍스트 기반 대화 생성
- 이미지 분석 (탑승권, 좌석표 등)
- 항공편 정보를 활용한 맞춤형 응답 생성

---

## 💬 LLM 챗 API

### 기본 정보

- **엔드포인트**: `POST /llm/chat`
- **설명**: 탑승권 사진 및 사용자 요청을 기반으로 항공사 리뷰/팁을 생성합니다.
- **인증**: 필요 없음 (추후 인증 추가 가능)

### 요청 스키마

```typescript
interface LLMChatRequest {
  prompt: string;                              // 사용자 질문/명령 프롬프트 (필수)
  context?: string[];                          // 대화 문맥이나 참고 문장 목록 (선택)
  system_instruction?: string;                 // 모델의 응답 톤/역할을 제한하는 시스템 인스트럭션 (선택)
  flight_info?: FlightInfo;                    // 항공편 정보 (선택)
  images?: ImageAttachment[];                  // 항공편 정보를 담고 있는 이미지 목록 (선택)
}

interface FlightInfo {
  airline?: string;                            // 항공사명 (예: Korean Air, Delta)
  flight_number?: string;                      // 항공편 번호 (예: KE123)
  seat_class?: string;                         // 좌석 등급 (예: 비즈니스, 이코노미)
  seat_number?: string;                        // 좌석 번호 (예: 12A)
  departure_airport?: string;                  // 출발 공항 또는 도시 (예: ICN, Seoul)
  arrival_airport?: string;                    // 도착 공항 또는 도시 (예: JFK, New York)
  departure_date?: string;                     // 출발 날짜 (ISO8601 또는 자연어 허용)
  meal_preference?: string;                    // 기내식/식단 정보 (예: 채식, 한식)
}

interface ImageAttachment {
  mime_type?: string;                          // 이미지 MIME 타입 (기본값: "image/png")
  base64_data?: string;                        // Base64로 인코딩된 이미지 데이터
  url?: string;                                // 원격 이미지 URL (사전 서명 URL 등)
  // 참고: base64_data 또는 url 중 하나는 반드시 필요
}
```

### 요청 예시

#### 예시 1: 기본 텍스트 요청

```json
{
  "prompt": "대한항공 KE001 편에 대해 알려주세요. 이코노미석 좌석의 편안함과 서비스 품질을 중심으로 설명해주세요."
}
```

#### 예시 2: 항공편 정보 포함 요청

```json
{
  "prompt": "이 항공편에 대한 팁을 알려주세요.",
  "flight_info": {
    "airline": "Korean Air",
    "flight_number": "KE001",
    "seat_class": "이코노미",
    "seat_number": "12A",
    "departure_airport": "ICN",
    "arrival_airport": "JFK",
    "departure_date": "2025-01-25",
    "meal_preference": "한식"
  }
}
```

#### 예시 3: 이미지 포함 요청 (Base64)

```json
{
  "prompt": "이 탑승권을 분석해서 항공사 리뷰와 유용한 팁을 제공해주세요.",
  "images": [
    {
      "mime_type": "image/jpeg",
      "base64_data": "/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRofHh0aHBwgJC4nICIsIxwcKDcpLDAxNDQ0Hyc5PTgyPC4zNDL/2wBDAQkJCQwLDBgNDRgyIRwhMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjL/wAARCAA..."
    }
  ]
}
```

#### 예시 4: 이미지 URL 포함 요청

```json
{
  "prompt": "이 탑승권을 분석해서 항공사 리뷰와 유용한 팁을 제공해주세요.",
  "images": [
    {
      "mime_type": "image/png",
      "url": "https://storage.googleapis.com/bucket/boarding-pass.png"
    }
  ]
}
```

#### 예시 5: 컨텍스트 포함 요청

```json
{
  "prompt": "이전 대화를 바탕으로 더 구체적인 정보를 알려주세요.",
  "context": [
    "사용자가 대한항공 KE001 편에 대해 물어봤습니다.",
    "이코노미석 좌석에 대한 정보를 원하고 있습니다."
  ],
  "flight_info": {
    "airline": "Korean Air",
    "flight_number": "KE001"
  }
}
```

### 응답 스키마

```typescript
interface LLMChatResponse {
  model: string;                               // 사용된 모델 이름 (예: "gemini-1.5-flash")
  content: string;                             // LLM이 생성한 응답 텍스트
}
```

### 응답 예시

```json
{
  "model": "gemini-1.5-flash",
  "content": "대한항공 KE001 편(ICN → JFK)은 장거리 노선으로, 이코노미석은 일반적으로 편안한 편입니다. 좌석 12A는 창가석으로 좋은 위치입니다. 한식 기내식 옵션이 제공되며, 평소에 선호하는 식단으로 신청하시면 됩니다.\n\n**좌석 팁:**\n- 12A는 창가석으로 조명 제어가 자유롭습니다.\n- 장거리 비행이므로 다리 공간을 확보하기 위해 좌석 앞 공간을 활용하세요.\n\n**서비스 팁:**\n- 한식 기내식은 사전 신청이 권장됩니다.\n- 비행 중에는 충분한 수분 섭취를 권장합니다."
}
```

---

## 📝 스키마 정의

### FlightInfo

항공편 정보를 담는 스키마입니다.

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `airline` | string | 선택 | 항공사명 (예: Korean Air, Delta) |
| `flight_number` | string | 선택 | 항공편 번호 (예: KE123) |
| `seat_class` | string | 선택 | 좌석 등급 (예: 비즈니스, 이코노미) |
| `seat_number` | string | 선택 | 좌석 번호 (예: 12A) |
| `departure_airport` | string | 선택 | 출발 공항 또는 도시 (예: ICN, Seoul) |
| `arrival_airport` | string | 선택 | 도착 공항 또는 도시 (예: JFK, New York) |
| `departure_date` | string | 선택 | 출발 날짜 (ISO8601 또는 자연어 허용) |
| `meal_preference` | string | 선택 | 기내식/식단 정보 (예: 채식, 한식) |

### ImageAttachment

이미지 첨부 파일을 담는 스키마입니다.

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `mime_type` | string | 선택 | 이미지 MIME 타입 (기본값: "image/png") |
| `base64_data` | string | 선택* | Base64로 인코딩된 이미지 데이터 |
| `url` | string | 선택* | 원격 이미지 URL (사전 서명 URL 등) |

* `base64_data` 또는 `url` 중 하나는 반드시 필요합니다.

### LLMChatRequest

LLM 챗 요청 스키마입니다.

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `prompt` | string | 필수 | 사용자 질문/명령 프롬프트 (최소 1자) |
| `context` | string[] | 선택 | 대화 문맥이나 참고 문장 목록 |
| `system_instruction` | string | 선택 | 모델의 응답 톤/역할을 제한하는 시스템 인스트럭션 |
| `flight_info` | FlightInfo | 선택 | 항공편 정보 |
| `images` | ImageAttachment[] | 선택 | 항공편 정보를 담고 있는 이미지 목록 |

### LLMChatResponse

LLM 챗 응답 스키마입니다.

| 필드 | 타입 | 설명 |
|------|------|------|
| `model` | string | 사용된 모델 이름 |
| `content` | string | LLM이 생성한 응답 텍스트 |

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
      "loc": ["body", "prompt"],
      "msg": "ensure this value has at least 1 characters",
      "type": "value_error.any_str.min_length"
    }
  ],
  "status_code": 422
}
```

**가능한 원인:**
- 필수 필드 누락
- 잘못된 데이터 형식
- 유효성 검증 실패

#### 4. 이미지 첨부 오류 (422)

```json
{
  "detail": [
    {
      "loc": ["body", "images", 0],
      "msg": "base64_data 또는 url 중 하나는 반드시 필요합니다.",
      "type": "value_error"
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
interface LLMChatRequest {
  prompt: string;
  context?: string[];
  system_instruction?: string;
  flight_info?: FlightInfo;
  images?: ImageAttachment[];
}

interface LLMChatResponse {
  model: string;
  content: string;
}

interface FlightInfo {
  airline?: string;
  flight_number?: string;
  seat_class?: string;
  seat_number?: string;
  departure_airport?: string;
  arrival_airport?: string;
  departure_date?: string;
  meal_preference?: string;
}

interface ImageAttachment {
  mime_type?: string;
  base64_data?: string;
  url?: string;
}

// llmService.ts
const API_BASE_URL = "http://localhost:8000";

export const llmService = {
  async chatWithGemini(request: LLMChatRequest): Promise<LLMChatResponse> {
    const response = await fetch(`${API_BASE_URL}/llm/chat`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "LLM 요청 실패");
    }

    return response.json();
  },

  // 이미지를 Base64로 변환하는 헬퍼 함수
  async convertImageToBase64(file: File): Promise<string> {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => {
        const result = reader.result as string;
        // "data:image/jpeg;base64," 부분 제거
        const base64 = result.split(",")[1];
        resolve(base64);
      };
      reader.onerror = reject;
      reader.readAsDataURL(file);
    });
  },
};

// 사용 예시
// 1. 기본 텍스트 요청
const handleTextChat = async () => {
  try {
    const response = await llmService.chatWithGemini({
      prompt: "대한항공 KE001 편에 대해 알려주세요.",
    });
    console.log("응답:", response.content);
  } catch (error) {
    console.error("요청 실패:", error);
  }
};

// 2. 항공편 정보 포함 요청
const handleFlightInfoChat = async () => {
  try {
    const response = await llmService.chatWithGemini({
      prompt: "이 항공편에 대한 팁을 알려주세요.",
      flight_info: {
        airline: "Korean Air",
        flight_number: "KE001",
        seat_class: "이코노미",
        departure_airport: "ICN",
        arrival_airport: "JFK",
      },
    });
    console.log("응답:", response.content);
  } catch (error) {
    console.error("요청 실패:", error);
  }
};

// 3. 이미지 포함 요청
const handleImageChat = async (imageFile: File) => {
  try {
    const base64Data = await llmService.convertImageToBase64(imageFile);
    const response = await llmService.chatWithGemini({
      prompt: "이 탑승권을 분석해서 항공사 리뷰와 유용한 팁을 제공해주세요.",
      images: [
        {
          mime_type: imageFile.type,
          base64_data: base64Data,
        },
      ],
    });
    console.log("응답:", response.content);
  } catch (error) {
    console.error("요청 실패:", error);
  }
};
```

### cURL 예시

```bash
# 기본 텍스트 요청
curl -X POST "http://localhost:8000/llm/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "대한항공 KE001 편에 대해 알려주세요."
  }'

# 항공편 정보 포함 요청
curl -X POST "http://localhost:8000/llm/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "이 항공편에 대한 팁을 알려주세요.",
    "flight_info": {
      "airline": "Korean Air",
      "flight_number": "KE001",
      "seat_class": "이코노미",
      "departure_airport": "ICN",
      "arrival_airport": "JFK"
    }
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

### 2. 이미지 처리

#### Base64 인코딩

- 이미지를 Base64로 인코딩하여 전송할 수 있습니다.
- Base64 데이터는 `data:image/jpeg;base64,` 접두사 없이 전송해야 합니다.
- 파일 크기가 클 경우 URL 방식 사용을 권장합니다.

#### URL 방식

- 이미지를 클라우드 스토리지(예: Google Cloud Storage)에 업로드한 후 URL을 전송할 수 있습니다.
- URL은 공개적으로 접근 가능하거나 사전 서명된 URL이어야 합니다.

### 3. 시스템 인스트럭션

- 기본 시스템 인스트럭션이 설정되어 있습니다.
- 커스텀 시스템 인스트럭션을 전달하여 모델의 응답 톤/역할을 제한할 수 있습니다.

### 4. LLM 응답 처리

- LLM 응답은 자연어 텍스트 형식입니다.
- 응답 형식이 일관되지 않을 수 있으므로, 클라이언트 측에서 파싱 로직을 구현해야 할 수 있습니다.

### 5. 비동기 처리

- 모든 LLM API는 비동기 처리를 지원합니다.
- 응답 시간이 수 초에서 수십 초까지 소요될 수 있으므로, 타임아웃을 적절히 설정해야 합니다.

---

## 🔗 관련 파일

### LLM 관련 파일

- LLM 라우터: `app/feature/LLM/llm_router.py`
- LLM 스키마: `app/feature/LLM/llm_schemas.py`
- LLM 서비스: `app/feature/LLM/llm_service.py`
- Gemini 클라이언트: `app/feature/LLM/gemini_client.py`
- 프롬프트 빌더: `app/feature/LLM/prompt_builder.py`

### 설정 파일

- 환경 변수 설정: `app/core/config.py`
- 예외 처리: `app/core/exceptions/exceptions.py`

---

## 📚 관련 문서

- [Wellness 시차적응 계획 API 문서](./API_WELLNESS_JETLAG.md)

---

**문서 버전**: 1.0  
**최종 업데이트**: 2025-01-20

