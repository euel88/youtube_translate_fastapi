"""
YouTube Translator 애플리케이션 패키지

이 패키지는 YouTube 영상을 한국어로 번역하는 웹 서비스의
백엔드 애플리케이션을 구현합니다.

주요 모듈:
- main: FastAPI 애플리케이션 및 라우트 정의
- config: 환경 설정 관리
- models: Pydantic 데이터 모델
- services: 비즈니스 로직 (번역 서비스)
"""

__version__ = "1.0.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

# 패키지 레벨 임포트
from app.config import settings
from app.models import TranslateRequest, TranslateResponse

__all__ = [
    "settings",
    "TranslateRequest", 
    "TranslateResponse",
]
