"""
YouTube Translator API 설정
Pydantic v1을 사용한 안정적인 버전
"""

from pydantic import BaseSettings, Field
from typing import List, Optional
import os
from pathlib import Path


class Settings(BaseSettings):
    """애플리케이션 설정"""
    
    # API 키
    GEMINI_API_KEY: str = Field(default="", env="GEMINI_API_KEY")
    
    # 서버 설정
    HOST: str = Field(default="0.0.0.0", env="HOST")
    PORT: int = Field(default=8000, env="PORT")
    ENVIRONMENT: str = Field(default="development", env="ENVIRONMENT")
    DEBUG: bool = Field(default=False, env="DEBUG")
    
    # CORS 설정 (쉼표로 구분된 문자열 처리)
    ALLOWED_ORIGINS: List[str] = Field(default=["*"])
    
    # 로깅 설정
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    
    # 번역 설정
    DEFAULT_TARGET_LANGUAGE: str = Field(default="ko", env="DEFAULT_TARGET_LANGUAGE")
    MAX_VIDEO_DURATION: int = Field(default=3600, env="MAX_VIDEO_DURATION")  # 1시간
    
    # 프로젝트 경로
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    
    class Config:
        """Pydantic v1 설정"""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        
        # 환경변수에서 리스트 타입 처리
        @classmethod
        def parse_env_var(cls, field_name: str, raw_val: str):
            if field_name == "ALLOWED_ORIGINS":
                # 쉼표로 구분된 문자열을 리스트로 변환
                return [origin.strip() for origin in raw_val.split(",")]
            return raw_val
    
    def __init__(self, **values):
        """설정 초기화"""
        # ALLOWED_ORIGINS 환경변수 처리
        origins = os.getenv("ALLOWED_ORIGINS")
        if origins and isinstance(origins, str):
            values["ALLOWED_ORIGINS"] = [o.strip() for o in origins.split(",")]
        super().__init__(**values)
    
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
print("=" * 50)
print("🔧 현재 설정:")
print(f"  - HOST: {settings.HOST}")
print(f"  - PORT: {settings.PORT}")
print(f"  - DEBUG: {settings.DEBUG}")
print(f"  - ENVIRONMENT: {settings.ENVIRONMENT}")
print(f"  - GEMINI_API_KEY: {'설정됨' if settings.GEMINI_API_KEY else '미설정'}")
print("=" * 50)
