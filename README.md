# 🎥 YouTube Translator - 영어 → 한국어 번역 서비스

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Deploy](https://github.com/yourusername/youtube-translator/actions/workflows/deploy.yml/badge.svg)](https://github.com/yourusername/youtube-translator/actions)

영어 YouTube 영상을 한국어로 번역하는 웹 서비스입니다. Gemini API를 활용하여 고품질 번역을 제공합니다.

## 🌟 주요 기능

- 🔗 YouTube URL 입력만으로 간편하게 번역
- 🤖 Google Gemini API를 활용한 정확한 번역
- 📝 전체 스크립트 번역 및 요약 제공
- 💾 번역 결과 다운로드 기능
- 🎨 반응형 웹 디자인

## 🚀 빠른 시작

### 1. 프로젝트 클론

```bash
git clone https://github.com/yourusername/youtube-translator.git
cd youtube-translator
```

### 2. 가상환경 설정

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Mac/Linux
python -m venv venv
source venv/bin/activate
```

### 3. 패키지 설치

```bash
pip install -r requirements.txt
```

### 4. 환경 변수 설정

```bash
# .env.example을 복사하여 .env 파일 생성
cp .env.example .env

# .env 파일을 열어 API 키 입력
# GEMINI_API_KEY=your_api_key_here
```

### 5. 서버 실행

```bash
# 개발 서버
uvicorn app.main:app --reload

# 프로덕션 서버
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

브라우저에서 http://localhost:8000 접속

## 📋 환경 변수

`.env` 파일에 다음 변수들을 설정하세요:

```env
# 필수
GEMINI_API_KEY=your_gemini_api_key

# 선택
PORT=8000
DEBUG=True
MAX_VIDEO_LENGTH=3600  # 초 단위 (기본: 1시간)
CACHE_TTL=86400       # 캐시 유효시간 (기본: 24시간)
```

## 🛠️ 기술 스택

- **Backend**: FastAPI, Python 3.9+
- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **API**: Google Gemini API
- **Deployment**: Docker, GitHub Actions
- **Testing**: pytest, pytest-asyncio

## 📁 프로젝트 구조

```
├── app/                    # 애플리케이션 코드
│   ├── main.py            # FastAPI 앱
│   ├── config.py          # 설정 관리
│   ├── models.py          # Pydantic 모델
│   ├── services/          # 비즈니스 로직
│   └── static/            # 정적 파일
├── tests/                 # 테스트 코드
├── .github/workflows/     # GitHub Actions
└── docker-compose.yml     # Docker 설정
```

## 🐳 Docker로 실행

### Docker Compose 사용

```bash
# 빌드 및 실행
docker-compose up -d

# 로그 확인
docker-compose logs -f

# 종료
docker-compose down
```

### Docker 직접 사용

```bash
# 이미지 빌드
docker build -t youtube-translator .

# 컨테이너 실행
docker run -d -p 8000:8000 --env-file .env youtube-translator
```

## 🧪 테스트

```bash
# 전체 테스트 실행
pytest

# 커버리지 포함
pytest --cov=app

# 특정 테스트만 실행
pytest tests/test_translator.py
```

## 📊 API 문서

서버 실행 후 다음 URL에서 API 문서를 확인할 수 있습니다:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 주요 엔드포인트

```http
POST /api/translate
Content-Type: application/json

{
  "youtube_url": "https://www.youtube.com/watch?v=..."
}
```

응답:
```json
{
  "translation": "번역된 텍스트...",
  "video_title": "영상 제목",
  "duration": "10:30",
  "translated_at": "2024-01-15T10:30:00"
}
```

## 🔧 개발 가이드

### 코드 스타일

```bash
# 코드 포맷팅
black app/

# 린팅
flake8 app/

# 타입 체크
mypy app/
```

### 새 기능 추가하기

1. `feature/기능명` 브랜치 생성
2. 코드 작성 및 테스트 추가
3. PR 생성 및 리뷰 요청

## 🚀 배포

### GitHub Actions (자동 배포)

`main` 브랜치에 푸시하면 자동으로 배포됩니다.

### 수동 배포

1. **AWS EC2**
   ```bash
   # 인스턴스 접속
   ssh ubuntu@your-server.com
   
   # 코드 업데이트
   git pull origin main
   
   # 서비스 재시작
   sudo systemctl restart youtube-translator
   ```

2. **Heroku**
   ```bash
   heroku create youtube-translator-kr
   heroku config:set GEMINI_API_KEY=your_key
   git push heroku main
   ```

## 🤝 기여하기

1. Fork 하기
2. Feature 브랜치 생성 (`git checkout -b feature/AmazingFeature`)
3. 변경사항 커밋 (`git commit -m 'Add some AmazingFeature'`)
4. 브랜치에 푸시 (`git push origin feature/AmazingFeature`)
5. Pull Request 생성

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 있습니다. 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.

## 👥 만든 사람

- **Your Name** - *Initial work* - [YourGitHub](https://github.com/yourusername)

## 🙏 감사의 말

- Google Gemini API 팀
- FastAPI 커뮤니티
- 모든 기여자들

## 📞 문의

- 이메일: your.email@example.com
- 이슈: https://github.com/yourusername/youtube-translator/issues

---

⭐ 이 프로젝트가 도움이 되었다면 Star를 눌러주세요!
