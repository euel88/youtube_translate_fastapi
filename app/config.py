"""
YouTube Translator API 설정
Pydantic v2 Settings 사용
"""

from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
from typing import List, Optional
import os
from pathlib import Path


class Settings(BaseSettings):
    """애플리케이션 설정"""
    
    # API 키
    GEMINI_API_KEY: str = Field(
        default="",
        description="Google Gemini API 키"
    )
    
    # 서버 설정
    HOST: str = Field(default="0.0.0.0", description="서버 호스트")
    PORT: int = Field(default=8000, description="서버 포트")
    ENVIRONMENT: str = Field(default="development", description="실행 환경")
    DEBUG: bool = Field(default=False, description="디버그 모드")
    
    # CORS 설정
    ALLOWED_ORIGINS: List[str] = Field(
        default=["*"],
        description="허용된 CORS origin 목록"
    )
    
    # 로깅 설정
    LOG_LEVEL: str = Field(default="INFO", description="로그 레벨")
    
    # 번역 설정
    DEFAULT_TARGET_LANGUAGE: str = Field(default="ko", description="기본 번역 언어")
    MAX_VIDEO_DURATION: int = Field(
        default=3600,  # 1시간
        description="최대 영상 길이 (초)"
    )
    
    # Redis 설정 (선택사항)
    REDIS_URL: Optional[str] = Field(
        default=None,
        description="Redis 연결 URL"
    )
    
    # 데이터베이스 설정 (선택사항)
    DATABASE_URL: Optional[str] = Field(
        default=None,
        description="PostgreSQL 데이터베이스 URL"
    )
    
    # API 제한 설정
    RATE_LIMIT_PER_MINUTE: int = Field(
        default=60,
        description="분당 API 요청 제한"
    )
    
    # Sentry 설정 (선택사항)
    SENTRY_DSN: Optional[str] = Field(
        default=None,
        description="Sentry DSN for error tracking"
    )
    
    # 프로젝트 경로
    BASE_DIR: Path = Field(
        default_factory=lambda: Path(__file__).resolve().parent.parent,
        description="프로젝트 루트 디렉토리"
    )
    
    # Pydantic v2 설정
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
        "extra": "ignore",  # 추가 필드 무시
    }
    
    @field_validator('GEMINI_API_KEY')
    @classmethod
    def validate_gemini_key(cls, v: str) -> str:
        """Gemini API 키 검증"""
        if not v and os.getenv("ENVIRONMENT") == "production":
            raise ValueError("프로덕션 환경에서는 GEMINI_API_KEY가 필수입니다.")
        return v
    
    @field_validator('ALLOWED_ORIGINS')
    @classmethod
    def validate_origins(cls, v: List[str]) -> List[str]:
        """CORS origin 검증"""
        # 환경변수에서 쉼표로 구분된 문자열로 올 수 있음
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    @property
    def is_production(self) -> bool:
        """프로덕션 환경 여부"""
        return self.ENVIRONMENT.lower() == "production"
    
    @property
    def is_development(self) -> bool:
        """개발 환경 여부"""
        return self.ENVIRONMENT.lower() == "development"


# 설정 싱글톤 인스턴스
settings = Settings()

# 시작 시 설정 확인 출력
if settings.DEBUG:
    print("=" * 50)
    print("🔧 현재 설정:")
    print(f"  - HOST: {settings.HOST}")
    print(f"  - PORT: {settings.PORT}")
    print(f"  - DEBUG: {settings.DEBUG}")
    print(f"  - ENVIRONMENT: {settings.ENVIRONMENT}")
    print(f"  - GEMINI_API_KEY: {'설정됨' if settings.GEMINI_API_KEY else '미설정'}")
    print("=" * 50)
