/**
 * YouTube Translator 프론트엔드 JavaScript
 * 
 * 주요 기능:
 * 1. 폼 제출 처리 및 API 통신
 * 2. UI 상태 관리 (로딩, 결과, 오류)
 * 3. 사용자 인터랙션 처리
 * 4. 테마 전환 (라이트/다크 모드)
 * 5. 유틸리티 함수들
 * 
 * @author Your Name
 * @version 1.0.0
 */

// 전역 상태 관리 객체
const AppState = {
    isLoading: false,
    currentTranslation: null,
    theme: localStorage.getItem('theme') || 'light'
};

// DOM 요소 캐싱 (성능 최적화)
const DOM = {
    // 폼 관련
    form: null,
    urlInput: null,
    submitBtn: null,
    pasteBtn: null,
    
    // 섹션
    loadingSection: null,
    resultSection: null,
    errorSection: null,
    
    // 결과 표시
    videoTitle: null,
    channelName: null,
    videoDuration: null,
    summaryContent: null,
    translationContent: null,
    
    // 버튼
    copyBtn: null,
    downloadBtn: null,
    shareBtn: null,
    newTranslationBtn: null,
    retryBtn: null,
    themeToggle: null,
    
    // 기타
    progressFill: null,
    errorMessage: null,
    toast: null
};

/**
 * 초기화 함수 - DOM이 로드되면 실행
 */
document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 YouTube Translator 초기화 시작');
    
    // DOM 요소 초기화
    initializeDOMElements();
    
    // 이벤트 리스너 설정
    setupEventListeners();
    
    // 테마 초기화
    initializeTheme();
    
    // URL 파라미터 확인 (공유 링크로 접속한 경우)
    checkURLParameters();
    
    console.log('✅ 초기화 완료');
});

/**
 * DOM 요소들을 캐싱하여 성능 향상
 */
function initializeDOMElements() {
    // 폼 관련
    DOM.form = document.getElementById('translateForm');
    DOM.urlInput = document.getElementById('youtubeUrl');
    DOM.submitBtn = document.getElementById('submitBtn');
    DOM.pasteBtn = document.getElementById('pasteBtn');
    
    // 섹션
    DOM.loadingSection = document.getElementById('loadingSection');
    DOM.resultSection = document.getElementById('resultSection');
    DOM.errorSection = document.getElementById('errorSection');
    
    // 결과 표시
    DOM.videoTitle = document.getElementById('videoTitle');
    DOM.channelName = document.getElementById('channelName');
    DOM.videoDuration = document.getElementById('videoDuration');
    DOM.summaryContent = document.getElementById('summaryContent');
    DOM.translationContent = document.getElementById('translationContent');
    
    // 버튼
    DOM.copyBtn = document.getElementById('copyBtn');
    DOM.downloadBtn = document.getElementById('downloadBtn');
    DOM.shareBtn = document.getElementById('shareBtn');
    DOM.newTranslationBtn = document.getElementById('newTranslationBtn');
    DOM.retryBtn = document.getElementById('retryBtn');
    DOM.themeToggle = document.getElementById('themeToggle');
    
    // 기타
    DOM.progressFill = document.getElementById('progressFill');
    DOM.errorMessage = document.getElementById('errorMessage');
    DOM.toast = document.getElementById('toast');
}

/**
 * 이벤트 리스너 설정
 */
function setupEventListeners() {
    // 폼 제출
    DOM.form.addEventListener('submit', handleFormSubmit);
    
    // 붙여넣기 버튼
    DOM.pasteBtn.addEventListener('click', handlePasteClick);
    
    // 샘플 URL 버튼들
    document.querySelectorAll('.sample-url-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const url = e.currentTarget.dataset.url;
            DOM.urlInput.value = url;
            DOM.urlInput.focus();
        });
    });
    
    // 결과 액션 버튼들
    DOM.copyBtn.addEventListener('click', handleCopyClick);
    DOM.downloadBtn.addEventListener('click', handleDownloadClick);
    DOM.shareBtn.addEventListener('click', handleShareClick);
    
    // 새 번역 & 재시도 버튼
    DOM.newTranslationBtn.addEventListener('click', resetForm);
    DOM.retryBtn.addEventListener('click', () => {
        resetForm();
        DOM.form.dispatchEvent(new Event('submit'));
    });
    
    // 테마 토글
    DOM.themeToggle.addEventListener('click', toggleTheme);
    
    // 부드러운 스크롤 (네비게이션 링크)
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', (e) => {
            e.preventDefault();
            const target = document.querySelector(anchor.getAttribute('href'));
            if (target) {
                target.scrollIntoView({ behavior: 'smooth' });
            }
        });
    });
}

/**
 * 폼 제출 처리
 * @param {Event} e - 제출 이벤트
 */
async function handleFormSubmit(e) {
    e.preventDefault();
    
    // 유효성 검사
    const url = DOM.urlInput.value.trim();
    if (!isValidYouTubeURL(url)) {
        showToast('올바른 YouTube URL을 입력해주세요', 'error');
        return;
    }
    
    // 중복 제출 방지
    if (AppState.isLoading) {
        return;
    }
    
    // 고급 옵션 수집
    const options = {
        include_summary: document.getElementById('includeSummary').checked,
        include_timestamps: document.getElementById('includeTimestamps').checked,
        highlight_keywords: document.getElementById('highlightKeywords').checked
    };
    
    // 번역 시작
    await translateVideo(url, options);
}

/**
 * YouTube URL 유효성 검사
 * @param {string} url - 검사할 URL
 * @returns {boolean} 유효 여부
 */
function isValidYouTubeURL(url) {
    const patterns = [
        /^https?:\/\/(www\.)?(youtube\.com\/watch\?v=|youtu\.be\/)/,
        /^https?:\/\/(www\.)?youtube\.com\/embed\//,
        /^https?:\/\/m\.youtube\.com\/watch\?v=/
    ];
    
    return patterns.some(pattern => pattern.test(url));
}

/**
 * 비디오 번역 메인 함수
 * @param {string} url - YouTube URL
 * @param {Object} options - 번역 옵션
 */
async function translateVideo(url, options = {}) {
    // UI 상태 변경
    showLoadingState();
    
    // 진행률 시뮬레이션 시작
    const progressInterval = startProgressSimulation();
    
    try {
        // API 호출
        const response = await fetch('/api/translate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                youtube_url: url,
                ...options
            })
        });
        
        // 응답 처리
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || '번역 처리 중 오류가 발생했습니다');
        }
        
        const data = await response.json();
        
        // 결과 저장
        AppState.currentTranslation = data;
        
        // 결과 표시
        displayResults(data);
        
        // 성공 알림
        showToast('번역이 완료되었습니다!', 'success');
        
    } catch (error) {
        console.error('번역 오류:', error);
        showErrorState(error.message);
    } finally {
        // 진행률 정리
        clearInterval(progressInterval);
        hideLoadingState();
    }
}

/**
 * 로딩 상태 표시
 */
function showLoadingState() {
    AppState.isLoading = true;
    
    // 버튼 비활성화
    DOM.submitBtn.disabled = true;
    DOM.submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> <span>번역 중...</span>';
    
    // 섹션 표시/숨김
    DOM.loadingSection.classList.remove('hidden');
    DOM.resultSection.classList.add('hidden');
    DOM.errorSection.classList.add('hidden');
    
    // 스크롤
    DOM.loadingSection.scrollIntoView({ behavior: 'smooth' });
}

/**
 * 로딩 상태 숨김
 */
function hideLoadingState() {
    AppState.isLoading = false;
    
    // 버튼 활성화
    DOM.submitBtn.disabled = false;
    DOM.submitBtn.innerHTML = '<i class="fas fa-language"></i> <span>번역 시작</span>';
    
    // 로딩 섹션 숨김
    DOM.loadingSection.classList.add('hidden');
    
    // 진행률 초기화
    DOM.progressFill.style.width = '0%';
}

/**
 * 진행률 시뮬레이션
 * @returns {number} 인터벌 ID
 */
function startProgressSimulation() {
    let progress = 0;
    const increment = Math.random() * 3 + 1; // 1-4% 랜덤 증가
    
    return setInterval(() => {
        progress += increment;
        if (progress > 90) progress = 90; // 90%에서 멈춤
        DOM.progressFill.style.width = `${progress}%`;
    }, 200);
}

/**
 * 결과 표시
 * @param {Object} data - API 응답 데이터
 */
function displayResults(data) {
    // 비디오 정보
    DOM.videoTitle.textContent = data.video_title || '제목 없음';
    DOM.channelName.textContent = data.channel_name || '채널 정보 없음';
    DOM.videoDuration.textContent = data.video_duration || '시간 정보 없음';
    
    // 요약 (옵션)
    if (data.summary) {
        document.getElementById('summarySection').style.display = 'block';
        DOM.summaryContent.textContent = data.summary;
    } else {
        document.getElementById('summarySection').style.display = 'none';
    }
    
    // 번역 결과
    DOM.translationContent.innerHTML = formatTranslation(data.translation);
    
    // 결과 섹션 표시
    DOM.resultSection.classList.remove('hidden');
    DOM.resultSection.scrollIntoView({ behavior: 'smooth' });
}

/**
 * 번역 텍스트 포맷팅
 * @param {string} text - 원본 텍스트
 * @returns {string} 포맷된 HTML
 */
function formatTranslation(text) {
    // 기본 이스케이프
    let formatted = escapeHtml(text);
    
    // 줄바꿈 처리
    formatted = formatted.replace(/\n/g, '<br>');
    
    // 타임스탬프 강조 [00:00]
    formatted = formatted.replace(
        /\[(\d{2}:\d{2})\]/g,
        '<span class="timestamp">[$1]</span>'
    );
    
    // 굵은 글씨 **텍스트**
    formatted = formatted.replace(
        /\*\*(.*?)\*\*/g,
        '<strong>$1</strong>'
    );
    
    // 화자 구분 [화자 1]
    formatted = formatted.replace(
        /\[(화자 \d+)\]/g,
        '<span class="speaker">[$1]</span>'
    );
    
    return formatted;
}

/**
 * HTML 이스케이프 (XSS 방지)
 * @param {string} text - 원본 텍스트
 * @returns {string} 이스케이프된 텍스트
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * 오류 상태 표시
 * @param {string} message - 오류 메시지
 */
function showErrorState(message) {
    DOM.errorMessage.textContent = message;
    DOM.errorSection.classList.remove('hidden');
    DOM.errorSection.scrollIntoView({ behavior: 'smooth' });
}

/**
 * 복사 버튼 클릭 처리
 */
async function handleCopyClick() {
    if (!AppState.currentTranslation) return;
    
    try {
        const text = DOM.translationContent.innerText;
        await navigator.clipboard.writeText(text);
        
        // 버튼 상태 변경
        DOM.copyBtn.innerHTML = '<i class="fas fa-check"></i> <span>복사됨!</span>';
        DOM.copyBtn.style.backgroundColor = 'var(--success-color)';
        DOM.copyBtn.style.color = 'white';
        
        // 3초 후 원래대로
        setTimeout(() => {
            DOM.copyBtn.innerHTML = '<i class="fas fa-copy"></i> <span>복사</span>';
            DOM.copyBtn.style.backgroundColor = '';
            DOM.copyBtn.style.color = '';
        }, 3000);
        
        showToast('클립보드에 복사되었습니다', 'success');
    } catch (error) {
        console.error('복사 실패:', error);
        showToast('복사에 실패했습니다', 'error');
    }
}

/**
 * 다운로드 버튼 클릭 처리
 */
function handleDownloadClick() {
    if (!AppState.currentTranslation) return;
    
    // 텍스트 파일 생성
    const content = `YouTube 번역 결과
========================
제목: ${AppState.currentTranslation.video_title || ''}
채널: ${AppState.currentTranslation.channel_name || ''}
길이: ${AppState.currentTranslation.video_duration || ''}
번역일: ${new Date(AppState.currentTranslation.translated_at).toLocaleString('ko-KR')}
URL: ${AppState.currentTranslation.youtube_url}

요약
----
${AppState.currentTranslation.summary || '요약 없음'}

전체 번역
---------
${DOM.translationContent.innerText}`;
    
    // Blob 생성 및 다운로드
    const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `youtube_translation_${Date.now()}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    showToast('다운로드가 시작되었습니다', 'success');
}

/**
 * 공유 버튼 클릭 처리
 */
async function handleShareClick() {
    if (!AppState.currentTranslation) return;
    
    const shareData = {
        title: 'YouTube 번역 결과',
        text: `"${AppState.currentTranslation.video_title}" 번역 결과를 확인하세요!`,
        url: window.location.href
    };
    
    try {
        // Web Share API 지원 확인
        if (navigator.share) {
            await navigator.share(shareData);
            showToast('공유되었습니다', 'success');
        } else {
            // 대체: URL 복사
            await navigator.clipboard.writeText(window.location.href);
            showToast('링크가 복사되었습니다', 'success');
        }
    } catch (error) {
        console.error('공유 실패:', error);
        // 사용자가 공유를 취소한 경우는 오류 표시하지 않음
        if (error.name !== 'AbortError') {
            showToast('공유에 실패했습니다', 'error');
        }
    }
}

/**
 * 붙여넣기 버튼 클릭 처리
 */
async function handlePasteClick() {
    try {
        const text = await navigator.clipboard.readText();
        DOM.urlInput.value = text;
        DOM.urlInput.focus();
        
        // 자동으로 YouTube URL인지 확인
        if (isValidYouTubeURL(text)) {
            showToast('YouTube URL이 붙여넣어졌습니다', 'success');
        }
    } catch (error) {
        console.error('붙여넣기 실패:', error);
        showToast('클립보드 접근 권한이 필요합니다', 'error');
    }
}

/**
 * 폼 초기화
 */
function resetForm() {
    DOM.form.reset();
    DOM.resultSection.classList.add('hidden');
    DOM.errorSection.classList.add('hidden');
    AppState.currentTranslation = null;
    DOM.urlInput.focus();
}

/**
 * 테마 초기화
 */
function initializeTheme() {
    document.documentElement.setAttribute('data-theme', AppState.theme);
    updateThemeIcon();
}

/**
 * 테마 전환
 */
function toggleTheme() {
    AppState.theme = AppState.theme === 'light' ? 'dark' : 'light';
    document.documentElement.setAttribute('data-theme', AppState.theme);
    localStorage.setItem('theme', AppState.theme);
    updateThemeIcon();
    
    showToast(`${AppState.theme === 'dark' ? '다크' : '라이트'} 모드로 전환되었습니다`, 'success');
}

/**
 * 테마 아이콘 업데이트
 */
function updateThemeIcon() {
    const icon = DOM.themeToggle.querySelector('i');
    icon.className = AppState.theme === 'light' ? 'fas fa-moon' : 'fas fa-sun';
}

/**
 * Toast 알림 표시
 * @param {string} message - 알림 메시지
 * @param {string} type - 알림 타입 (success, error, warning)
 */
function showToast(message, type = 'success') {
    // 기존 toast 제거
    DOM.toast.className = 'toast';
    
    // 메시지 설정
    DOM.toast.querySelector('.toast-message').textContent = message;
    
    // 아이콘 설정
    const icon = DOM.toast.querySelector('.toast-icon');
    const iconClasses = {
        success: 'fas fa-check-circle',
        error: 'fas fa-exclamation-circle',
        warning: 'fas fa-exclamation-triangle'
    };
    icon.className = `toast-icon ${iconClasses[type] || iconClasses.success}`;
    
    // 표시
    DOM.toast.classList.add(type);
    DOM.toast.classList.remove('hidden');
    
    // 3초 후 자동 숨김
    setTimeout(() => {
        DOM.toast.classList.add('hidden');
    }, 3000);
}

/**
 * URL 파라미터 확인 (공유 링크 처리)
 */
function checkURLParameters() {
    const params = new URLSearchParams(window.location.search);
    const youtubeUrl = params.get('url');
    
    if (youtubeUrl && isValidYouTubeURL(youtubeUrl)) {
        DOM.urlInput.value = youtubeUrl;
        // 자동으로 번역 시작
        setTimeout(() => {
            DOM.form.dispatchEvent(new Event('submit'));
        }, 500);
    }
}

/**
 * 네트워크 상태 감지
 */
window.addEventListener('online', () => {
    showToast('인터넷 연결이 복구되었습니다', 'success');
});

window.addEventListener('offline', () => {
    showToast('인터넷 연결이 끊어졌습니다', 'error');
});

/**
 * 페이지 벗어날 때 경고 (번역 진행 중인 경우)
 */
window.addEventListener('beforeunload', (e) => {
    if (AppState.isLoading) {
        e.preventDefault();
        e.returnValue = '번역이 진행 중입니다. 페이지를 벗어나시겠습니까?';
    }
});

// 💡 초보자를 위한 JavaScript 팁
/*
 * 1. async/await 사용하기
 *    - 비동기 코드를 동기 코드처럼 작성할 수 있습니다
 *    - try/catch로 에러 처리가 쉬워집니다
 * 
 * 2. DOM 요소 캐싱
 *    - document.getElementById를 반복하지 말고 한 번만 호출하세요
 *    - 성능이 크게 향상됩니다
 * 
 * 3. 이벤트 위임
 *    - 부모 요소에 이벤트를 등록하면 동적 요소도 처리 가능합니다
 *    - event.target으로 실제 클릭된 요소를 확인하세요
 * 
 * 4. 디바운싱/쓰로틀링
 *    - 연속적인 이벤트(스크롤, 리사이즈)는 제한하세요
 *    - 성능 문제를 방지할 수 있습니다
 * 
 * 5. 에러 처리
 *    - 모든 비동기 작업에는 try/catch를 사용하세요
 *    - 사용자에게 친절한 에러 메시지를 보여주세요
 */
