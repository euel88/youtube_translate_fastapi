# YouTube Translator Dockerfile
# 멀티 스테이지 빌드로 이미지 크기 최적화

# ===========================
# Stage 1: Builder
# ===========================
FROM python:3.11-slim as builder

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 패키지 업데이트 및 필수 도구 설치
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# 의존성 파일 복사
COPY requirements.txt .

# 가상환경 생성 및 패키지 설치
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ===========================
# Stage 2: Runtime
# ===========================
FROM python:3.11-slim

# 메타데이터
LABEL maintainer="your.email@example.com"
LABEL description="YouTube Translator API Server"
LABEL version="1.0.0"

# 환경 변수 설정
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    PORT=8000

# 작업 디렉토리 설정
WORKDIR /app

# 런타임 의존성 설치
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# builder에서 가상환경 복사
COPY --from=builder /opt/venv /opt/venv

# 애플리케이션 코드 복사
COPY app/ ./app/
COPY .env.example .

# 비루트 사용자 생성 (보안)
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

# 사용자 전환
USER appuser

# 헬스체크 설정
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# 포트 노출
EXPOSE ${PORT}

# 애플리케이션 실행
CMD ["gunicorn", "app.main:app", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--workers", "4", \
     "--bind", "0.0.0.0:8000", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]

# ===========================
# 빌드 명령어
# ===========================
# docker build -t youtube-translator .
# docker run -p 8000:8000 --env-file .env youtube-translator
