"""
이 모듈은 애플리케이션 전반에서 사용될 커스텀 예외 클래스들을 정의합니다.

1. AppConfigError:
   - 애플리케이션 *시작* 시점에 발생하는 설정 오류입니다.
   - 이 예외가 발생하면 앱 시작이 즉시 중단되어야 합니다. (Fail Fast)
   - HTTP 응답으로 변환되지 않습니다.

2. CustomException (및 그 자식 클래스들):
   - 애플리케이션 *런타임* 중에 발생하는 비즈니스 로직 오류입니다.
   - 이 예외들은 main.py에 등록된 exception_handler에 의해
     일관된 JSON 형식의 HTTP 응답으로 변환됩니다.
"""


# --- 1. Startup Configuration Error ---

class AppConfigError(Exception):
    """
    애플리케이션 시작(Startup) 시점에 발생하는
    필수 설정(환경 변수, 키 파일 등) 관련 오류.

    이 예외가 발생하면 앱 시작이 중단되어야 합니다.
    """

    def __init__(self, message: str):
        self.message = f"설정 오류: {message}"
        super().__init__(self.message)


# --- 2. Runtime Exception Base Class ---

class CustomException(Exception):
    """
    런타임(Runtime) 중에 발생하는 모든 커스텀 예외의
    기본 클래스(Base Class)입니다.

    main.py의 exception_handler가 이 클래스의 자식들을
    '잡아서' 일관된 JSON 응답으로 변환합니다.
    """

    def __init__(
            self,
            status_code: int = 500,
            error_code: str = "INTERNAL_SERVER_ERROR",
            message: str = "서버 내부 오류가 발생했습니다.",
    ):
        self.status_code = status_code
        self.error_code = error_code  # 프론트엔드와 규약할 수 있는 문자열 코드
        self.message = message
        super().__init__(self.message)


# --- 3. Specific Runtime Exceptions (Auth / Token) ---

class TokenExpiredError(CustomException):
    """
    토큰이 만료되었을 때 발생하는 예외.
    (Firebase ID 토큰 또는 우리 API 토큰)
    """

    def __init__(self, message: str = "토큰이 만료되었습니다. 다시 로그인하세요."):
        super().__init__(
            status_code=401,
            error_code="TOKEN_EXPIRED",
            message=message
        )


class InvalidTokenError(CustomException):
    """
    토큰의 서명, 형식, 발급자(issuer) 등이 유효하지 않을 때 발생하는 예외.
    """

    def __init__(self, message: str = "토큰이 유효하지 않습니다. 다시 로그인하세요."):
        super().__init__(
            status_code=401,
            error_code="INVALID_TOKEN",
            message=message
        )


class TokenVerificationError(CustomException):
    """
    토큰 검증 중 Firebase/Google 서버 통신 오류 등
    알 수 없는 원인으로 실패했을 때.
    """

    def __init__(self, message: str = "토큰 검증에 실패했습니다. 잠시 후 다시 시도하세요."):
        super().__init__(
            status_code=401,
            error_code="TOKEN_VERIFICATION_FAILED",
            message=message
        )


class AuthInitError(CustomException):
    """
    (런타임) Firebase Auth가 초기화되지 않았는데
    auth_client를 사용하려고 할 때.
    """

    def __init__(self, message: str = "Firebase Auth가 초기화되지 않았습니다. 서버 설정을 확인하세요."):
        # 이 오류는 런타임에 발생하지만, 근본 원인은 500번대 서버 설정 오류입니다.
        super().__init__(
            status_code=500,
            error_code="AUTH_NOT_INITIALIZED",
            message=message
        )


class InvalidTokenPayloadError(CustomException):
    """
    토큰 페이로드(내용물)에 필수 정보(e.g., uid)가 누락되었을 때.
    """

    def __init__(self, message: str = "토큰에 필수 사용자 정보가 없습니다."):
        super().__init__(
            status_code=400,  # 400 Bad Request가 더 적절할 수 있음
            error_code="INVALID_TOKEN_PAYLOAD",
            message=message
        )


# --- 4. Specific Runtime Exceptions (Database) ---

class DatabaseError(CustomException):
    """
    Firestore 등 데이터베이스 작업(조회, 생성, 수정) 중 오류 발생 시.
    """

    def __init__(self, message: str = "데이터베이스 처리 중 오류가 발생했습니다."):
        super().__init__(
            status_code=500,
            error_code="DATABASE_ERROR",
            message=message
        )


# --- 5. Specific Runtime Exceptions (External API) ---

class ExternalApiError(CustomException):
    """
    (확장용) Kakao, Apple 등 외부 소셜 로그인 API 호출 실패 시.
    """

    def __init__(self, message: str = "외부 API 호출에 실패했습니다. 잠시 후 다시 시도하세요."):
        super().__init__(
            status_code=502,  # 502 Bad Gateway
            error_code="EXTERNAL_API_FAILED",
            message=message
        )