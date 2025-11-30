# 🔐 인증 및 사용자 API 스키마 문서

프론트엔드 개발자를 위한 인증 및 사용자 관련 API 스키마 가이드입니다.

---

## 📋 목차

1. [인증 API](#인증-api)
2. [사용자 스키마](#사용자-스키마)
3. [에러 응답](#에러-응답)
4. [사용 예시](#사용-예시)

---

## 🔑 인증 API

### 기본 정보

- **Base URL**: `/auth`
- **인증 방식**: Bearer Token (JWT)
- **Content-Type**: `application/json`

### 1. Google 로그인

**엔드포인트**: `POST /auth/google/login`

**설명**: 
- 프론트엔드에서 Firebase SDK로 Google 로그인 후 받은 **Firebase ID Token**을 전달합니다.
- 백엔드가 토큰을 검증하고 우리 서비스 전용 JWT를 발급합니다.

#### 요청 스키마

```typescript
interface SocialLoginRequest {
  token: string;  // Firebase ID Token (Google)
}
```

#### 요청 예시

```json
{
  "token": "eyJhbGciOiJSUzI1NiIsImtpZCI6Ij..."
}
```

#### 응답 스키마

```typescript
interface TokenResponse {
  access_token: string;  // 우리 서비스 전용 JWT 토큰
  token_type: "bearer";  // 항상 "bearer"
}
```

#### 응답 예시

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

---

### 2. Apple 로그인

**엔드포인트**: `POST /auth/apple/login`

**설명**: 
- 프론트엔드에서 Firebase SDK로 Apple 로그인 후 받은 **Firebase ID Token**을 전달합니다.
- 백엔드가 토큰을 검증하고 우리 서비스 전용 JWT를 발급합니다.

#### 요청 스키마

```typescript
interface SocialLoginRequest {
  token: string;  // Firebase ID Token (Apple)
}
```

#### 요청 예시

```json
{
  "token": "eyJhbGciOiJSUzI1NiIsImtpZCI6Ij..."
}
```

#### 응답 스키마

```typescript
interface TokenResponse {
  access_token: string;  // 우리 서비스 전용 JWT 토큰
  token_type: "bearer";  // 항상 "bearer"
}
```

#### 응답 예시

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

---

### 3. Kakao 로그인

**엔드포인트**: `POST /auth/kakao/login`

**설명**: 
- 프론트엔드에서 Kakao SDK로 로그인 후 받은 **Kakao Access Token**을 전달합니다.
- 백엔드가 Kakao API로 토큰을 검증하고, Firebase Auth에 사용자를 생성/조회한 후 우리 서비스 전용 JWT를 발급합니다.

#### 요청 스키마

```typescript
interface SocialLoginRequest {
  token: string;  // Kakao Access Token
}
```

#### 요청 예시

```json
{
  "token": "kakao_access_token_here"
}
```

#### 응답 스키마

```typescript
interface TokenResponse {
  access_token: string;  // 우리 서비스 전용 JWT 토큰
  token_type: "bearer";  // 항상 "bearer"
}
```

#### 응답 예시

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

---

## 👤 사용자 스키마

### 1. 사용자 기본 정보 (UserBase)

백엔드 내부에서 사용하는 사용자 기본 정보 스키마입니다.

```typescript
interface UserBase {
  uid: string;                    // Firebase UID (고유 식별자)
  email: string | null;            // 사용자 이메일
  display_name: string | null;     // 사용자 표시 이름
  photo_url: string | null;        // 프로필 사진 URL
  provider_id: string;             // 인증 프로바이더 ("google.com", "apple.com", "kakao.com")
}
```

### 2. 데이터베이스 사용자 정보 (UserInDB)

Firestore에 저장되는 사용자 정보입니다. `UserBase`를 확장합니다.

```typescript
interface UserInDB extends UserBase {
  created_at: string;      // ISO 8601 형식 (예: "2025-01-20T10:30:00Z")
  last_login_at: string;   // ISO 8601 형식 (예: "2025-01-20T10:30:00Z")
}
```

#### 예시

```json
{
  "uid": "firebase_uid_12345",
  "email": "user@example.com",
  "display_name": "홍길동",
  "photo_url": "https://example.com/photo.jpg",
  "provider_id": "google.com",
  "created_at": "2025-01-15T08:00:00Z",
  "last_login_at": "2025-01-20T10:30:00Z"
}
```

### 3. 사용자 계정 정보 (UserSchema)

앱 내 사용자 계정 설정 정보입니다. (별도 엔드포인트에서 사용될 예정)

```typescript
interface UserSchema {
  nickname: string;                 // 사용자 닉네임
  sleepPatternStart: string;       // 수면 패턴 시작 시간 (ISO 8601)
  sleepPatternEnd: string;         // 수면 패턴 종료 시간 (ISO 8601)
  createdAt: string;               // 계정 생성 시간 (ISO 8601)
}
```

#### 예시

```json
{
  "nickname": "BIMO",
  "sleepPatternStart": "2025-11-20T23:00:00Z",
  "sleepPatternEnd": "2025-11-21T07:00:00Z",
  "createdAt": "2025-01-15T08:00:00Z"
}
```

---

## ⚠️ 에러 응답

모든 에러는 다음 형식으로 반환됩니다:

```typescript
interface ErrorResponse {
  detail: string;  // 에러 메시지
  status_code: number;  // HTTP 상태 코드
}
```

### 주요 에러 케이스

#### 1. 토큰 만료 (401)

```json
{
  "detail": "토큰이 만료되었습니다.",
  "status_code": 401
}
```

#### 2. 유효하지 않은 토큰 (401)

```json
{
  "detail": "유효하지 않은 토큰입니다.",
  "status_code": 401
}
```

#### 3. 토큰 검증 실패 (400)

```json
{
  "detail": "토큰 검증 중 오류 발생: ...",
  "status_code": 400
}
```

#### 4. 외부 API 오류 (502)

```json
{
  "detail": "Kakao API 오류: 401 Unauthorized",
  "status_code": 502
}
```

#### 5. 데이터베이스 오류 (500)

```json
{
  "detail": "Firestore 처리 중 오류 발생: ...",
  "status_code": 500
}
```

---

## 💡 사용 예시

### React/TypeScript 예시

```typescript
// types.ts
interface SocialLoginRequest {
  token: string;
}

interface TokenResponse {
  access_token: string;
  token_type: "bearer";
}

// authService.ts
const API_BASE_URL = "http://localhost:8000";

export const authService = {
  // Google 로그인
  async loginWithGoogle(firebaseIdToken: string): Promise<TokenResponse> {
    const response = await fetch(`${API_BASE_URL}/auth/google/login`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        token: firebaseIdToken,
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "로그인 실패");
    }

    return response.json();
  },

  // Apple 로그인
  async loginWithApple(firebaseIdToken: string): Promise<TokenResponse> {
    const response = await fetch(`${API_BASE_URL}/auth/apple/login`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        token: firebaseIdToken,
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "로그인 실패");
    }

    return response.json();
  },

  // Kakao 로그인
  async loginWithKakao(kakaoAccessToken: string): Promise<TokenResponse> {
    const response = await fetch(`${API_BASE_URL}/auth/kakao/login`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        token: kakaoAccessToken,
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "로그인 실패");
    }

    return response.json();
  },
};

// 사용 예시
// Google 로그인
const handleGoogleLogin = async () => {
  try {
    // 1. Firebase SDK로 Google 로그인
    const firebaseIdToken = await signInWithGoogle();
    
    // 2. 백엔드에 토큰 전달하여 우리 서비스 JWT 받기
    const { access_token } = await authService.loginWithGoogle(firebaseIdToken);
    
    // 3. JWT를 로컬 스토리지에 저장
    localStorage.setItem("access_token", access_token);
    
    console.log("로그인 성공!");
  } catch (error) {
    console.error("로그인 실패:", error);
  }
};
```

### cURL 예시

```bash
# Google 로그인
curl -X POST "http://localhost:8000/auth/google/login" \
  -H "Content-Type: application/json" \
  -d '{
    "token": "firebase_id_token_here"
  }'

# Apple 로그인
curl -X POST "http://localhost:8000/auth/apple/login" \
  -H "Content-Type: application/json" \
  -d '{
    "token": "firebase_id_token_here"
  }'

# Kakao 로그인
curl -X POST "http://localhost:8000/auth/kakao/login" \
  -H "Content-Type: application/json" \
  -d '{
    "token": "kakao_access_token_here"
  }'
```

---

## 📝 중요 사항

### 1. 토큰 관리

- 받은 `access_token`은 이후 API 요청 시 `Authorization` 헤더에 포함해야 합니다.
- 형식: `Authorization: Bearer {access_token}`

### 2. 토큰 만료

- JWT 토큰은 기본적으로 30분 후 만료됩니다. (환경 변수로 설정 가능)
- 토큰 만료 시 재로그인이 필요합니다.

### 3. 인증 흐름

```
프론트엔드:
  1. 소셜 로그인 SDK로 로그인
  2. 소셜 프로바이더 토큰 받기
  3. 백엔드에 토큰 전달

백엔드:
  1. 소셜 프로바이더 토큰 검증
  2. 사용자 정보 조회/생성
  3. 우리 서비스 JWT 발급
  4. JWT 반환

프론트엔드:
  1. JWT 저장
  2. 이후 API 요청 시 JWT 사용
```

### 4. 프로바이더별 차이점

| 프로바이더 | 토큰 타입 | 토큰 발급 위치 |
|-----------|----------|--------------|
| Google | Firebase ID Token | Firebase SDK |
| Apple | Firebase ID Token | Firebase SDK |
| Kakao | Kakao Access Token | Kakao SDK |

---

## 🔗 관련 파일

- 인증 스키마: `app/feature/auth/auth_schemas.py`
- 사용자 스키마: `app/shared/schemas.py`, `app/feature/users/users_schemas.py`
- 인증 라우터: `app/feature/auth/auth_router.py`

---

**문서 버전**: 1.0  
**최종 업데이트**: 2025-01-20

