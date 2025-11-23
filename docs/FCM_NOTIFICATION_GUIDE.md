# 🔔 FCM 알림 기능 가이드

## 개요

BIMO-BE에 Firebase Cloud Messaging (FCM) 푸시 알림 기능이 추가되었습니다.

## 주요 기능

1. **로그인 시 FCM 토큰 저장**: 사용자가 로그인할 때 FCM 토큰을 자동으로 저장
2. **FCM 토큰 관리**: 토큰 업데이트 및 제거 기능
3. **푸시 알림 전송**: 사용자에게 알림 전송

## 구현 내용

### 1. 사용자 스키마 업데이트

`UserBase`와 `UserInDB`에 `fcm_tokens` 필드가 추가되었습니다:

```python
class UserBase(BaseModel):
    uid: str
    email: Optional[EmailStr] = None
    display_name: Optional[str] = None
    photo_url: Optional[str] = None
    provider_id: str
    fcm_tokens: Optional[List[str]] = []  # 여러 디바이스 지원
```

### 2. 로그인 요청 스키마 업데이트

`SocialLoginRequest`에 `fcm_token` 필드가 추가되었습니다:

```python
class SocialLoginRequest(BaseModel):
    token: str
    fcm_token: Optional[str] = None  # FCM 디바이스 토큰 (선택사항)
```

### 3. 로그인 시 FCM 토큰 저장

로그인 시 FCM 토큰이 자동으로 Firestore에 저장됩니다:
- 신규 사용자: FCM 토큰이 포함된 사용자 정보 생성
- 기존 사용자: FCM 토큰 목록에 추가 (중복 방지)

## API 엔드포인트

### 1. 알림 전송

**엔드포인트**: `POST /notifications/send`

**인증**: JWT 토큰 필요 (Authorization 헤더)

**요청 본문**:
```json
{
  "title": "알림 제목",
  "body": "알림 본문",
  "data": {
    "key1": "value1",
    "key2": "value2"
  },
  "image_url": "https://example.com/image.jpg"
}
```

**응답**:
```json
{
  "success_count": 1,
  "failure_count": 0,
  "message": "알림 전송 완료"
}
```

### 2. FCM 토큰 업데이트

**엔드포인트**: `POST /notifications/token/update`

**인증**: JWT 토큰 필요 (Authorization 헤더)

**요청 본문**:
```json
{
  "fcm_token": "fcm-device-token-here"
}
```

**응답**:
```json
{
  "message": "FCM 토큰이 업데이트되었습니다."
}
```

### 3. FCM 토큰 제거

**엔드포인트**: `POST /notifications/token/remove`

**인증**: JWT 토큰 필요 (Authorization 헤더)

**요청 본문**:
```json
{
  "fcm_token": "fcm-device-token-here"
}
```

**응답**:
```json
{
  "message": "FCM 토큰이 제거되었습니다."
}
```

## 프론트엔드 통합

### 1. 로그인 시 FCM 토큰 전송

```typescript
// React Native 예시
import messaging from '@react-native-firebase/messaging';

async function loginWithGoogle(idToken: string) {
  // FCM 토큰 가져오기
  const fcmToken = await messaging().getToken();
  
  // 로그인 요청에 FCM 토큰 포함
  const response = await fetch('http://your-api.com/auth/google/login', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      token: idToken,
      fcm_token: fcmToken  // FCM 토큰 추가
    })
  });
  
  return response.json();
}
```

### 2. FCM 토큰 업데이트 (앱 재시작 시)

```typescript
// 앱이 재시작되거나 토큰이 갱신될 때
messaging().onTokenRefresh(async (newToken) => {
  await fetch('http://your-api.com/notifications/token/update', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${accessToken}`
    },
    body: JSON.stringify({
      fcm_token: newToken
    })
  });
});
```

### 3. 로그아웃 시 FCM 토큰 제거

```typescript
async function logout(fcmToken: string, accessToken: string) {
  // FCM 토큰 제거
  await fetch('http://your-api.com/notifications/token/remove', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${accessToken}`
    },
    body: JSON.stringify({
      fcm_token: fcmToken
    })
  });
  
  // 로그아웃 처리
}
```

## 사용 예시

### 비행 전 알림 전송

```python
from app.feature.notifications import notification_service

# 사용자에게 비행 전 알림 전송
result = await notification_service.send_notification_to_user_by_uid(
    uid="user-123",
    title="출발 시간 알림",
    body="곧 출발 시간입니다. 체크인을 완료해주세요.",
    data={
        "type": "flight_reminder",
        "flight_id": "flight-456"
    }
)
```

### 시차적응 알림 전송

```python
result = await notification_service.send_notification_to_user_by_uid(
    uid="user-123",
    title="수면 시간 알림",
    body="현지 시간에 맞춰 수면 시간입니다.",
    data={
        "type": "jetlag_reminder",
        "timezone": "America/New_York"
    }
)
```

## 주의사항

1. **FCM 토큰은 선택사항**: 로그인 시 FCM 토큰이 없어도 로그인은 정상적으로 작동합니다.
2. **여러 디바이스 지원**: 한 사용자가 여러 디바이스에서 로그인할 수 있으며, 모든 디바이스에 알림이 전송됩니다.
3. **토큰 갱신**: FCM 토큰은 앱 재설치나 특정 상황에서 변경될 수 있으므로, 정기적으로 업데이트하는 것이 좋습니다.
4. **무효한 토큰**: 전송 실패한 토큰은 자동으로 제거되지 않으므로, 주기적으로 정리하는 로직을 추가하는 것을 권장합니다.

## Firebase 설정

FCM은 Firebase Admin SDK를 통해 작동하므로, 추가 설정이 필요하지 않습니다. 현재 사용 중인 Firebase 서비스 계정 키로 FCM 알림을 전송할 수 있습니다.

## 테스트

FCM 알림 기능을 테스트하려면:

1. 실제 디바이스에서 FCM 토큰 획득
2. 로그인 시 FCM 토큰 전송
3. `/notifications/send` 엔드포인트로 알림 전송
4. 디바이스에서 알림 수신 확인

## 추가 개선 사항 (선택사항)

1. **토큰 정리**: 주기적으로 무효한 토큰 제거
2. **알림 히스토리**: 전송한 알림 기록 저장
3. **알림 설정**: 사용자별 알림 수신 설정
4. **배치 알림**: 여러 사용자에게 동시에 알림 전송

