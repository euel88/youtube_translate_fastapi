# YouTube Translator Makefile
# 프로젝트 관리를 위한 자동화 스크립트

# 변수 정의
PYTHON := python3
PIP := pip3
PROJECT_NAME := youtube-translator
DOCKER_IMAGE := $(PROJECT_NAME):latest
PORT := 8000

# 색상 정의 (터미널 출력용)
GREEN := \033[0;32m
RED := \033[0;31m
YELLOW := \033[0;33m
NC := \033[0m # No Color

# 기본 타겟
.DEFAULT_GOAL := help

# ===========================
# 도움말
# ===========================
.PHONY: help
help: ## 도움말 표시
	@echo "$(GREEN)YouTube Translator - 사용 가능한 명령어$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "$(YELLOW)%-20s$(NC) %s\n", $$1, $$2}'

# ===========================
# 개발 환경 설정
# ===========================
.PHONY: setup
setup: ## 개발 환경 초기 설정
	@echo "$(GREEN)개발 환경 설정 시작...$(NC)"
	$(PYTHON) -m venv venv
	. venv/bin/activate && $(PIP) install --upgrade pip
	. venv/bin/activate && $(PIP) install -r requirements.txt
	cp .env.example .env
	@echo "$(GREEN)✅ 설정 완료! .env 파일에 API 키를 입력하세요.$(NC)"

.PHONY: install
install: ## 의존성 설치
	@echo "$(GREEN)의존성 설치 중...$(NC)"
	$(PIP) install -r requirements.txt

.PHONY: install-dev
install-dev: ## 개발 의존성 포함 설치
	@echo "$(GREEN)개발 의존성 설치 중...$(NC)"
	$(PIP) install -r requirements.txt
	$(PIP) install pytest pytest-cov pytest-asyncio black flake8 mypy

# ===========================
# 개발 서버
# ===========================
.PHONY: dev
dev: ## 개발 서버 실행 (자동 리로드)
	@echo "$(GREEN)개발 서버 시작... (http://localhost:$(PORT))$(NC)"
	uvicorn app.main:app --reload --port $(PORT)

.PHONY: run
run: ## 프로덕션 서버 실행
	@echo "$(GREEN)프로덕션 서버 시작...$(NC)"
	gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$(PORT)

# ===========================
# 테스트
# ===========================
.PHONY: test
test: ## 테스트 실행
	@echo "$(GREEN)테스트 실행 중...$(NC)"
	pytest tests/ -v

.PHONY: test-cov
test-cov: ## 커버리지 포함 테스트
	@echo "$(GREEN)커버리지 테스트 실행 중...$(NC)"
	pytest tests/ -v --cov=app --cov-report=html --cov-report=term

.PHONY: test-watch
test-watch: ## 파일 변경 시 자동 테스트
	@echo "$(GREEN)자동 테스트 모드...$(NC)"
	ptw tests/ -- -v

# ===========================
# 코드 품질
# ===========================
.PHONY: format
format: ## 코드 포맷팅 (Black)
	@echo "$(GREEN)코드 포맷팅 중...$(NC)"
	black app/ tests/

.PHONY: lint
lint: ## 코드 린팅 (Flake8)
	@echo "$(GREEN)코드 린팅 중...$(NC)"
	flake8 app/ tests/ --max-line-length=100 --exclude=__pycache__

.PHONY: type
type: ## 타입 체크 (mypy)
	@echo "$(GREEN)타입 체크 중...$(NC)"
	mypy app/ --ignore-missing-imports

.PHONY: quality
quality: format lint type ## 전체 코드 품질 검사

# ===========================
# Docker
# ===========================
.PHONY: docker-build
docker-build: ## Docker 이미지 빌드
	@echo "$(GREEN)Docker 이미지 빌드 중...$(NC)"
	docker build -t $(DOCKER_IMAGE) .

.PHONY: docker-run
docker-run: ## Docker 컨테이너 실행
	@echo "$(GREEN)Docker 컨테이너 시작...$(NC)"
	docker run -d -p $(PORT):$(PORT) --env-file .env --name $(PROJECT_NAME) $(DOCKER_IMAGE)

.PHONY: docker-stop
docker-stop: ## Docker 컨테이너 중지
	@echo "$(RED)Docker 컨테이너 중지...$(NC)"
	docker stop $(PROJECT_NAME) && docker rm $(PROJECT_NAME)

.PHONY: docker-logs
docker-logs: ## Docker 로그 확인
	docker logs -f $(PROJECT_NAME)

# ===========================
# Docker Compose
# ===========================
.PHONY: up
up: ## Docker Compose 시작
	@echo "$(GREEN)전체 스택 시작...$(NC)"
	docker-compose up -d

.PHONY: down
down: ## Docker Compose 중지
	@echo "$(RED)전체 스택 중지...$(NC)"
	docker-compose down

.PHONY: logs
logs: ## 전체 로그 확인
	docker-compose logs -f

.PHONY: ps
ps: ## 실행 중인 서비스 확인
	docker-compose ps

# ===========================
# 데이터베이스
# ===========================
.PHONY: db-upgrade
db-upgrade: ## 데이터베이스 마이그레이션
	@echo "$(GREEN)데이터베이스 마이그레이션...$(NC)"
	alembic upgrade head

.PHONY: db-downgrade
db-downgrade: ## 데이터베이스 롤백
	@echo "$(YELLOW)데이터베이스 롤백...$(NC)"
	alembic downgrade -1

.PHONY: db-reset
db-reset: ## 데이터베이스 초기화
	@echo "$(RED)⚠️  데이터베이스 초기화...$(NC)"
	alembic downgrade base
	alembic upgrade head

# ===========================
# 유틸리티
# ===========================
.PHONY: clean
clean: ## 캐시 및 임시 파일 정리
	@echo "$(YELLOW)정리 중...$(NC)"
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name ".coverage" -delete
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	@echo "$(GREEN)✅ 정리 완료!$(NC)"

.PHONY: env-example
env-example: ## .env.example 파일 생성
	@echo "$(GREEN).env.example 파일 생성 중...$(NC)"
	cp .env .env.example
	sed -i 's/=.*/=/' .env.example

.PHONY: api-docs
api-docs: ## API 문서 열기
	@echo "$(GREEN)API 문서 열기...$(NC)"
	open http://localhost:$(PORT)/docs

.PHONY: shell
shell: ## IPython 셸 실행
	@echo "$(GREEN)대화형 셸 시작...$(NC)"
	ipython

# ===========================
# 배포
# ===========================
.PHONY: deploy-check
deploy-check: ## 배포 전 체크리스트
	@echo "$(YELLOW)배포 전 체크리스트:$(NC)"
	@echo "[ ] .env 파일의 DEBUG=False 확인"
	@echo "[ ] SECRET_KEY 변경 확인"
	@echo "[ ] 테스트 통과 확인"
	@echo "[ ] Docker 이미지 빌드 확인"
	@echo "[ ] 데이터베이스 마이그레이션 확인"

.PHONY: version
version: ## 현재 버전 표시
	@echo "$(GREEN)YouTube Translator v1.0.0$(NC)"

# ===========================
# 일괄 작업
# ===========================
.PHONY: all
all: clean install quality test ## 전체 빌드 프로세스

.PHONY: fresh
fresh: clean setup install-dev quality test ## 완전히 새로 시작

# ===========================
# 사용 예시
# ===========================
# make setup          # 초기 설정
# make dev           # 개발 서버 실행
# make test          # 테스트 실행
# make docker-build  # Docker 이미지 빌드
# make up            # 전체 스택 실행
