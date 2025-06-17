-- YouTube Translator 데이터베이스 초기화 스크립트
-- PostgreSQL 16+ 권장

-- ===========================
-- 데이터베이스 설정
-- ===========================

-- 확장 기능 활성화
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";      -- UUID 생성
CREATE EXTENSION IF NOT EXISTS "pgcrypto";       -- 암호화
CREATE EXTENSION IF NOT EXISTS "pg_trgm";        -- 텍스트 검색

-- ===========================
-- 사용자 테이블
-- ===========================
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100),
    is_active BOOLEAN DEFAULT true,
    is_superuser BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP WITH TIME ZONE,
    
    -- 인덱스
    CONSTRAINT email_check CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')
);

-- 인덱스 생성
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_created_at ON users(created_at);

-- ===========================
-- 번역 기록 테이블
-- ===========================
CREATE TABLE IF NOT EXISTS translations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    youtube_url TEXT NOT NULL,
    video_id VARCHAR(20) NOT NULL,
    video_title TEXT,
    channel_name VARCHAR(255),
    video_duration VARCHAR(20),
    
    -- 번역 데이터
    source_language VARCHAR(10) DEFAULT 'en',
    target_language VARCHAR(10) DEFAULT 'ko',
    translation TEXT NOT NULL,
    summary TEXT,
    
    -- 메타데이터
    word_count INTEGER,
    confidence_score DECIMAL(3,2) CHECK (confidence_score >= 0 AND confidence_score <= 1),
    processing_time DECIMAL(10,2),  -- 초 단위
    
    -- 타임스탬프
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- 캐시 키 (중복 방지)
    cache_key VARCHAR(64) UNIQUE,
    
    -- 상태
    status VARCHAR(20) DEFAULT 'completed' CHECK (status IN ('pending', 'processing', 'completed', 'failed'))
);

-- 인덱스 생성
CREATE INDEX idx_translations_user_id ON translations(user_id);
CREATE INDEX idx_translations_video_id ON translations(video_id);
CREATE INDEX idx_translations_youtube_url ON translations(youtube_url);
CREATE INDEX idx_translations_created_at ON translations(created_at);
CREATE INDEX idx_translations_cache_key ON translations(cache_key);
CREATE INDEX idx_translations_status ON translations(status);

-- 전문 검색 인덱스
CREATE INDEX idx_translations_search ON translations USING gin(to_tsvector('korean', translation));

-- ===========================
-- API 사용 통계 테이블
-- ===========================
CREATE TABLE IF NOT EXISTS api_usage (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    endpoint VARCHAR(255) NOT NULL,
    method VARCHAR(10) NOT NULL,
    status_code INTEGER,
    response_time DECIMAL(10,3),  -- 밀리초
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- 일별 집계용
    date DATE GENERATED ALWAYS AS (DATE(created_at)) STORED
);

-- 인덱스 생성
CREATE INDEX idx_api_usage_user_id ON api_usage(user_id);
CREATE INDEX idx_api_usage_endpoint ON api_usage(endpoint);
CREATE INDEX idx_api_usage_date ON api_usage(date);
CREATE INDEX idx_api_usage_created_at ON api_usage(created_at);

-- ===========================
-- 에러 로그 테이블
-- ===========================
CREATE TABLE IF NOT EXISTS error_logs (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    error_type VARCHAR(100) NOT NULL,
    error_message TEXT NOT NULL,
    error_traceback TEXT,
    endpoint VARCHAR(255),
    request_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 인덱스 생성
CREATE INDEX idx_error_logs_user_id ON error_logs(user_id);
CREATE INDEX idx_error_logs_error_type ON error_logs(error_type);
CREATE INDEX idx_error_logs_created_at ON error_logs(created_at);

-- ===========================
-- 사용자 선호 설정
-- ===========================
CREATE TABLE IF NOT EXISTS user_preferences (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    default_target_language VARCHAR(10) DEFAULT 'ko',
    auto_summary BOOLEAN DEFAULT true,
    save_history BOOLEAN DEFAULT true,
    notification_enabled BOOLEAN DEFAULT false,
    theme VARCHAR(20) DEFAULT 'light',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ===========================
-- 구독/결제 정보 (향후 확장용)
-- ===========================
CREATE TABLE IF NOT EXISTS subscriptions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    plan_type VARCHAR(20) DEFAULT 'free' CHECK (plan_type IN ('free', 'basic', 'pro', 'enterprise')),
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'cancelled', 'expired', 'suspended')),
    start_date DATE NOT NULL DEFAULT CURRENT_DATE,
    end_date DATE,
    monthly_limit INTEGER DEFAULT 10,  -- 월 번역 제한
    used_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ===========================
-- 뷰 생성 (통계용)
-- ===========================

-- 일별 사용 통계 뷰
CREATE OR REPLACE VIEW daily_usage_stats AS
SELECT 
    date,
    COUNT(*) as total_requests,
    COUNT(DISTINCT user_id) as unique_users,
    AVG(response_time) as avg_response_time,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY response_time) as p95_response_time,
    COUNT(CASE WHEN status_code >= 400 THEN 1 END) as error_count
FROM api_usage
GROUP BY date;

-- 인기 비디오 뷰
CREATE OR REPLACE VIEW popular_videos AS
SELECT 
    video_id,
    video_title,
    channel_name,
    COUNT(*) as translation_count,
    COUNT(DISTINCT user_id) as unique_users,
    AVG(confidence_score) as avg_confidence,
    MAX(created_at) as last_translated
FROM translations
WHERE status = 'completed'
GROUP BY video_id, video_title, channel_name
ORDER BY translation_count DESC;

-- ===========================
-- 함수 생성
-- ===========================

-- updated_at 자동 업데이트 함수
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 트리거 생성
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_translations_updated_at BEFORE UPDATE ON translations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_preferences_updated_at BEFORE UPDATE ON user_preferences
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_subscriptions_updated_at BEFORE UPDATE ON subscriptions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ===========================
-- 초기 데이터 (선택사항)
-- ===========================

-- 기본 관리자 계정 (비밀번호: admin123 - bcrypt 해시)
-- INSERT INTO users (email, username, password_hash, full_name, is_superuser)
-- VALUES ('admin@example.com', 'admin', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewKyNiGPKkdJ3.C6', 'Administrator', true);

-- ===========================
-- 권한 설정
-- ===========================

-- 읽기 전용 사용자 생성 (모니터링용)
-- CREATE ROLE readonly_user WITH LOGIN PASSWORD 'readonly_password';
-- GRANT CONNECT ON DATABASE youtube_translator TO readonly_user;
-- GRANT USAGE ON SCHEMA public TO readonly_user;
-- GRANT SELECT ON ALL TABLES IN SCHEMA public TO readonly_user;

-- 초보자를 위한 설명:
-- 1. UUID: 고유한 ID를 자동으로 생성하는 타입
-- 2. REFERENCES: 외래 키로 다른 테이블과 연결
-- 3. INDEX: 검색 속도를 높이는 색인
-- 4. TRIGGER: 특정 이벤트 발생 시 자동 실행되는 함수
-- 5. VIEW: 자주 사용하는 쿼리를 미리 정의한 가상 테이블
