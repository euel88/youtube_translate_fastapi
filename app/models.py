"""
데이터 모델 정의
Pydantic을 사용하여 요청/응답 데이터의 구조를 정의합니다.

Pydantic의 장점:
1. 자동 데이터 검증
2. 타입 힌트 지원
3. JSON 스키마 자동 생성 (API 문서용)
4. 직렬화/역직렬화 자동 처리
"""

from pydantic import BaseModel, HttpUrl, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# Enum 정의 - 상수값들을 그룹화
class TranslationStatus(str, Enum):
    """번역 상태를 나타내는 열거형"""
    PENDING = "pending"          # 대기 중
    PROCESSING = "processing"    # 처리 중
    COMPLETED = "completed"      # 완료
    FAILED = "failed"           # 실패


class VideoQuality(str, Enum):
    """비디오 품질 옵션"""
    AUTO = "auto"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Language(str, Enum):
    """지원 언어"""
    ENGLISH = "en"
    KOREAN = "ko"
    JAPANESE = "ja"
    CHINESE = "zh"
    SPANISH = "es"


# 요청 모델 - 클라이언트가 보내는 데이터
class TranslateRequest(BaseModel):
    """
    번역 요청 모델
    
    클라이언트가 API로 보내는 데이터의 구조를 정의합니다.
    """
    youtube_url: HttpUrl = Field(
        ...,  # 필수 필드
        description="번역할 YouTube 영상 URL",
        example="https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    )
    
    target_language: Language = Field(
        default=Language.KOREAN,
        description="번역 대상 언어"
    )
    
    include_summary: bool = Field(
        default=True,
        description="요약 포함 여부"
    )
    
    quality: VideoQuality = Field(
        default=VideoQuality.AUTO,
        description="비디오 품질 설정"
    )
    
    # 커스텀 검증 로직
    @validator('youtube_url')
    def validate_youtube_url(cls, v):
        """YouTube URL 형식 검증"""
        url_str = str(v)
        
        # YouTube URL 패턴 확인
        valid_patterns = [
            'youtube.com/watch?v=',
            'youtu.be/',
            'youtube.com/embed/',
            'm.youtube.com/watch?v='
        ]
        
        if not any(pattern in url_str for pattern in valid_patterns):
            raise ValueError('유효한 YouTube URL이 아닙니다.')
        
        return v
    
    class Config:
        """Pydantic 설정"""
        # JSON 스키마 예시 - API 문서에 표시됨
        schema_extra = {
            "example": {
                "youtube_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                "target_language": "ko",
                "include_summary": True,
                "quality": "auto"
            }
        }


# 응답 모델 - 서버가 반환하는 데이터
class TranslateResponse(BaseModel):
    """
    번역 응답 모델
    
    API가 클라이언트에게 반환하는 데이터의 구조를 정의합니다.
    """
    # 기본 정보
    status: TranslationStatus = Field(
        description="번역 작업 상태"
    )
    
    youtube_url: str = Field(
        description="원본 YouTube URL"
    )
    
    # 번역 결과
    translation: Optional[str] = Field(
        None,
        description="번역된 전체 텍스트"
    )
    
    summary: Optional[str] = Field(
        None,
        description="내용 요약 (요청 시)"
    )
    
    # 메타데이터
    video_title: Optional[str] = Field(
        None,
        description="영상 제목"
    )
    
    video_duration: Optional[str] = Field(
        None,
        description="영상 길이 (예: '10:30')"
    )
    
    channel_name: Optional[str] = Field(
        None,
        description="채널 이름"
    )
    
    # 시간 정보
    translated_at: datetime = Field(
        default_factory=datetime.now,
        description="번역 완료 시간"
    )
    
    processing_time: Optional[float] = Field(
        None,
        description="처리 소요 시간 (초)"
    )
    
    # 추가 정보
    word_count: Optional[int] = Field(
        None,
        description="번역된 텍스트의 단어 수"
    )
    
    confidence_score: Optional[float] = Field(
        None,
        ge=0.0,  # 0 이상
        le=1.0,  # 1 이하
        description="번역 신뢰도 점수 (0-1)"
    )
    
    # 메서드 정의
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return self.dict(exclude_none=True)
    
    def get_formatted_duration(self) -> str:
        """포맷된 영상 길이 반환"""
        if not self.video_duration:
            return "알 수 없음"
        return self.video_duration
    
    class Config:
        """Pydantic 설정"""
        # 날짜 시간 직렬화 설정
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        
        # 응답 예시
        schema_extra = {
            "example": {
                "status": "completed",
                "youtube_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                "translation": "안녕하세요, 오늘은 Python 프로그래밍에 대해...",
                "summary": "이 영상은 Python 기초 문법을 설명합니다.",
                "video_title": "Python Tutorial for Beginners",
                "video_duration": "15:30",
                "channel_name": "Programming with Mosh",
                "translated_at": "2024-01-15T10:30:00",
                "processing_time": 3.5,
                "word_count": 1250,
                "confidence_score": 0.95
            }
        }


# 에러 응답 모델
class ErrorResponse(BaseModel):
    """에러 응답 모델"""
    error: str = Field(
        description="에러 메시지"
    )
    
    detail: Optional[str] = Field(
        None,
        description="상세 에러 정보"
    )
    
    error_code: Optional[str] = Field(
        None,
        description="에러 코드"
    )
    
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="에러 발생 시간"
    )


# 건강 체크 응답 모델
class HealthCheckResponse(BaseModel):
    """서버 상태 확인 응답"""
    status: str = Field(
        description="서버 상태 (healthy/unhealthy)"
    )
    
    version: str = Field(
        description="API 버전"
    )
    
    gemini_configured: bool = Field(
        description="Gemini API 설정 여부"
    )
    
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="확인 시간"
    )


# 통계 모델
class TranslationStats(BaseModel):
    """번역 통계 모델"""
    total_translations: int = Field(
        default=0,
        description="전체 번역 수"
    )
    
    successful_translations: int = Field(
        default=0,
        description="성공한 번역 수"
    )
    
    failed_translations: int = Field(
        default=0,
        description="실패한 번역 수"
    )
    
    average_processing_time: float = Field(
        default=0.0,
        description="평균 처리 시간 (초)"
    )
    
    most_translated_channels: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="가장 많이 번역된 채널 목록"
    )
    
    @property
    def success_rate(self) -> float:
        """성공률 계산"""
        if self.total_translations == 0:
            return 0.0
        return self.successful_translations / self.total_translations


# 사용자 선호 설정 모델
class UserPreferences(BaseModel):
    """사용자 선호 설정"""
    default_target_language: Language = Field(
        default=Language.KOREAN,
        description="기본 번역 언어"
    )
    
    auto_summary: bool = Field(
        default=True,
        description="자동 요약 생성"
    )
    
    save_history: bool = Field(
        default=True,
        description="번역 기록 저장"
    )
    
    notification_enabled: bool = Field(
        default=False,
        description="알림 활성화"
    )


# 배치 번역 요청 모델
class BatchTranslateRequest(BaseModel):
    """여러 영상 일괄 번역 요청"""
    youtube_urls: List[HttpUrl] = Field(
        ...,
        min_items=1,
        max_items=10,
        description="번역할 YouTube URL 목록 (최대 10개)"
    )
    
    target_language: Language = Field(
        default=Language.KOREAN,
        description="번역 대상 언어"
    )
    
    priority: bool = Field(
        default=False,
        description="우선 처리 여부"
    )
    
    @validator('youtube_urls')
    def validate_unique_urls(cls, v):
        """중복 URL 체크"""
        if len(v) != len(set(str(url) for url in v)):
            raise ValueError('중복된 URL이 있습니다.')
        return v


# 번역 작업 모델 (백그라운드 작업용)
class TranslationJob(BaseModel):
    """번역 작업 정보"""
    job_id: str = Field(
        description="작업 ID"
    )
    
    status: TranslationStatus = Field(
        default=TranslationStatus.PENDING,
        description="작업 상태"
    )
    
    youtube_url: str = Field(
        description="번역 대상 URL"
    )
    
    created_at: datetime = Field(
        default_factory=datetime.now,
        description="생성 시간"
    )
    
    started_at: Optional[datetime] = Field(
        None,
        description="시작 시간"
    )
    
    completed_at: Optional[datetime] = Field(
        None,
        description="완료 시간"
    )
    
    error_message: Optional[str] = Field(
        None,
        description="에러 메시지 (실패 시)"
    )
    
    result: Optional[TranslateResponse] = Field(
        None,
        description="번역 결과 (완료 시)"
    )


# 💡 개발자를 위한 팁
"""
Pydantic 모델 사용 팁:

1. Field()를 사용하여 상세한 설명과 제약 조건을 추가하세요
2. validator를 사용하여 커스텀 검증 로직을 구현하세요
3. Config 클래스로 모델의 동작을 커스터마이즈하세요
4. 타입 힌트를 정확히 사용하면 자동완성이 잘 작동합니다
5. Optional 필드는 None을 기본값으로 설정하세요

예시:
    # API 엔드포인트에서 사용
    @app.post("/translate", response_model=TranslateResponse)
    async def translate(request: TranslateRequest):
        # Pydantic이 자동으로 데이터를 검증합니다
        return TranslateResponse(...)
"""
