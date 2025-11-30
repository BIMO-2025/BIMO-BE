@echo off
chcp 65001 >nul
echo ========================================
echo   BIMO-BE 테스트 실행
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
    pause
    exit /b 1
)

REM 가상 환경 활성화 (있는 경우)
if exist "venv\Scripts\activate.bat" (
    echo 가상 환경 활성화 중...
    call venv\Scripts\activate.bat
    echo.
)

REM pytest 설치 확인
python -c "import pytest" >nul 2>&1
if errorlevel 1 (
    echo [오류] pytest가 설치되어 있지 않습니다.
    echo 다음 명령어로 설치해주세요: pip install -r requirements.txt
    pause
    exit /b 1
)

echo 테스트 실행 중...
echo ========================================
echo.

REM 테스트 실행 (상세한 에러 정보 포함)
python -m pytest tests/ -v --tb=long --showlocals --full-trace -ra

if errorlevel 1 (
    echo.
    echo [경고] 일부 테스트가 실패했습니다.
    echo.
) else (
    echo.
    echo [성공] 모든 테스트가 통과했습니다!
    echo.
)

pause

