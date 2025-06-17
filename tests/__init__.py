"""
YouTube Translator 테스트 패키지

이 패키지는 애플리케이션의 모든 테스트를 포함합니다.

테스트 구조:
- test_translator.py: 번역 서비스 테스트
- test_api.py: API 엔드포인트 테스트 (추가 가능)
- test_models.py: 데이터 모델 테스트 (추가 가능)

테스트 실행:
    pytest                    # 전체 테스트
    pytest -v                # 상세 출력
    pytest --cov=app         # 커버리지 포함
    pytest -k "test_name"    # 특정 테스트만
"""

import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
# 이렇게 하면 테스트에서 app 모듈을 임포트할 수 있습니다
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
