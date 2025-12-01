# Python 3.12 슬림 이미지 사용 (용량 최적화)
FROM python:3.12-slim

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 의존성 설치 (필요한 경우)
# RUN apt-get update && apt-get install -y gcc && rm -rf /var/lib/apt/lists/*

# 의존성 파일 복사 및 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 소스 코드 복사
COPY . .

# Cloud Run은 PORT 환경변수를 주입해줍니다 (기본값 8080)
ENV PORT=8080

# uvicorn 실행
# --host 0.0.0.0: 컨테이너 외부에서 접속 허용
# --port $PORT: Cloud Run이 주입한 포트 사용
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
