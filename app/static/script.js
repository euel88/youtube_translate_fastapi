/**
 * YouTube 실시간 번역 자막 시스템
 * 
 * 주요 기능:
 * 1. YouTube IFrame API로 영상 재생
 * 2. WebSocket으로 서버와 실시간 통신
 * 3. 재생 시간에 맞춰 자막 동기화
 * 4. 자막 오버레이 표시
 * 
 * @author Your Name
 * @version 2.0.0
 */

// 전역 변수
let player = null;              // YouTube Player 객체
let socket = null;              // WebSocket 연결
let subtitles = [];             // 번역된 자막 배열
let currentSubtitleIndex = -1;  // 현재 자막 인덱스
let isPlaying = false;          // 재생 상태
let syncInterval = null;        // 동기화 인터벌

// DOM 요소 캐싱
const DOM = {
    form: null,
    urlInput: null,
    playerSection: null,
    subtitleOverlay: null,
    subtitleKorean: null,
    subtitleEnglish: null,
    playPauseBtn: null,
    progressFill: null,
    timeDisplay: null,
    subtitleList: null,
    submitBtn: null
};

/**
 * 초기화 함수
 */
document.addEventListener('DOMContentLoaded', () => {
    console.log('🎬 YouTube 실시간 번역 자막 시스템 초기화');
    
    // DOM 요소 초기화
    initializeDOMElements();
    
    // 이벤트 리스너 설정
    setupEventListeners();
    
    // YouTube IFrame API 로드
    loadYouTubeAPI();
});

/**
 * DOM 요소 초기화
 */
function initializeDOMElements() {
    DOM.form = document.getElementById('translateForm');
    DOM.urlInput = document.getElementById('youtubeUrl');
    DOM.playerSection = document.getElementById('playerSection');
    DOM.subtitleOverlay = document.getElementById('subtitle-overlay');
    DOM.subtitleKorean = document.getElementById('subtitle-korean');
    DOM.subtitleEnglish = document.getElementById('subtitle-english');
    DOM.playPauseBtn = document.getElementById('playPauseBtn');
    DOM.progressFill = document.getElementById('progressFill');
    DOM.timeDisplay = document.getElementById('timeDisplay');
    DOM.subtitleList = document.getElementById('subtitleList');
    DOM.submitBtn = document.getElementById('submitBtn');
}

/**
 * 이벤트 리스너 설정
 */
function setupEventListeners() {
    // 폼 제출
    DOM.form.addEventListener('submit', handleFormSubmit);
    
    // 샘플 URL 버튼
    document.querySelectorAll('.sample-url-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            DOM.urlInput.value = e.currentTarget.dataset.url;
        });
    });
    
    // 재생/일시정지 버튼
    DOM.playPauseBtn.addEventListener('click', togglePlayPause);
    
    // 진행바 클릭
    document.querySelector('.progress-bar').addEventListener('click', seekToPosition);
}

/**
 * YouTube IFrame API 로드
 */
function loadYouTubeAPI() {
    const tag = document.createElement('script');
    tag.src = 'https://www.youtube.com/iframe_api';
    const firstScriptTag = document.getElementsByTagName('script')[0];
    firstScriptTag.parentNode.insertBefore(tag, firstScriptTag);
}

/**
 * YouTube API 준비 완료 콜백
 */
window.onYouTubeIframeAPIReady = function() {
    console.log('✅ YouTube IFrame API 준비 완료');
};

/**
 * 폼 제출 처리
 */
async function handleFormSubmit(e) {
    e.preventDefault();
    
    const url = DOM.urlInput.value.trim();
    if (!url) return;
    
    // 버튼 상태 변경
    DOM.submitBtn.disabled = true;
    DOM.submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> <span>준비 중...</span>';
    
    try {
        // WebSocket 연결
        await connectWebSocket();
        
        // 자막 로드 요청
        socket.send(JSON.stringify({
            type: 'init',
            url: url
        }));
        
    } catch (error) {
        console.error('오류:', error);
        showError('연결 실패. 다시 시도해주세요.');
        resetSubmitButton();
    }
}

/**
 * WebSocket 연결
 */
async function connectWebSocket() {
    return new Promise((resolve, reject) => {
        // 기존 연결 종료
        if (socket) {
            socket.close();
        }
        
        // 새 연결 생성
        const wsUrl = `ws://localhost:8000/ws/${Date.now()}`;
        socket = new WebSocket(wsUrl);
        
        socket.onopen = () => {
            console.log('✅ WebSocket 연결 성공');
            resolve();
        };
        
        socket.onerror = (error) => {
            console.error('❌ WebSocket 오류:', error);
            reject(error);
        };
        
        socket.onmessage = handleWebSocketMessage;
        
        socket.onclose = () => {
            console.log('🔌 WebSocket 연결 종료');
        };
    });
}

/**
 * WebSocket 메시지 처리
 */
function handleWebSocketMessage(event) {
    const data = JSON.parse(event.data);
    
    switch (data.type) {
        case 'ready':
            // 자막 준비 완료
            console.log(`✅ ${data.total}개의 자막 준비 완료`);
            subtitles = data.subtitles;
            initializePlayer();
            displaySubtitleList();
            resetSubmitButton();
            break;
            
        case 'error':
            // 오류 발생
            showError(data.message);
            resetSubmitButton();
            break;
    }
}

/**
 * YouTube Player 초기화
 */
function initializePlayer() {
    const videoId = extractVideoId(DOM.urlInput.value);
    
    // 플레이어 섹션 표시
    DOM.playerSection.classList.remove('hidden');
    DOM.playerSection.scrollIntoView({ behavior: 'smooth' });
    
    // 기존 플레이어 제거
    if (player) {
        player.destroy();
    }
    
    // 새 플레이어 생성
    player = new YT.Player('youtube-player', {
        height: '100%',
        width: '100%',
        videoId: videoId,
        playerVars: {
            'autoplay': 0,
            'controls': 1,
            'rel': 0,
            'modestbranding': 1,
            'cc_load_policy': 0  // 기본 자막 숨김
        },
        events: {
            'onReady': onPlayerReady,
            'onStateChange': onPlayerStateChange
        }
    });
}

/**
 * 플레이어 준비 완료 콜백
 */
function onPlayerReady(event) {
    console.log('✅ 플레이어 준비 완료');
    updateTimeDisplay();
}

/**
 * 플레이어 상태 변경 콜백
 */
function onPlayerStateChange(event) {
    if (event.data === YT.PlayerState.PLAYING) {
        isPlaying = true;
        startSubtitleSync();
        DOM.playPauseBtn.innerHTML = '<i class="fas fa-pause"></i>';
    } else {
        isPlaying = false;
        stopSubtitleSync();
        DOM.playPauseBtn.innerHTML = '<i class="fas fa-play"></i>';
    }
}

/**
 * 자막 동기화 시작
 */
function startSubtitleSync() {
    if (syncInterval) return;
    
    syncInterval = setInterval(() => {
        if (!player || !player.getCurrentTime) return;
        
        const currentTime = player.getCurrentTime();
        updateProgress(currentTime);
        updateCurrentSubtitle(currentTime);
        updateTimeDisplay();
    }, 100); // 100ms마다 체크
}

/**
 * 자막 동기화 중지
 */
function stopSubtitleSync() {
    if (syncInterval) {
        clearInterval(syncInterval);
        syncInterval = null;
    }
}

/**
 * 현재 시간에 맞는 자막 업데이트
 */
function updateCurrentSubtitle(currentTime) {
    let foundIndex = -1;
    
    // 현재 시간에 맞는 자막 찾기
    for (let i = 0; i < subtitles.length; i++) {
        const subtitle = subtitles[i];
        if (currentTime >= subtitle.start && currentTime < subtitle.start + subtitle.duration) {
            foundIndex = i;
            break;
        }
    }
    
    // 자막이 변경되었을 때만 업데이트
    if (foundIndex !== currentSubtitleIndex) {
        currentSubtitleIndex = foundIndex;
        
        if (foundIndex >= 0) {
            showSubtitle(subtitles[foundIndex]);
            highlightSubtitleItem(foundIndex);
        } else {
            hideSubtitle();
        }
    }
}

/**
 * 자막 표시
 */
function showSubtitle(subtitle) {
    DOM.subtitleKorean.textContent = subtitle.translation;
    
    // 원문 표시 옵션 확인
    if (document.getElementById('showOriginal').checked) {
        DOM.subtitleEnglish.textContent = subtitle.text;
        DOM.subtitleEnglish.style.display = 'block';
    } else {
        DOM.subtitleEnglish.style.display = 'none';
    }
    
    DOM.subtitleOverlay.style.display = 'block';
}

/**
 * 자막 숨기기
 */
function hideSubtitle() {
    DOM.subtitleOverlay.style.display = 'none';
}

/**
 * 자막 목록 표시
 */
function displaySubtitleList() {
    DOM.subtitleList.innerHTML = '';
    
    subtitles.forEach((subtitle, index) => {
        const item = document.createElement('div');
        item.className = 'subtitle-item';
        item.dataset.index = index;
        
        item.innerHTML = `
            <div class="subtitle-time">${formatTime(subtitle.start)}</div>
            <div class="subtitle-content">
                <div class="subtitle-content-korean">${subtitle.translation}</div>
                <div class="subtitle-content-english">${subtitle.text}</div>
            </div>
        `;
        
        // 클릭 시 해당 시간으로 이동
        item.addEventListener('click', () => {
            if (player && player.seekTo) {
                player.seekTo(subtitle.start);
            }
        });
        
        DOM.subtitleList.appendChild(item);
    });
}

/**
 * 자막 아이템 하이라이트
 */
function highlightSubtitleItem(index) {
    // 기존 하이라이트 제거
    document.querySelectorAll('.subtitle-item').forEach(item => {
        item.classList.remove('active');
    });
    
    // 현재 자막 하이라이트
    const currentItem = document.querySelector(`.subtitle-item[data-index="${index}"]`);
    if (currentItem) {
        currentItem.classList.add('active');
        
        // 자동 스크롤 옵션 확인
        if (document.getElementById('autoScroll').checked) {
            currentItem.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    }
}

/**
 * 재생/일시정지 토글
 */
function togglePlayPause() {
    if (!player) return;
    
    if (isPlaying) {
        player.pauseVideo();
    } else {
        player.playVideo();
    }
}

/**
 * 진행바 업데이트
 */
function updateProgress(currentTime) {
    if (!player || !player.getDuration) return;
    
    const duration = player.getDuration();
    const progress = (currentTime / duration) * 100;
    DOM.progressFill.style.width = `${progress}%`;
}

/**
 * 시간 표시 업데이트
 */
function updateTimeDisplay() {
    if (!player || !player.getCurrentTime) return;
    
    const currentTime = player.getCurrentTime() || 0;
    const duration = player.getDuration() || 0;
    
    DOM.timeDisplay.textContent = `${formatTime(currentTime)} / ${formatTime(duration)}`;
}

/**
 * 진행바 클릭으로 위치 이동
 */
function seekToPosition(e) {
    if (!player || !player.getDuration) return;
    
    const progressBar = e.currentTarget;
    const clickX = e.offsetX;
    const width = progressBar.offsetWidth;
    const percentage = clickX / width;
    const duration = player.getDuration();
    const seekTime = duration * percentage;
    
    player.seekTo(seekTime);
}

/**
 * 비디오 ID 추출
 */
function extractVideoId(url) {
    const match = url.match(/(?:v=|\/)([0-9A-Za-z_-]{11}).*/);
    return match ? match[1] : null;
}

/**
 * 시간 포맷팅
 */
function formatTime(seconds) {
    const minutes = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${minutes}:${secs.toString().padStart(2, '0')}`;
}

/**
 * 오류 표시
 */
function showError(message) {
    // Toast 알림 표시
    const toast = document.getElementById('toast');
    const toastMessage = toast.querySelector('.toast-message');
    
    toast.className = 'toast error';
    toastMessage.textContent = message;
    toast.classList.remove('hidden');
    
    setTimeout(() => {
        toast.classList.add('hidden');
    }, 5000);
}

/**
 * 제출 버튼 초기화
 */
function resetSubmitButton() {
    DOM.submitBtn.disabled = false;
    DOM.submitBtn.innerHTML = '<i class="fas fa-play"></i> <span>영상 재생 & 번역</span>';
}

// 페이지 언로드 시 정리
window.addEventListener('beforeunload', () => {
    if (socket) {
        socket.close();
    }
    if (syncInterval) {
        clearInterval(syncInterval);
    }
});

console.log('✅ YouTube 실시간 번역 자막 스크립트 로드 완료');
