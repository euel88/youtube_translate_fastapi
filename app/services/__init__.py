"""
YouTube Translator 서비스 패키지

이 패키지는 애플리케이션의 핵심 비즈니스 로직을 포함합니다.
각 서비스는 독립적으로 동작하며, 필요에 따라 확장 가능합니다.

현재 서비스:
- translator: YouTube 영상 번역 서비스 (Gemini API 사용)

향후 추가 가능한 서비스:
- cache: 캐싱 서비스
- auth: 인증 서비스
- analytics: 분석 서비스
"""

from app.services.translator import TranslatorService

__all__ = [
    "TranslatorService",
]

# 서비스 인스턴스 생성 (싱글톤 패턴)
# 애플리케이션 전체에서 하나의 인스턴스만 사용
_translator_instance = None


def get_translator_service() -> TranslatorService:
    """
    번역 서비스 인스턴스를 반환합니다.
    
    싱글톤 패턴을 사용하여 애플리케이션 전체에서
    하나의 인스턴스만 생성되도록 보장합니다.
    
    Returns:
        TranslatorService: 번역 서비스 인스턴스
    """
    global _translator_instance
    
    if _translator_instance is None:
        _translator_instance = TranslatorService()
    
    return _translator_instance
