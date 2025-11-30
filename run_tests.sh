#!/bin/bash

echo "========================================"
echo "  BIMO-BE 테스트 실행"
echo "========================================"
echo ""

# 가상 환경 활성화 (있는 경우)
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# pytest 설치 확인
if ! python -c "import pytest" 2>/dev/null; then
    echo "[오류] pytest가 설치되어 있지 않습니다."
    echo "다음 명령어로 설치해주세요: pip install -r requirements.txt"
    exit 1
fi

echo "테스트 실행 중..."
echo "========================================"
echo ""

# 테스트 실행 (상세한 에러 정보 포함)
python -m pytest tests/ -v --tb=long --showlocals --full-trace -ra

if [ $? -eq 0 ]; then
    echo ""
    echo "[성공] 모든 테스트가 통과했습니다!"
    echo ""
else
    echo ""
    echo "[경고] 일부 테스트가 실패했습니다."
    echo ""
fi

