# app/config.py
"""
환경 설정 관리 모듈
Pydantic 1.x 버전 호환
"""

import os
from typing import Optional

# Pydantic 1.x에서는 BaseSettings가 pydantic 패키지 안에 있습니다
from pydantic import BaseSettings  # ✅ 수정된 import
# from pydantic_settings import BaseSettings  # ❌ 이전 코드 (제거)

from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()


class Settings(BaseSettings):
    """애플리케이션 설정"""
    
    # API 키
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    YOUTUBE_API_KEY: Optional[str] = os.getenv("YOUTUBE_API_KEY", None)
    
    # 서버 설정
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", 8000))
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"
    
    # CORS 설정
    ALLOWED_ORIGINS: list = os.getenv(
        "ALLOWED_ORIGINS", 
        "*"
    ).split(",")
    
    # 로깅 설정
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "info")
    
    # 환경 설정
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    
    class Config:
        """Pydantic 설정"""
        env_file = ".env"
        case_sensitive = True
    
    def validate_settings(self):
        """필수 설정 검증"""
        if not self.GEMINI_API_KEY:
            raise ValueError(
                "GEMINI_API_KEY가 설정되지 않았습니다! "
                ".env 파일이나 환경 변수를 확인하세요."
            )
        return True


# 설정 인스턴스 생성
settings = Settings()

# 개발 환경에서만 설정 출력
if settings.DEBUG:
    print("=" * 50)
    print("🔧 현재 설정:")
    print(f"  - HOST: {settings.HOST}")
    print(f"  - PORT: {settings.PORT}")
    print(f"  - DEBUG: {settings.DEBUG}")
    print(f"  - ENVIRONMENT: {settings.ENVIRONMENT}")
    print(f"  - GEMINI_API_KEY: {'설정됨' if settings.GEMINI_API_KEY else '❌ 없음'}")
    print("=" * 50)
