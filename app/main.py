"""
YouTube Translator API - 메인 서버
영어 YouTube 영상을 한국어로 번역하는 FastAPI 서버입니다.
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from contextlib import asynccontextmanager
import logging
from pathlib import Path

from app.config import settings
from app.models import TranslateRequest, TranslateResponse, HealthCheckResponse
from app.services.translator import TranslatorService
from fastapi import WebSocket, WebSocketDisconnect
from typing import List, Dict
import json
from youtube_transcript_api import YouTubeTranscriptApi

# 로깅 설정
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# 앱 생명주기 관리
@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 시작/종료 시 실행되는 코드"""
    # 시작 시
    logger.info(f"🚀 YouTube Translator 서버 시작 - 포트: {settings.PORT}")
    logger.info(f"📊 환경: {'개발' if settings.DEBUG else '프로덕션'}")
    yield
    # 종료 시
    logger.info("👋 서버 종료")


# FastAPI 앱 초기화
app = FastAPI(
    title="YouTube Translator API",
    description="영어 YouTube 영상을 한국어로 번역하는 서비스",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,  # 프로덕션에서는 문서 숨김
    redoc_url="/redoc" if settings.DEBUG else None,
)

# CORS 설정 - 프론트엔드와의 통신을 위해
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 번역 서비스 초기화
translator_service = TranslatorService()

# 정적 파일 경로 설정
static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


# 라우트 정의
@app.get("/", response_class=FileResponse)
async def read_root():
    """메인 페이지 반환"""
    return FileResponse(static_dir / "index.html")


@app.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """서버 상태 확인 엔드포인트"""
    return HealthCheckResponse(
        status="healthy",
        version="1.0.0",
        gemini_configured=bool(settings.GEMINI_API_KEY)
    )


@app.post("/api/translate", response_model=TranslateResponse)
async def translate_youtube(
    request: TranslateRequest,
    background_tasks: BackgroundTasks
):
    """
    YouTube 영상을 한국어로 번역
    
    Args:
        request: YouTube URL을 포함한 번역 요청
        background_tasks: 백그라운드 작업 (로깅, 통계 등)
        
    Returns:
        번역 결과와 메타데이터
        
    Raises:
        HTTPException: 번역 실패 시
    """
    try:
        logger.info(f"번역 요청: {request.youtube_url}")
        
        # URL 유효성 검사
        if not translator_service.is_valid_youtube_url(str(request.youtube_url)):
            raise HTTPException(
                status_code=400,
                detail="유효하지 않은 YouTube URL입니다."
            )
        
        # 번역 실행
        result = await translator_service.translate(str(request.youtube_url))
        
        # 백그라운드에서 통계 기록
        background_tasks.add_task(
            log_translation_stats,
            url=str(request.youtube_url),
            success=True
        )
        
        return result
        
    except ValueError as e:
        logger.error(f"값 오류: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
        
    except Exception as e:
        logger.error(f"번역 오류: {str(e)}")
        background_tasks.add_task(
            log_translation_stats,
            url=str(request.youtube_url),
            success=False,
            error=str(e)
        )
        raise HTTPException(
            status_code=500,
            detail="번역 처리 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요."
        )


@app.get("/api/stats")
async def get_stats():
    """사용 통계 반환 (관리자용)"""
    if not settings.DEBUG:
        raise HTTPException(status_code=404)
    
    # 실제로는 데이터베이스에서 가져옴
    return {
        "total_translations": 1234,
        "today_translations": 56,
        "success_rate": 0.95,
        "average_response_time": 3.2
    }


# 헬퍼 함수
async def log_translation_stats(url: str, success: bool, error: str = None):
    """번역 통계 기록 (백그라운드)"""
    # 실제로는 데이터베이스나 분석 서비스에 기록
    if success:
        logger.info(f"✅ 번역 성공: {url}")
    else:
        logger.error(f"❌ 번역 실패: {url} - {error}")


# 에러 핸들러
@app.exception_handler(404)
async def not_found_handler(request, exc):
    """404 에러 커스텀 처리"""
    return JSONResponse(
        status_code=404,
        content={
            "error": "요청하신 페이지를 찾을 수 없습니다.",
            "path": str(request.url.path)
        }
    )


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    """500 에러 커스텀 처리"""
    logger.error(f"내부 서버 오류: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "서버 내부 오류가 발생했습니다.",
            "message": "잠시 후 다시 시도해주세요."
        }
    )


# 개발 모드에서만 사용하는 엔드포인트
if settings.DEBUG:
    @app.get("/api/test")
    async def test_endpoint():
        """테스트 엔드포인트"""
        return {
            "message": "테스트 성공!",
            "gemini_configured": bool(settings.GEMINI_API_KEY),
            "environment": "development"
        }


if __name__ == "__main__":
    # 개발 서버 실행 (프로덕션에서는 gunicorn 사용)
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="debug" if settings.DEBUG else "info"
    )
