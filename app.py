# app.py - 프로젝트 루트에 생성
"""
Render.com이 app:app을 찾을 수 있도록 하는 엔트리 포인트
render.yaml이 무시될 경우를 위한 백업
"""
from app.main import app

# gunicorn이 찾을 수 있도록 app 변수 노출
__all__ = ['app']

# 개발 환경에서 직접 실행 가능
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True
    )
