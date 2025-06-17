"""
app.py - Render.com 배포를 위한 엔트리 포인트
이 파일은 gunicorn app:app 명령어가 올바르게 작동하도록 합니다.
Render.com은 기본적으로 'gunicorn app:app'을 실행하므로,
app.py 파일에서 FastAPI 앱을 import해야 합니다.
"""

# app 패키지의 main 모듈에서 FastAPI 인스턴스를 가져옵니다
from app.main import app

# gunicorn이 찾을 수 있도록 app 변수를 노출합니다
# 이제 'gunicorn app:app'이 이 파일의 app 변수를 찾을 수 있습니다
__all__ = ['app']  # ✅ 언더스코어 2개씩!

# 개발 환경에서 직접 실행할 때 사용
if __name__ == "__main__":  # ✅ 언더스코어 2개씩!
    import uvicorn
    import os
    
    # 환경 변수에서 포트 가져오기 (기본값: 8000)
    port = int(os.getenv("PORT", 8000))
    
    # 개발 서버 실행
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        reload=True,  # 개발 시 자동 리로드
        log_level="debug"
    )
