// script.js - 前端邏輯 (完整版，適用於分析板模式 + 棋譜功能)

// --- DOM 元素引用 ---
const canvas = document.getElementById('xiangqi-board');
const ctx = canvas.getContext('2d');
const messageArea = document.getElementById('message-area');
const turnInfoSpan = document.getElementById('current-turn');
const playerColorSpan = document.getElementById('player-color'); // For display if needed
const redTimerDisplay = document.getElementById('red-timer');
const blackTimerDisplay = document.getElementById('black-timer');
const startButton = document.getElementById('start-button');
// 新增棋譜相關元素
const gameRecordArea = document.getElementById('game-record-area');
const copyRecordButton = document.getElementById('copy-record-button');
const loadFenButton = document.getElementById('load-fen-button');
const updateRecordButton = document.getElementById('update-record-button');

// --- 棋盤常量 ---
const BOARD_WIDTH = canvas ? canvas.width : 540; // Add fallback for robustness
const BOARD_HEIGHT = canvas ? canvas.height : 600;
const COLS = 9;
const ROWS = 10;
const SQUARE_SIZE = BOARD_WIDTH / COLS;
const RIVER_Y_CENTER = BOARD_HEIGHT / 2;
const PIECE_RADIUS = SQUARE_SIZE * 0.4;

// --- 遊戲狀態變量 ---
let boardState = null;
let selectedPiece = null;
let currentTurn = 'red';
let gameStarted = false;
let webSocket = null;
// let moveHistory = []; // 前端歷史記錄 (暫時不使用，依賴後端)

// --- 繪圖函數 ---
function drawGrid() { /* ... (同上一個版本) ... */
    if (!ctx) return;
    ctx.strokeStyle = '#6b4e2a'; ctx.lineWidth = 1;
    for (let i = 0; i < COLS; i++) { const x = i * SQUARE_SIZE + SQUARE_SIZE / 2; ctx.beginPath(); ctx.moveTo(x, SQUARE_SIZE / 2); ctx.lineTo(x, RIVER_Y_CENTER - SQUARE_SIZE / 2); ctx.stroke(); ctx.beginPath(); ctx.moveTo(x, RIVER_Y_CENTER + SQUARE_SIZE / 2); ctx.lineTo(x, BOARD_HEIGHT - SQUARE_SIZE / 2); ctx.stroke(); }
    for (let i = 0; i < ROWS; i++) { const y = i * SQUARE_SIZE + SQUARE_SIZE / 2; ctx.beginPath(); ctx.moveTo(SQUARE_SIZE / 2, y); ctx.lineTo(BOARD_WIDTH - SQUARE_SIZE / 2, y); ctx.stroke(); }
    ctx.font = `bold ${SQUARE_SIZE * 0.4}px sans-serif`; ctx.fillStyle = '#4a391d'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; const textY = RIVER_Y_CENTER;
    ctx.save(); ctx.translate(BOARD_WIDTH / 4, textY); ctx.rotate(-Math.PI / 2); ctx.fillText('楚', 0, 0); ctx.restore(); ctx.save(); ctx.translate(BOARD_WIDTH / 4 + ctx.measureText('楚').width / 1.5, textY); ctx.rotate(-Math.PI / 2); ctx.fillText('河', 0, 0); ctx.restore();
    ctx.save(); ctx.translate(BOARD_WIDTH * 3 / 4, textY); ctx.rotate(Math.PI / 2); ctx.fillText('漢', 0, 0); ctx.restore(); ctx.save(); ctx.translate(BOARD_WIDTH * 3 / 4 - ctx.measureText('漢').width / 1.5, textY); ctx.rotate(Math.PI / 2); ctx.fillText('界', 0, 0); ctx.restore();
    function drawPalaceLine(x1, y1, x2, y2) { ctx.beginPath(); ctx.moveTo(x1*SQUARE_SIZE+SQUARE_SIZE/2, y1*SQUARE_SIZE+SQUARE_SIZE/2); ctx.lineTo(x2*SQUARE_SIZE+SQUARE_SIZE/2, y2*SQUARE_SIZE+SQUARE_SIZE/2); ctx.stroke(); }
    drawPalaceLine(3, 0, 5, 2); drawPalaceLine(5, 0, 3, 2); drawPalaceLine(3, 7, 5, 9); drawPalaceLine(5, 7, 3, 9);
 }
function drawPieces() { /* ... (同上一個版本) ... */
    if (!ctx || !boardState) return;
    ctx.font = `bold ${PIECE_RADIUS * 1.2}px sans-serif`; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    for (let y = 0; y < ROWS; y++) {
        for (let x = 0; x < COLS; x++) {
            const piece = boardState[y][x];
            if (piece) {
                const drawX = x * SQUARE_SIZE + SQUARE_SIZE / 2; const drawY = y * SQUARE_SIZE + SQUARE_SIZE / 2;
                ctx.beginPath(); ctx.arc(drawX, drawY, PIECE_RADIUS, 0, Math.PI * 2); ctx.fillStyle = '#f7e0b8'; ctx.fill();
                ctx.strokeStyle = piece.color === 'red' ? '#e03030' : '#333'; ctx.lineWidth = 2; ctx.stroke();
                ctx.beginPath(); ctx.arc(drawX, drawY, PIECE_RADIUS * 0.85, 0, Math.PI * 2); ctx.strokeStyle = piece.color === 'red' ? '#f06060' : '#666'; ctx.lineWidth = 1; ctx.stroke();
                ctx.fillStyle = piece.color === 'red' ? 'red' : 'black'; ctx.fillText(piece.name, drawX, drawY);
                if (selectedPiece && selectedPiece.x === x && selectedPiece.y === y) {
                    ctx.beginPath(); ctx.arc(drawX, drawY, PIECE_RADIUS * 1.05, 0, Math.PI * 2); ctx.strokeStyle = 'gold'; ctx.lineWidth = 4; ctx.stroke();
                }
            }
        }
    }
}
function redrawBoard() { if (!ctx) return; ctx.clearRect(0, 0, BOARD_WIDTH, BOARD_HEIGHT); drawGrid(); drawPieces(); }

// --- 事件處理 ---
function handleCanvasClick(event) {
    if (!webSocket || webSocket.readyState !== WebSocket.OPEN) { setMessage("未連接到伺服器"); return; }
    if (!boardState) { setMessage("等待棋盤數據..."); return; } // 確保棋盤已加載

    const rect = canvas.getBoundingClientRect();
    const clickX = event.clientX - rect.left; const clickY = event.clientY - rect.top;
    const col = Math.floor(clickX / SQUARE_SIZE); const row = Math.floor(clickY / SQUARE_SIZE);
    if (col < 0 || col >= COLS || row < 0 || row >= ROWS) return;

    const clickedPieceData = boardState[row]?.[col];

    if (selectedPiece) {
        const moveData = { type: 'move', from: { x: selectedPiece.x, y: selectedPiece.y }, to: { x: col, y: row } };
        webSocket.send(JSON.stringify(moveData));
        console.log("分析板: 嘗試移動:", moveData);
        selectedPiece = null;
        redrawBoard();
    } else if (clickedPieceData) {
        selectedPiece = { x: col, y: row, piece: clickedPieceData };
        setMessage("");
        redrawBoard();
    }
}

// --- WebSocket 通信 ---
function connectWebSocket() {
    // const wsUrl = `ws://${window.location.hostname}:8080`; // 暫時註釋掉
    const wsUrl = 'ws://localhost:8080'; // 或者 ws://127.0.0.1:8080
    //const wsUrl = `ws://${window.location.hostname}:8080`; // Use hostname from browser bar
    console.log(`嘗試連接 WebSocket: ${wsUrl}`);
    setMessage("正在連接伺服器...");
    if (startButton) startButton.disabled = true;

    // Close existing connection if any
    if (webSocket && webSocket.readyState !== WebSocket.CLOSED) {
        webSocket.close();
    }

    webSocket = new WebSocket(wsUrl);

    webSocket.onopen = () => { console.log('WebSocket 連接已建立'); setMessage("已連接，等待棋盤信息..."); if (startButton) startButton.textContent = "已連接"; };
    webSocket.onmessage = (event) => {
        try {
            const message = JSON.parse(event.data);
            console.log('收到消息:', message);
            switch (message.type) {
                case 'assign_info':
                    if (playerColorSpan) { playerColorSpan.textContent = message.color === 'red' ? '紅方' : '黑方'; playerColorSpan.style.color = message.color; }
                    boardState = message.board; currentTurn = message.turn; updateTurnInfo(); redrawBoard(); setMessage("收到棋盤信息"); gameStarted = true; if (startButton) startButton.textContent = "分析中...";
                    break;
                case 'start_game':
                    gameStarted = true; if (startButton) startButton.textContent = "分析中..."; setMessage(`遊戲信號已開始，輪到 ${currentTurn === 'red' ? '紅方' : '黑方'} (提示)`); if (message.timers) updateTimers(message.timers.red, message.timers.black); redrawBoard();
                    break;
                case 'update_state':
                    boardState = message.board; currentTurn = message.turn; updateTurnInfo(); if (message.timers) updateTimers(message.timers.red, message.timers.black); selectedPiece = null; redrawBoard(); setMessage(message.lastMoveInfo || `輪到 ${currentTurn === 'red' ? '紅方' : '黑方'} (提示)`);
                    break;
                case 'illegal_move':
                    setMessage(`非法移動: ${message.reason}`); selectedPiece = null; redrawBoard(); setTimeout(() => { if (gameStarted && messageArea.textContent.startsWith('非法移動')) setMessage(`輪到 ${currentTurn === 'red' ? '紅方' : '黑方'} (提示)`); }, 1500);
                    break;
                case 'game_over':
                    gameStarted = false; setMessage(`遊戲結束! ${message.winner ? (message.winner === 'red' ? '紅方勝！' : '黑方勝！') : '和棋！'} 原因: ${message.reason}`); if (startButton) { startButton.textContent = "遊戲已結束"; startButton.disabled = true; } if (message.timers) updateTimers(message.timers.red, message.timers.black);
                    break;
                case 'game_record': // 處理棋譜數據
                    if (gameRecordArea) gameRecordArea.value = message.record; setMessage("棋譜已更新");
                    break;
                case 'timer_update': if (message.timers) updateTimers(message.timers.red, message.timers.black); break;
                case 'error': setMessage(`伺服器錯誤: ${message.content}`); break;
                case 'message': setMessage(message.content); break;
                default: console.warn('收到未知的消息類型:', message.type);
            }
        } catch (error) { console.error('處理 WebSocket 消息時出錯:', error, '原始數據:', event.data); setMessage("處理伺服器消息時發生錯誤"); }
    };
    webSocket.onclose = (event) => { console.log('WebSocket 連接已關閉。 Code:', event.code, 'Reason:', event.reason); setMessage("與伺服器斷開連接"); gameStarted = false; boardState = null; if (playerColorSpan) { playerColorSpan.textContent = 'N/A'; playerColorSpan.style.color = 'black';} if (turnInfoSpan) turnInfoSpan.textContent = '已斷開'; if (startButton) { startButton.textContent = "連接已斷開"; startButton.disabled = true; } updateTimers(null, null); redrawBoard(); };
    webSocket.onerror = (error) => { console.error('WebSocket 錯誤:', error); setMessage("WebSocket 連接錯誤"); if (startButton) { startButton.textContent = "連接失敗"; startButton.disabled = true; } };
}

// --- 輔助 UI 函數 ---
function setMessage(msg) { if (messageArea) messageArea.textContent = msg; }
function updateTurnInfo() { if (turnInfoSpan) { turnInfoSpan.textContent = currentTurn === 'red' ? '紅方' : '黑方'; turnInfoSpan.style.color = currentTurn; } }
function formatTime(seconds) { if (seconds === null || seconds === undefined || seconds < 0) return "--:--"; const mins = Math.floor(seconds / 60); const secs = Math.floor(seconds % 60); return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`; }
function updateTimers(redSeconds, blackSeconds) { if (redTimerDisplay && blackTimerDisplay) { redTimerDisplay.textContent = formatTime(redSeconds); blackTimerDisplay.textContent = formatTime(blackSeconds); } }

// --- 初始化和事件綁定 ---
document.addEventListener('DOMContentLoaded', () => {
    if (!canvas || !canvas.getContext) {
        console.error("無法找到 Canvas 元素或獲取其上下文！");
        setMessage("錯誤：無法初始化棋盤 Canvas。");
        if(startButton) startButton.disabled = true;
        return; // Stop initialization if canvas is not found
    }
    ctx.imageSmoothingEnabled = true;
    redrawBoard();
    connectWebSocket();
    canvas.addEventListener('click', handleCanvasClick);

    // 棋譜按鈕事件綁定
    if (updateRecordButton) {
        updateRecordButton.onclick = () => {
            if (webSocket && webSocket.readyState === WebSocket.OPEN) { webSocket.send(JSON.stringify({ type: 'get_game_record' })); setMessage("正在請求棋譜..."); }
            else { setMessage("未連接"); }
        };
    }
    if (copyRecordButton && gameRecordArea) {
        copyRecordButton.onclick = () => {
            if (!gameRecordArea.value) { if (updateRecordButton) updateRecordButton.click(); setMessage("請先更新顯示"); return; } // Auto-update if empty
            navigator.clipboard.writeText(gameRecordArea.value)
                .then(() => { setMessage("棋譜已複製"); copyRecordButton.style.backgroundColor = '#90EE90'; setTimeout(() => { copyRecordButton.style.backgroundColor = ''; }, 1000); })
                .catch(err => { console.error('複製失敗:', err); setMessage("複製失敗"); });
        };
    }
    if (loadFenButton && gameRecordArea) {
        loadFenButton.onclick = () => {
            const content = gameRecordArea.value.trim(); if (!content) { setMessage("請粘貼 FEN"); return; }
            let fenToLoad = ''; const fenMatch = content.match(/\[FEN\s+"([^"]+)"\]/);
            if (fenMatch && fenMatch[1]) fenToLoad = fenMatch[1];
            else { const lines = content.split('\n'); if (lines.length > 0 && lines[0].includes('/')) fenToLoad = lines[0].trim(); }
            if (!fenToLoad) { setMessage("未找到 FEN"); return; }
            if (webSocket && webSocket.readyState === WebSocket.OPEN) { webSocket.send(JSON.stringify({ type: 'load_fen', fen: fenToLoad })); setMessage(`加載 FEN...`); }
            else { setMessage("未連接"); }
        };
    }
});