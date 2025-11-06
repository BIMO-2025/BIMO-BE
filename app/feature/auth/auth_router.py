from fastapi import APIRouter
from app.feature.auth import auth_schemas, auth_service
from firebase_admin.auth import UserRecord  # Kakao에서 반환된 타입

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
    responses={404: {"description": "Not found"}},
)


@router.post("/google/login", response_model=auth_schemas.TokenResponse)
async def login_with_google(
        request: auth_schemas.SocialLoginRequest
):
    """
    Google Firebase ID Token을 검증하고 API Access Token을 발급합니다.
    """
    # 1. Firebase ID Token 검증 (Google)
    decoded_token = await auth_service.verify_firebase_id_token(request.token)

    # 2. Firestore DB에서 사용자 조회 또는 생성
    user = await auth_service.get_or_create_user(decoded_token)

    # 3. 우리 서비스 전용 API 토큰 생성
    api_access_token = auth_service.generate_api_token(uid=user.uid)

    return {
        "access_token": api_access_token,
        "token_type": "bearer"
    }


@router.post("/apple/login", response_model=auth_schemas.TokenResponse)
async def login_with_apple(
        request: auth_schemas.SocialLoginRequest
):
    """
    Apple Firebase ID Token을 검증하고 API Access Token을 발급합니다.
    (클라이언트가 Firebase SDK로 로그인했다면 Google과 로직 동일)
    """
    # 1. Firebase ID Token 검증 (Apple)
    decoded_token = await auth_service.verify_firebase_id_token(request.token)

    # 2. Firestore DB에서 사용자 조회 또는 생성
    user = await auth_service.get_or_create_user(decoded_token)

    # 3. 우리 서비스 전용 API 토큰 생성
    api_access_token = auth_service.generate_api_token(uid=user.uid)

    return {
        "access_token": api_access_token,
        "token_type": "bearer"
    }


@router.post("/kakao/login", response_model=auth_schemas.TokenResponse)
async def login_with_kakao(
        request: auth_schemas.SocialLoginRequest
):
    """
    Kakao Access Token을 검증하고, Firebase Auth 사용자를 생성/조회한 뒤
    API Access Token을 발급합니다.
    """

    # 1. Kakao Access Token으로 Kakao API에서 사용자 정보 가져오기
    kakao_user_info = await auth_service.verify_kakao_token(request.token)

    # 2. Kakao 정보로 Firebase Auth 사용자 조회 또는 생성
    firebase_user: UserRecord = await auth_service.get_or_create_firebase_user(kakao_user_info)

    # 3. Firestore DB용 "가상 토큰" 생성
    # get_or_create_user 함수가 동일한 입력을 받도록 포맷을 맞춰줍니다.
    synthetic_decoded_token = {
        "uid": firebase_user.uid,
        "email": firebase_user.email,
        "name": firebase_user.display_name,
        "picture": firebase_user.photo_url,
        "firebase": {"sign_in_provider": "kakao.com"}  # 공급자 명시
    }

    # 4. Firestore DB에서 사용자 조회 또는 생성
    user_in_db = await auth_service.get_or_create_user(synthetic_decoded_token)

    # 5. 우리 서비스 전용 API 토큰 생성
    api_access_token = auth_service.generate_api_token(uid=user_in_db.uid)

    return {
        "access_token": api_access_token,
        "token_type": "bearer"
    }