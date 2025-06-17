# 🚀 YouTube Translator 빠른 시작 가이드

5분 안에 YouTube 번역 서비스를 시작하세요!

## 📋 체크리스트

- [ ] Python 3.9 이상 설치
- [ ] Git 설치
- [ ] Gemini API 키 발급

## 🎯 3단계로 시작하기

### 1️⃣ 프로젝트 클론 및 설정 (1분)

```bash
# 프로젝트 클론
git clone https://github.com/yourusername/youtube-translator.git
cd youtube-translator

# 자동 설정 (Makefile 사용)
make setup
```

### 2️⃣ API 키 설정 (1분)

1. [Google AI Studio](https://makersuite.google.com/app/apikey)에서 API 키 발급
2. `.env` 파일 열기
3. `GEMINI_API_KEY=your_api_key_here` 부분에 API 키 입력

```bash
# .env 파일 편집
nano .env
# 또는
code .env  # VS Code 사용 시
```

### 3️⃣ 서버 실행 (30초)

```bash
# 개발 서버 실행
make dev

# 또는 직접 실행
uvicorn app.main:app --reload
```

브라우저에서 http://localhost:8000 접속!

## 🎉 완료!

이제 YouTube URL을 입력하고 번역을 시작하세요!

## 📚 다음 단계

### 테스트 실행
```bash
make test
```

### Docker로 실행
```bash
make docker-build
make docker-run
```

### 전체 스택 실행 (Redis, PostgreSQL 포함)
```bash
docker-compose up -d
```

## 🆘 문제 해결

### "ModuleNotFoundError" 오류
```bash
# 가상환경 활성화 확인
source venv/bin/activate  # Mac/Linux
venv\Scripts\activate     # Windows
```

### "GEMINI_API_KEY not found" 오류
```bash
# .env 파일 확인
cat .env
# GEMINI_API_KEY가 설정되어 있는지 확인
```

### 포트 충돌 (8000번 포트 사용 중)
```bash
# 다른 포트로 실행
make dev PORT=8080
# 또는
uvicorn app.main:app --reload --port 8080
```

## 🔧 유용한 명령어

| 명령어 | 설명 |
|--------|------|
| `make help` | 사용 가능한 모든 명령어 보기 |
| `make test` | 테스트 실행 |
| `make format` | 코드 자동 포맷팅 |
| `make clean` | 캐시 정리 |
| `make logs` | 로그 확인 |

## 📖 추가 문서

- [전체 README](README.md)
- [API 문서](http://localhost:8000/docs)
- [환경 변수 설명](.env.example)

---

💡 **팁**: VS Code 사용자는 Python 확장을 설치하면 더 편리합니다!

🐛 **버그 발견?** [이슈 등록](https://github.com/yourusername/youtube-translator/issues)

⭐ **마음에 드셨나요?** GitHub에 Star를 눌러주세요!
