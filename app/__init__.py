"""
YouTube Translator FastAPI 애플리케이션
영어 YouTube 영상을 한국어로 번역하는 서비스

Author: YouTube Translator Team
Version: 1.0.0
"""

# 버전 정보
__version__ = "1.0.0"
__author__ = "YouTube Translator Team"

# 패키지 초기화
# 이 파일이 있어야 Python이 app 디렉토리를 패키지로 인식합니다
import logging

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# 중요: 순환 import 방지를 위해 여기서는 다른 모듈을 import하지 않습니다
# from app.config import settings  # 이렇게 하면 순환 import 오류 발생 가능!
