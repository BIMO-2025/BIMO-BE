# BIMO-BE Server PowerShell 실행 스크립트

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  BIMO-BE Server 시작 중..." -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 현재 스크립트 위치로 이동
Set-Location $PSScriptRoot
Write-Host "현재 디렉토리: $(Get-Location)" -ForegroundColor Gray
Write-Host ""

# Python 설치 확인
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Python 버전: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "[오류] Python이 설치되어 있지 않거나 PATH에 등록되지 않았습니다." -ForegroundColor Red
    Write-Host "Python을 설치하고 PATH에 추가해주세요." -ForegroundColor Yellow
    Read-Host "계속하려면 Enter를 누르세요"
    exit 1
}

# 가상 환경 활성화 (있는 경우)
if (Test-Path "venv\Scripts\Activate.ps1") {
    Write-Host "가상 환경 활성화 중..." -ForegroundColor Yellow
    & "venv\Scripts\Activate.ps1"
    Write-Host ""
}

# uvicorn 설치 확인
try {
    python -c "import uvicorn" 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "uvicorn not found"
    }
} catch {
    Write-Host "[오류] uvicorn이 설치되어 있지 않습니다." -ForegroundColor Red
    Write-Host "다음 명령어로 설치해주세요: pip install -r requirements.txt" -ForegroundColor Yellow
    Read-Host "계속하려면 Enter를 누르세요"
    exit 1
}

Write-Host "서버 시작 중..." -ForegroundColor Green
Write-Host "접속 URL: http://localhost:8000" -ForegroundColor Cyan
Write-Host "API 문서: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "서버를 중지하려면 Ctrl+C를 누르세요." -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 서버 실행
try {
    python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
} catch {
    Write-Host ""
    Write-Host "[오류] 서버 시작에 실패했습니다." -ForegroundColor Red
    Write-Host "다음을 확인해주세요:" -ForegroundColor Yellow
    Write-Host "1. requirements.txt의 패키지가 모두 설치되었는지"
    Write-Host "2. .env 파일이 올바르게 설정되었는지"
    Write-Host "3. Firebase 서비스 계정 키 파일 경로가 올바른지"
    Write-Host ""
    Read-Host "계속하려면 Enter를 누르세요"
}

