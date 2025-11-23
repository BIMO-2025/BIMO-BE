#!/bin/bash

echo "Starting BIMO-BE Server..."
echo ""

# 가상 환경 활성화 (있는 경우)
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# 서버 실행
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000


