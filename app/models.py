"""
YouTube Translator API 모델 정의
Pydantic v1을 사용한 안정적인 버전
"""

from pydantic import BaseModel, HttpUrl, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


# Enum 정의
class TranslationStatus(str, Enum):
    """번역 상태"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class LanguageCode(str, Enum):
    """지원 언어 코드"""
    EN = "en"  # 영어
    KO = "ko"  # 한국어
    JA = "ja"  # 일본어
    ZH = "zh"  # 중국어
    ES = "es"  # 스페인어
    FR = "fr"  # 프랑스어


# Request 모델
class TranslateRequest(BaseModel):
    """YouTube 번역 요청 모델"""
    youtube_url: HttpUrl = Field(
        ...,
        description="번역할 YouTube 영상 URL",
        example="https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    )
    
    # 선택적 필드
    target_language: LanguageCode = Field(
        default=LanguageCode.KO,
        description="번역 대상 언어"
    )
    
    @validator('youtube_url')
    def validate_youtube_url(cls, v):
        """YouTube URL 유효성 검사"""
        url_str = str(v)
        if not any(domain in url_str for domain in ['youtube.com', 'youtu.be']):
            raise ValueError('유효한 YouTube URL이 아닙니다.')
        return v
    
    class Config:
        """Pydantic v1 설정"""
        str_strip_whitespace = True  # 문자열 공백 자동 제거
        schema_extra = {
            "example": {
                "youtube_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                "target_language": "ko"
            }
        }


# Response 모델
class TranslationSegment(BaseModel):
    """번역 세그먼트 (자막 한 줄)"""
    start_time: float = Field(..., description="시작 시간 (초)")
    end_time: float = Field(..., description="종료 시간 (초)")
    original_text: str = Field(..., description="원본 텍스트")
    translated_text: str = Field(..., description="번역된 텍스트")
    confidence: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="번역 신뢰도 (0.0 ~ 1.0)"
    )


class VideoMetadata(BaseModel):
    """YouTube 영상 메타데이터"""
    video_id: str = Field(..., description="YouTube 영상 ID")
    title: str = Field(..., description="영상 제목")
    channel: str = Field(..., description="채널명")
    duration: int = Field(..., description="영상 길이 (초)")
    thumbnail_url: Optional[HttpUrl] = Field(None, description="썸네일 URL")
    published_at: Optional[datetime] = Field(None, description="게시일")


class TranslateResponse(BaseModel):
    """번역 응답 모델"""
    status: TranslationStatus = Field(..., description="번역 상태")
    video_metadata: VideoMetadata = Field(..., description="영상 메타데이터")
    segments: List[TranslationSegment] = Field(
        default_factory=list,
        description="번역된 자막 세그먼트 목록"
    )
    total_segments: int = Field(..., description="전체 세그먼트 수")
    processing_time: Optional[float] = Field(None, description="처리 시간 (초)")
    error_message: Optional[str] = Field(None, description="오류 발생 시 메시지")
    
    class Config:
        """응답 예시"""
        schema_extra = {
            "example": {
                "status": "completed",
                "video_metadata": {
                    "video_id": "dQw4w9WgXcQ",
                    "title": "Example Video",
                    "channel": "Example Channel",
                    "duration": 300,
                    "thumbnail_url": "https://i.ytimg.com/vi/dQw4w9WgXcQ/maxresdefault.jpg"
                },
                "segments": [
                    {
                        "start_time": 0.0,
                        "end_time": 3.5,
                        "original_text": "Hello, world!",
                        "translated_text": "안녕하세요, 세계!",
                        "confidence": 0.95
                    }
                ],
                "total_segments": 1,
                "processing_time": 2.5
            }
        }


# 헬스체크 응답
class HealthCheckResponse(BaseModel):
    """헬스체크 응답 모델"""
    status: str = Field(..., description="서버 상태")
    version: str = Field(..., description="API 버전")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="응답 시간"
    )
    gemini_configured: bool = Field(..., description="Gemini API 설정 여부")


# 에러 응답
class ErrorResponse(BaseModel):
    """에러 응답 모델"""
    error: str = Field(..., description="에러 유형")
    message: str = Field(..., description="에러 메시지")
    detail: Optional[Dict[str, Any]] = Field(None, description="추가 에러 정보")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="에러 발생 시간"
    )


# WebSocket 메시지 (실시간 진행상황용)
class WebSocketMessage(BaseModel):
    """WebSocket 메시지 모델"""
    type: str = Field(..., description="메시지 타입 (progress, error, complete)")
    data: Dict[str, Any] = Field(..., description="메시지 데이터")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="메시지 시간"
    )
    
    class Config:
        """메시지 예시"""
        schema_extra = {
            "example": {
                "type": "progress",
                "data": {
                    "current_segment": 10,
                    "total_segments": 50,
                    "percentage": 20
                },
                "timestamp": "2025-06-17T12:00:00Z"
            }
        }
