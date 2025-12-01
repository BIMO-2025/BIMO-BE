import firebase_admin
from firebase_admin import auth, credentials, firestore
import json

from app.core.config import FIREBASE_KEY_PATH, FIREBASE_CREDENTIALS_JSON
from app.core.exceptions.exceptions import AppConfigError

# 모듈 레벨에서 변수를 선언합니다.
# 초기화에 실패하면 이 변수들은 None으로 남겠지만,
# 그 전에 예외가 발생하여 앱 시작이 중단될 것입니다.
db = None
auth_client = None

# 1. 설정 확인 (Fail Fast 1)
if not FIREBASE_KEY_PATH and not FIREBASE_CREDENTIALS_JSON:
    raise AppConfigError(
        "Firebase 설정이 없습니다. 'FIREBASE_SERVICE_ACCOUNT_KEY' 파일 경로 또는 'FIREBASE_CREDENTIALS_JSON' 환경 변수를 설정하세요."
    )

try:
    # 2. 서비스 키 로드 (Fail Fast 2)
    cred = None
    
    if FIREBASE_CREDENTIALS_JSON:
        # JSON 문자열이 있는 경우 이를 딕셔너리로 파싱하여 사용
        try:
            cred_dict = json.loads(FIREBASE_CREDENTIALS_JSON)
            cred = credentials.Certificate(cred_dict)
            print("Firebase 인증: 환경 변수(FIREBASE_CREDENTIALS_JSON)를 사용합니다.")
        except json.JSONDecodeError as e:
            raise AppConfigError(f"FIREBASE_CREDENTIALS_JSON 환경 변수가 유효한 JSON이 아닙니다: {e}")
            
    elif FIREBASE_KEY_PATH:
        # 파일 경로가 있는 경우
        cred = credentials.Certificate(FIREBASE_KEY_PATH)
        print(f"Firebase 인증: 키 파일({FIREBASE_KEY_PATH})을 사용합니다.")

    # 3. Firebase Admin SDK 초기화 (Fail Fast 3)
    # 이미 초기화되었으면 에러가 발생할 수 있습니다. (지금 구조에선 괜찮음)
    firebase_admin.initialize_app(cred)

    # 4. 클라이언트 생성
    # 성공적으로 초기화된 경우에만 클라이언트를 할당합니다.
    db = firestore.client()
    auth_client = auth

    print("Firebase Admin SDK가 성공적으로 초기화되었습니다. (Firestore, Auth)")

except ValueError as e:
    # credentials.Certificate()가 실패한 경우 (e.g., 파일은 있으나 JSON 형식이 아님)
    raise AppConfigError(f"Firebase 서비스 키 파일이 유효하지 않습니다: {e}")
except FileNotFoundError:
    # credentials.Certificate()가 실패한 경우 (파일 경로가 잘못됨)
    raise AppConfigError(
        f"Firebase 서비스 키 파일을 찾을 수 없습니다. 경로를 확인하세요: {FIREBASE_KEY_PATH}"
    )
except Exception as e:
    # initialize_app() 실패 등 기타 알 수 없는 오류
    raise AppConfigError(f"Firebase 초기화 중 알 수 없는 오류 발생: {e}")