"""
설정 관리 모듈
환경 변수와 애플리케이션 설정을 중앙에서 관리합니다.
"""

from pydantic_settings import BaseSettings
from typing import List, Optional
import os
from functools import lru_cache


class Settings(BaseSettings):
    """
    애플리케이션 설정 클래스
    
    환경 변수에서 값을 자동으로 읽어옵니다.
    .env 파일이나 시스템 환경 변수를 사용할 수 있습니다.
    """
    
    # 기본 설정
    APP_NAME: str = "YouTube Translator"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    PORT: int = 8000
    
    # Gemini API 설정
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-1.5-flash"  # 또는 gemini-1.5-pro
    
    # YouTube 관련 설정
    MAX_VIDEO_LENGTH: int = 3600  # 최대 영상 길이 (초 단위, 기본 1시간)
    SUPPORTED_LANGUAGES: List[str] = ["en", "ko"]  # 지원 언어
    
    # 캐싱 설정
    CACHE_ENABLED: bool = True
    CACHE_TTL: int = 86400  # 캐시 유효 시간 (초 단위, 기본 24시간)
    REDIS_URL: Optional[str] = None  # Redis URL (캐싱용)
    
    # CORS 설정
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "https://yourdomain.com"
    ]
    
    # 보안 설정
    SECRET_KEY: str = "your-secret-key-change-this-in-production"
    API_KEY_HEADER: str = "X-API-Key"
    RATE_LIMIT_PER_MINUTE: int = 10  # 분당 요청 제한
    
    # 로깅 설정
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # 데이터베이스 설정 (선택사항)
    DATABASE_URL: Optional[str] = None
    
    # 파일 저장 설정
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    
    # Gemini API 제한 설정
    GEMINI_REQUESTS_PER_MINUTE: int = 60  # 무료 티어 기준
    GEMINI_MAX_OUTPUT_TOKENS: int = 8192
    GEMINI_TEMPERATURE: float = 0.7
    
    # 기능 플래그
    ENABLE_DOWNLOAD: bool = True  # 번역 결과 다운로드 기능
    ENABLE_SUMMARY: bool = True   # 요약 기능
    ENABLE_CACHE: bool = True     # 캐싱 기능
    
    class Config:
        """Pydantic 설정"""
        env_file = ".env"  # .env 파일에서 환경 변수 읽기
        env_file_encoding = "utf-8"
        case_sensitive = True  # 대소문자 구분
        
        # 환경 변수 예시
        json_schema_extra = {
            "example": {
                "GEMINI_API_KEY": "AIzaSyD-xxxxxxxxxxxxx",
                "DEBUG": True,
                "PORT": 8000,
                "MAX_VIDEO_LENGTH": 3600,
                "CACHE_TTL": 86400
            }
        }
    
    def validate_settings(self) -> bool:
        """설정 유효성 검사"""
        errors = []
        
        # 필수 설정 확인
        if not self.GEMINI_API_KEY:
            errors.append("GEMINI_API_KEY가 설정되지 않았습니다.")
        
        # 포트 범위 확인
        if not (1 <= self.PORT <= 65535):
            errors.append("PORT는 1-65535 사이여야 합니다.")
        
        # 캐시 설정 확인
        if self.CACHE_ENABLED and not self.REDIS_URL:
            # Redis URL이 없으면 메모리 캐시 사용
            print("⚠️  Redis URL이 없어 메모리 캐시를 사용합니다.")
        
        # 오류가 있으면 출력
        if errors:
            for error in errors:
                print(f"❌ 설정 오류: {error}")
            return False
        
        return True
    
    @property
    def is_production(self) -> bool:
        """프로덕션 환경인지 확인"""
        return not self.DEBUG
    
    @property
    def gemini_config(self) -> dict:
        """Gemini API 설정 반환"""
        return {
            "model": self.GEMINI_MODEL,
            "temperature": self.GEMINI_TEMPERATURE,
            "max_output_tokens": self.GEMINI_MAX_OUTPUT_TOKENS,
        }
    
    def get_redis_client(self):
        """Redis 클라이언트 반환 (캐싱용)"""
        if not self.REDIS_URL:
            return None
            
        try:
            import redis
            return redis.from_url(self.REDIS_URL)
        except ImportError:
            print("⚠️  redis 패키지가 설치되지 않았습니다.")
            return None
        except Exception as e:
            print(f"❌ Redis 연결 실패: {e}")
            return None
    
    def __str__(self) -> str:
        """설정 정보 문자열 표현"""
        return f"""
YouTube Translator 설정:
- 환경: {'개발' if self.DEBUG else '프로덕션'}
- 포트: {self.PORT}
- Gemini 모델: {self.GEMINI_MODEL}
- 최대 영상 길이: {self.MAX_VIDEO_LENGTH}초
- 캐싱: {'활성화' if self.CACHE_ENABLED else '비활성화'}
        """


# 설정 싱글톤 인스턴스
@lru_cache()
def get_settings() -> Settings:
    """
    설정 인스턴스 반환 (싱글톤 패턴)
    
    Returns:
        Settings: 애플리케이션 설정
    """
    settings = Settings()
    
    # 설정 유효성 검사
    if not settings.validate_settings():
        print("⚠️  일부 설정에 문제가 있습니다. 기본값을 사용합니다.")
    
    return settings


# 전역 설정 인스턴스
settings = get_settings()


# 환경별 설정 오버라이드
if settings.DEBUG:
    # 개발 환경 설정
    settings.LOG_LEVEL = "DEBUG"
    settings.RATE_LIMIT_PER_MINUTE = 100  # 개발 중에는 제한 완화
else:
    # 프로덕션 환경 설정
    settings.LOG_LEVEL = "INFO"
    # HTTPS만 허용
    settings.ALLOWED_ORIGINS = [
        origin for origin in settings.ALLOWED_ORIGINS 
        if origin.startswith("https://")
    ]


# 설정 정보 출력 (서버 시작 시)
if __name__ == "__main__":
    print("=" * 50)
    print("YouTube Translator 설정 정보")
    print("=" * 50)
    print(settings)
    print("=" * 50)
    
    # 환경 변수 예시 출력
    print("\n📝 .env 파일 예시:")
    print("""
GEMINI_API_KEY=your_gemini_api_key_here
DEBUG=True
PORT=8000
MAX_VIDEO_LENGTH=3600
CACHE_TTL=86400
REDIS_URL=redis://localhost:6379/0
    """)
    
    # 개발자를 위한 팁
    print("\n💡 개발자 팁:")
    print("1. .env 파일은 절대 Git에 커밋하지 마세요!")
    print("2. 프로덕션에서는 DEBUG=False로 설정하세요.")
    print("3. SECRET_KEY는 반드시 변경하세요.")
    print("4. Redis를 사용하면 성능이 크게 향상됩니다.")
