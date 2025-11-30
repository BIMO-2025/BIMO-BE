# BIMO-BE 테스트 PowerShell 실행 스크립트

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  BIMO-BE 테스트 실행" -ForegroundColor Cyan
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
    Read-Host "계속하려면 Enter를 누르세요"
    exit 1
}

# 가상 환경 활성화 (있는 경우)
if (Test-Path "venv\Scripts\Activate.ps1") {
    Write-Host "가상 환경 활성화 중..." -ForegroundColor Yellow
    & "venv\Scripts\Activate.ps1"
    Write-Host ""
}

# pytest 설치 확인
try {
    python -c "import pytest" 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "pytest not found"
    }
} catch {
    Write-Host "[오류] pytest가 설치되어 있지 않습니다." -ForegroundColor Red
    Write-Host "다음 명령어로 설치해주세요: pip install -r requirements.txt" -ForegroundColor Yellow
    Read-Host "계속하려면 Enter를 누르세요"
    exit 1
}

Write-Host "테스트 실행 중..." -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 테스트 실행 (상세한 에러 정보 포함)
try {
    python -m pytest tests/ -v --tb=long --showlocals --full-trace -ra
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "[성공] 모든 테스트가 통과했습니다!" -ForegroundColor Green
        Write-Host ""
    } else {
        Write-Host ""
        Write-Host "[경고] 일부 테스트가 실패했습니다." -ForegroundColor Yellow
        Write-Host ""
    }
} catch {
    Write-Host ""
    Write-Host "[오류] 테스트 실행 중 오류가 발생했습니다." -ForegroundColor Red
    Write-Host ""
}

Read-Host "계속하려면 Enter를 누르세요"

