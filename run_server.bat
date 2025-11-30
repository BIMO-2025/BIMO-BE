@echo off
chcp 65001 >nul
echo ========================================
echo   BIMO-BE Server 시작 중...
echo ========================================
echo.

REM 현재 디렉토리 확인
cd /d "%~dp0"
echo 현재 디렉토리: %CD%
echo.

REM Python 설치 확인
python --version >nul 2>&1
if errorlevel 1 (
    echo [오류] Python이 설치되어 있지 않거나 PATH에 등록되지 않았습니다.
    echo Python을 설치하고 PATH에 추가해주세요.
    pause
    exit /b 1
)

REM 가상 환경 활성화 (있는 경우)
if exist "venv\Scripts\activate.bat" (
    echo 가상 환경 활성화 중...
    call venv\Scripts\activate.bat
    echo.
)

REM uvicorn 설치 확인
python -c "import uvicorn" >nul 2>&1
if errorlevel 1 (
    echo [오류] uvicorn이 설치되어 있지 않습니다.
    echo 다음 명령어로 설치해주세요: pip install -r requirements.txt
    pause
    exit /b 1
)

echo 서버 시작 중...
echo 접속 URL: http://localhost:8000
echo API 문서: http://localhost:8000/docs
echo.
echo 서버를 중지하려면 Ctrl+C를 누르세요.
echo ========================================
echo.

REM 서버 실행
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

if errorlevel 1 (
    echo.
    echo [오류] 서버 시작에 실패했습니다.
    echo 다음을 확인해주세요:
    echo 1. requirements.txt의 패키지가 모두 설치되었는지
    echo 2. .env 파일이 올바르게 설정되었는지
    echo 3. Firebase 서비스 계정 키 파일 경로가 올바른지
    echo.
)

pause


