import firebase_admin
from firebase_admin import credentials, firestore
from app.core.config import FIREBASE_KEY_PATH  # 1번 config 파일에서 경로 가져오기

# 서비스 키 경로가 .env에 설정되었는지 확인
if not FIREBASE_KEY_PATH:
    raise ValueError("환경 변수 'FIREBASE_SERVICE_ACCOUNT_KEY'가 설정되지 않았습니다.")

try:
    # Firebase Admin SDK 초기화
    cred = credentials.Certificate(FIREBASE_KEY_PATH)
    firebase_admin.initialize_app(cred)

    # Firestore 클라이언트 생성
    db = firestore.client()

    print("Firebase Admin SDK가 성공적으로 초기화되었습니다.")

except ValueError as e:
    # 파일 경로가 잘못되었을 경우 (예: 파일 없음)
    print(f"Firebase 초기화 오류: 서비스 키 파일 경로를 찾을 수 없습니다. ({e})")
    db = None
except Exception as e:
    print(f"Firebase 초기화 중 알 수 없는 오류 발생: {e}")
    db = None