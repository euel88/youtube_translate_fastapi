"""
YouTube 번역 서비스 핵심 로직
Gemini API를 사용하여 YouTube 영상을 번역합니다.

이 모듈은 전체 애플리케이션의 핵심입니다!
"""

import google.generativeai as genai
from typing import Optional, Dict, Any
import re
import time
import hashlib
import json
from datetime import datetime
import asyncio
from functools import lru_cache
import logging

from app.config import settings
from app.models import TranslateResponse, TranslationStatus

# 로깅 설정
logger = logging.getLogger(__name__)


class TranslatorService:
    """
    YouTube 영상 번역 서비스 클래스
    
    이 클래스가 실제 번역 작업을 수행합니다.
    Gemini API와 통신하고, 캐싱을 관리하며, 에러를 처리합니다.
    """
    
    def __init__(self):
        """서비스 초기화"""
        # Gemini API 설정
        if not settings.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY가 설정되지 않았습니다!")
        
        genai.configure(api_key=settings.GEMINI_API_KEY)
        
        # 모델 초기화
        self.model = genai.GenerativeModel(
            settings.GEMINI_MODEL,
            generation_config=genai.GenerationConfig(
                temperature=settings.GEMINI_TEMPERATURE,
                max_output_tokens=settings.GEMINI_MAX_OUTPUT_TOKENS,
            )
        )
        
        # 캐시 초기화 (Redis 또는 메모리)
        self.cache = self._initialize_cache()
        
        logger.info(f"✅ 번역 서비스 초기화 완료 - 모델: {settings.GEMINI_MODEL}")
    
    def _initialize_cache(self) -> Optional[Any]:
        """캐시 초기화 - Redis 사용 가능하면 Redis, 아니면 메모리 캐시"""
        if not settings.CACHE_ENABLED:
            return None
            
        redis_client = settings.get_redis_client()
        if redis_client:
            logger.info("📦 Redis 캐시 사용")
            return redis_client
        else:
            logger.info("💾 메모리 캐시 사용")
            return {}  # 간단한 딕셔너리 캐시
    
    @staticmethod
    def is_valid_youtube_url(url: str) -> bool:
        """
        YouTube URL 유효성 검사
        
        Args:
            url: 검사할 URL
            
        Returns:
            bool: 유효한 YouTube URL인지 여부
        """
        # YouTube URL 패턴
        youtube_regex = re.compile(
            r'(https?://)?(www\.)?(youtube\.com/(watch\?v=|embed/|v/)|youtu\.be/|m\.youtube\.com/watch\?v=)[\w-]+',
            re.IGNORECASE
        )
        return bool(youtube_regex.match(url))
    
    @staticmethod
    def extract_video_id(url: str) -> Optional[str]:
        """
        YouTube URL에서 비디오 ID 추출
        
        Args:
            url: YouTube URL
            
        Returns:
            str: 비디오 ID 또는 None
        """
        # 다양한 YouTube URL 형식 지원
        patterns = [
            r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
            r'(?:embed\/)([0-9A-Za-z_-]{11})',
            r'(?:watch\?v=)([0-9A-Za-z_-]{11})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None
    
    def _generate_cache_key(self, url: str) -> str:
        """
        URL로부터 캐시 키 생성
        
        Args:
            url: YouTube URL
            
        Returns:
            str: 캐시 키
        """
        # URL을 해시하여 캐시 키 생성
        return f"yt_translation:{hashlib.md5(url.encode()).hexdigest()}"
    
    async def _get_from_cache(self, url: str) -> Optional[Dict[str, Any]]:
        """
        캐시에서 번역 결과 조회
        
        Args:
            url: YouTube URL
            
        Returns:
            dict: 캐시된 번역 결과 또는 None
        """
        if not self.cache:
            return None
        
        cache_key = self._generate_cache_key(url)
        
        try:
            if isinstance(self.cache, dict):
                # 메모리 캐시
                return self.cache.get(cache_key)
            else:
                # Redis 캐시
                cached = self.cache.get(cache_key)
                if cached:
                    return json.loads(cached)
        except Exception as e:
            logger.error(f"캐시 조회 실패: {e}")
        
        return None
    
    async def _save_to_cache(self, url: str, data: Dict[str, Any]):
        """
        번역 결과를 캐시에 저장
        
        Args:
            url: YouTube URL
            data: 저장할 데이터
        """
        if not self.cache:
            return
        
        cache_key = self._generate_cache_key(url)
        
        try:
            if isinstance(self.cache, dict):
                # 메모리 캐시
                self.cache[cache_key] = data
            else:
                # Redis 캐시 (TTL 설정)
                self.cache.setex(
                    cache_key,
                    settings.CACHE_TTL,
                    json.dumps(data, ensure_ascii=False, default=str)
                )
            
            logger.info(f"✅ 캐시 저장 완료: {cache_key}")
        except Exception as e:
            logger.error(f"캐시 저장 실패: {e}")
    
    def _create_translation_prompt(self, url: str) -> str:
        """
        번역 프롬프트 생성
        
        Args:
            url: YouTube URL
            
        Returns:
            str: Gemini API용 프롬프트
        """
        prompt = f"""
다음 YouTube 영상의 음성을 한국어로 번역해주세요.

YouTube URL: {url}

번역 요구사항:
1. 영상의 전체 내용을 빠짐없이 번역해주세요.
2. 문맥을 고려하여 자연스러운 한국어로 번역해주세요.
3. 전문 용어는 정확하게 번역하되, 필요시 영어를 병기해주세요. 예: 머신러닝(Machine Learning)
4. 화자가 여러 명인 경우, [화자 1], [화자 2] 등으로 구분해주세요.
5. 중요한 내용은 **굵게** 표시해주세요.
6. 시간 표시가 가능한 경우 [00:00] 형식으로 표시해주세요.

추가로 다음 정보도 포함해주세요:
- 영상 제목 (한국어로 번역)
- 채널 이름
- 영상 길이
- 핵심 내용 3줄 요약

번역 형식:
=== 영상 정보 ===
제목: [번역된 제목]
채널: [채널명]
길이: [영상 길이]

=== 요약 ===
[3줄 요약]

=== 전체 번역 ===
[전체 내용 번역]
"""
        return prompt
    
    async def translate(self, youtube_url: str) -> TranslateResponse:
        """
        YouTube 영상 번역 - 메인 함수
        
        Args:
            youtube_url: 번역할 YouTube URL
            
        Returns:
            TranslateResponse: 번역 결과
            
        Raises:
            ValueError: 잘못된 URL 또는 번역 실패
        """
        start_time = time.time()
        
        # 1. URL 유효성 검사
        if not self.is_valid_youtube_url(youtube_url):
            raise ValueError("유효하지 않은 YouTube URL입니다.")
        
        # 2. 캐시 확인
        cached_result = await self._get_from_cache(youtube_url)
        if cached_result:
            logger.info("✨ 캐시에서 결과 반환")
            return TranslateResponse(**cached_result)
        
        # 3. Gemini API로 번역 요청
        try:
            logger.info(f"🔄 번역 시작: {youtube_url}")
            
            # 프롬프트 생성
            prompt = self._create_translation_prompt(youtube_url)
            
            # API 호출 (속도 제한 고려)
            response = await self._call_gemini_api(prompt)
            
            # 응답 파싱
            parsed_result = self._parse_translation_response(response, youtube_url)
            
            # 처리 시간 추가
            parsed_result['processing_time'] = time.time() - start_time
            
            # 캐시에 저장
            await self._save_to_cache(youtube_url, parsed_result)
            
            logger.info(f"✅ 번역 완료 - 소요시간: {parsed_result['processing_time']:.2f}초")
            
            return TranslateResponse(**parsed_result)
            
        except Exception as e:
            logger.error(f"번역 실패: {str(e)}")
            raise ValueError(f"번역 처리 중 오류가 발생했습니다: {str(e)}")
    
    async def _call_gemini_api(self, prompt: str) -> str:
        """
        Gemini API 호출 (속도 제한 처리 포함)
        
        Args:
            prompt: API에 전송할 프롬프트
            
        Returns:
            str: API 응답 텍스트
        """
        max_retries = 3
        retry_delay = 1.0
        
        for attempt in range(max_retries):
            try:
                # 비동기로 실행
                response = await asyncio.to_thread(
                    self.model.generate_content,
                    prompt
                )
                
                return response.text
                
            except Exception as e:
                logger.warning(f"API 호출 실패 (시도 {attempt + 1}/{max_retries}): {e}")
                
                if "quota" in str(e).lower():
                    raise ValueError("API 사용량을 초과했습니다. 잠시 후 다시 시도해주세요.")
                
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2  # 지수 백오프
                else:
                    raise
    
    def _parse_translation_response(self, response_text: str, youtube_url: str) -> Dict[str, Any]:
        """
        Gemini API 응답을 파싱하여 구조화된 데이터로 변환
        
        Args:
            response_text: API 응답 텍스트
            youtube_url: 원본 YouTube URL
            
        Returns:
            dict: 파싱된 번역 결과
        """
        # 기본 결과 구조
        result = {
            'status': TranslationStatus.COMPLETED,
            'youtube_url': youtube_url,
            'translation': response_text,
            'translated_at': datetime.now()
        }
        
        # 응답에서 구조화된 정보 추출 시도
        try:
            # 영상 정보 추출
            title_match = re.search(r'제목:\s*(.+)', response_text)
            if title_match:
                result['video_title'] = title_match.group(1).strip()
            
            channel_match = re.search(r'채널:\s*(.+)', response_text)
            if channel_match:
                result['channel_name'] = channel_match.group(1).strip()
            
            duration_match = re.search(r'길이:\s*(.+)', response_text)
            if duration_match:
                result['video_duration'] = duration_match.group(1).strip()
            
            # 요약 추출
            summary_match = re.search(r'=== 요약 ===\n([\s\S]*?)\n=== 전체 번역 ===', response_text)
            if summary_match:
                result['summary'] = summary_match.group(1).strip()
            
            # 단어 수 계산
            korean_text = re.sub(r'[^\w\s]', '', response_text)
            result['word_count'] = len(korean_text.split())
            
            # 신뢰도 점수 (간단한 휴리스틱)
            result['confidence_score'] = min(0.95, len(response_text) / 10000)
            
        except Exception as e:
            logger.warning(f"응답 파싱 중 일부 오류: {e}")
        
        return result
    
    @lru_cache(maxsize=100)
    def estimate_translation_time(self, video_duration_seconds: int) -> float:
        """
        영상 길이를 기반으로 번역 소요 시간 예측
        
        Args:
            video_duration_seconds: 영상 길이 (초)
            
        Returns:
            float: 예상 소요 시간 (초)
        """
        # 경험적 공식: 영상 1분당 약 2-3초 소요
        base_time = 2.0  # 기본 오버헤드
        per_minute_time = 2.5
        
        minutes = video_duration_seconds / 60
        estimated_time = base_time + (minutes * per_minute_time)
        
        return min(estimated_time, 30.0)  # 최대 30초로 제한
    
    async def translate_batch(self, youtube_urls: list[str]) -> list[TranslateResponse]:
        """
        여러 영상을 일괄 번역 (병렬 처리)
        
        Args:
            youtube_urls: YouTube URL 목록
            
        Returns:
            list: 번역 결과 목록
        """
        logger.info(f"📦 일괄 번역 시작 - {len(youtube_urls)}개 영상")
        
        # 동시 실행 제한 (API 속도 제한 고려)
        semaphore = asyncio.Semaphore(3)  # 동시에 3개까지만
        
        async def translate_with_semaphore(url: str) -> TranslateResponse:
            async with semaphore:
                try:
                    return await self.translate(url)
                except Exception as e:
                    logger.error(f"일괄 번역 중 오류 ({url}): {e}")
                    return TranslateResponse(
                        status=TranslationStatus.FAILED,
                        youtube_url=url,
                        translation=f"번역 실패: {str(e)}",
                        translated_at=datetime.now()
                    )
        
        # 모든 번역 작업을 병렬로 실행
        tasks = [translate_with_semaphore(url) for url in youtube_urls]
        results = await asyncio.gather(*tasks)
        
        logger.info(f"✅ 일괄 번역 완료 - 성공: {sum(1 for r in results if r.status == TranslationStatus.COMPLETED)}개")
        
        return results


# 💡 초보자를 위한 사용 예시
"""
# 기본 사용법
translator = TranslatorService()

# 단일 영상 번역
result = await translator.translate("https://youtube.com/watch?v=...")
print(result.translation)

# 일괄 번역
urls = ["url1", "url2", "url3"]
results = await translator.translate_batch(urls)

# 캐시 활용
# 같은 URL을 다시 번역하면 캐시에서 즉시 반환됩니다!
"""
