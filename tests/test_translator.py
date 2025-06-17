"""
YouTube Translator 테스트 코드
pytest를 사용하여 핵심 기능들을 테스트합니다.

실행 방법:
- 전체 테스트: pytest
- 특정 테스트: pytest tests/test_translator.py::test_translate_success
- 커버리지 포함: pytest --cov=app
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
from fastapi.testclient import TestClient
import json

from app.main import app
from app.models import TranslateRequest, TranslateResponse, TranslationStatus
from app.services.translator import TranslatorService
from app.config import settings


# ===========================
# Fixtures (테스트 데이터)
# ===========================

@pytest.fixture
def test_client():
    """테스트용 FastAPI 클라이언트"""
    return TestClient(app)


@pytest.fixture
def valid_youtube_url():
    """유효한 YouTube URL"""
    return "https://www.youtube.com/watch?v=dQw4w9WgXcQ"


@pytest.fixture
def invalid_youtube_url():
    """유효하지 않은 URL"""
    return "https://not-youtube.com/video"


@pytest.fixture
def mock_translation_response():
    """모의 번역 응답"""
    return {
        "status": TranslationStatus.COMPLETED,
        "youtube_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "translation": "안녕하세요. 이것은 번역된 텍스트입니다.",
        "summary": "테스트 요약입니다.",
        "video_title": "Test Video",
        "video_duration": "10:30",
        "channel_name": "Test Channel",
        "translated_at": datetime.now(),
        "processing_time": 3.5,
        "word_count": 100,
        "confidence_score": 0.95
    }


@pytest.fixture
def mock_gemini_response():
    """모의 Gemini API 응답"""
    return """
=== 영상 정보 ===
제목: 테스트 비디오
채널: 테스트 채널
길이: 10:30

=== 요약 ===
이것은 테스트 영상의 요약입니다.

=== 전체 번역 ===
안녕하세요. 이것은 번역된 텍스트입니다.
"""


# ===========================
# API 엔드포인트 테스트
# ===========================

def test_health_check(test_client):
    """헬스체크 엔드포인트 테스트"""
    response = test_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "gemini_configured" in data


def test_main_page(test_client):
    """메인 페이지 접속 테스트"""
    response = test_client.get("/")
    assert response.status_code == 200
    assert "YouTube Translator" in response.text


@patch('app.services.translator.TranslatorService.translate')
async def test_translate_endpoint_success(mock_translate, test_client, valid_youtube_url, mock_translation_response):
    """번역 API 성공 케이스"""
    # Mock 설정
    mock_translate.return_value = AsyncMock(return_value=TranslateResponse(**mock_translation_response))
    
    # API 호출
    response = test_client.post(
        "/api/translate",
        json={"youtube_url": valid_youtube_url}
    )
    
    # 검증
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    assert data["translation"] is not None
    assert data["youtube_url"] == valid_youtube_url


def test_translate_endpoint_invalid_url(test_client, invalid_youtube_url):
    """잘못된 URL로 번역 요청"""
    response = test_client.post(
        "/api/translate",
        json={"youtube_url": invalid_youtube_url}
    )
    
    assert response.status_code == 422  # Validation Error


def test_translate_endpoint_missing_url(test_client):
    """URL 없이 번역 요청"""
    response = test_client.post(
        "/api/translate",
        json={}
    )
    
    assert response.status_code == 422


# ===========================
# TranslatorService 테스트
# ===========================

class TestTranslatorService:
    """번역 서비스 단위 테스트"""
    
    @pytest.fixture
    def translator_service(self):
        """번역 서비스 인스턴스"""
        with patch('app.config.settings.GEMINI_API_KEY', 'test-key'):
            return TranslatorService()
    
    def test_is_valid_youtube_url(self, translator_service):
        """YouTube URL 유효성 검사 테스트"""
        # 유효한 URL들
        valid_urls = [
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "https://youtu.be/dQw4w9WgXcQ",
            "https://m.youtube.com/watch?v=dQw4w9WgXcQ",
            "http://youtube.com/watch?v=dQw4w9WgXcQ",
            "https://www.youtube.com/embed/dQw4w9WgXcQ"
        ]
        
        for url in valid_urls:
            assert translator_service.is_valid_youtube_url(url) is True
        
        # 유효하지 않은 URL들
        invalid_urls = [
            "https://vimeo.com/123456",
            "https://www.google.com",
            "not-a-url",
            "https://youtube.com/",
            ""
        ]
        
        for url in invalid_urls:
            assert translator_service.is_valid_youtube_url(url) is False
    
    def test_extract_video_id(self, translator_service):
        """비디오 ID 추출 테스트"""
        test_cases = [
            ("https://www.youtube.com/watch?v=dQw4w9WgXcQ", "dQw4w9WgXcQ"),
            ("https://youtu.be/dQw4w9WgXcQ", "dQw4w9WgXcQ"),
            ("https://www.youtube.com/embed/dQw4w9WgXcQ", "dQw4w9WgXcQ"),
            ("https://m.youtube.com/watch?v=dQw4w9WgXcQ&t=10s", "dQw4w9WgXcQ"),
        ]
        
        for url, expected_id in test_cases:
            assert translator_service.extract_video_id(url) == expected_id
        
        # ID를 추출할 수 없는 경우
        assert translator_service.extract_video_id("https://youtube.com") is None
    
    def test_generate_cache_key(self, translator_service):
        """캐시 키 생성 테스트"""
        url = "https://www.youtube.com/watch?v=test123"
        key1 = translator_service._generate_cache_key(url)
        key2 = translator_service._generate_cache_key(url)
        
        # 같은 URL은 같은 키 생성
        assert key1 == key2
        assert key1.startswith("yt_translation:")
        
        # 다른 URL은 다른 키 생성
        different_url = "https://www.youtube.com/watch?v=different"
        key3 = translator_service._generate_cache_key(different_url)
        assert key1 != key3
    
    @patch('google.generativeai.GenerativeModel.generate_content')
    async def test_translate_success(self, mock_generate, translator_service, valid_youtube_url, mock_gemini_response):
        """번역 성공 테스트"""
        # Mock 설정
        mock_response = Mock()
        mock_response.text = mock_gemini_response
        mock_generate.return_value = mock_response
        
        # 번역 실행
        result = await translator_service.translate(valid_youtube_url)
        
        # 검증
        assert result.status == TranslationStatus.COMPLETED
        assert result.youtube_url == valid_youtube_url
        assert result.translation is not None
        assert "안녕하세요" in result.translation
    
    async def test_translate_invalid_url(self, translator_service, invalid_youtube_url):
        """잘못된 URL로 번역 시도"""
        with pytest.raises(ValueError, match="유효하지 않은 YouTube URL"):
            await translator_service.translate(invalid_youtube_url)
    
    def test_parse_translation_response(self, translator_service, mock_gemini_response, valid_youtube_url):
        """응답 파싱 테스트"""
        parsed = translator_service._parse_translation_response(
            mock_gemini_response,
            valid_youtube_url
        )
        
        assert parsed["status"] == TranslationStatus.COMPLETED
        assert parsed["video_title"] == "테스트 비디오"
        assert parsed["channel_name"] == "테스트 채널"
        assert parsed["video_duration"] == "10:30"
        assert "테스트 영상의 요약" in parsed["summary"]
        assert parsed["word_count"] > 0
    
    def test_estimate_translation_time(self, translator_service):
        """번역 시간 예측 테스트"""
        # 1분 영상
        time_1min = translator_service.estimate_translation_time(60)
        assert 2 <= time_1min <= 5
        
        # 10분 영상
        time_10min = translator_service.estimate_translation_time(600)
        assert 20 <= time_10min <= 30
        
        # 최대값 테스트
        time_max = translator_service.estimate_translation_time(3600)
        assert time_max <= 30  # 최대 30초


# ===========================
# 모델 테스트
# ===========================

class TestModels:
    """Pydantic 모델 테스트"""
    
    def test_translate_request_valid(self, valid_youtube_url):
        """유효한 번역 요청 모델"""
        request = TranslateRequest(youtube_url=valid_youtube_url)
        assert str(request.youtube_url) == valid_youtube_url
        assert request.target_language == "ko"  # 기본값
        assert request.include_summary is True  # 기본값
    
    def test_translate_request_invalid_url(self):
        """잘못된 URL로 요청 모델 생성"""
        with pytest.raises(ValueError):
            TranslateRequest(youtube_url="not-a-url")
    
    def test_translate_response(self, mock_translation_response):
        """번역 응답 모델"""
        response = TranslateResponse(**mock_translation_response)
        assert response.status == TranslationStatus.COMPLETED
        assert response.translation is not None
        assert response.word_count == 100
        
        # 메서드 테스트
        dict_data = response.to_dict()
        assert isinstance(dict_data, dict)
        assert dict_data["status"] == "completed"


# ===========================
# 통합 테스트
# ===========================

@pytest.mark.integration
class TestIntegration:
    """통합 테스트 (실제 서비스 호출)"""
    
    @pytest.mark.skipif(not settings.GEMINI_API_KEY, reason="Gemini API key not set")
    async def test_real_translation(self, test_client, valid_youtube_url):
        """실제 API를 사용한 번역 테스트"""
        response = test_client.post(
            "/api/translate",
            json={"youtube_url": valid_youtube_url},
            timeout=30
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert len(data["translation"]) > 0


# ===========================
# 성능 테스트
# ===========================

@pytest.mark.performance
class TestPerformance:
    """성능 테스트"""
    
    def test_cache_performance(self, translator_service):
        """캐시 성능 테스트"""
        import time
        
        url = "https://www.youtube.com/watch?v=test"
        
        # 첫 번째 호출 (캐시 미스)
        start = time.time()
        key1 = translator_service._generate_cache_key(url)
        time1 = time.time() - start
        
        # 두 번째 호출 (이미 계산됨)
        start = time.time()
        key2 = translator_service._generate_cache_key(url)
        time2 = time.time() - start
        
        assert key1 == key2
        assert time2 < time1  # 두 번째가 더 빨라야 함


# ===========================
# 유틸리티 함수
# ===========================

def test_format_duration():
    """시간 포맷팅 테스트"""
    # 여기에 실제 포맷팅 함수가 있다면 테스트
    pass


# 실행: pytest -v tests/test_translator.py
