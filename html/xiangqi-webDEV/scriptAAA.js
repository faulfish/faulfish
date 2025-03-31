// script.js - 前端邏輯 (完整版，適用於分析板模式)

// --- DOM 元素引用 ---
const canvas = document.getElementById('xiangqi-board');
const ctx = canvas.getContext('2d');
const messageArea = document.getElementById('message-area');
const turnInfoSpan = document.getElementById('current-turn');
const playerColorSpan = document.getElementById('player-color'); // May not be needed for analysis board
const redTimerDisplay = document.getElementById('red-timer');
const blackTimerDisplay = document.getElementById('black-timer');
const startButton = document.getElementById('start-button');

// --- 棋盤常量 ---
const BOARD_WIDTH = canvas.width;
const BOARD_HEIGHT = canvas.height;
const COLS = 9;
const ROWS = 10;
const SQUARE_SIZE = BOARD_WIDTH / COLS;
const RIVER_Y_CENTER = BOARD_HEIGHT / 2;
const PIECE_RADIUS = SQUARE_SIZE * 0.4;

// --- 遊戲狀態變量 ---
let boardState = null;
let selectedPiece = null;
let currentTurn = 'red'; // 界面提示的輪次，會根據實際移動更新
let gameStarted = false;
let webSocket = null;

// --- 繪圖函數 ---
function drawGrid() {
    ctx.strokeStyle = '#6b4e2a';
    ctx.lineWidth = 1;
    for (let i = 0; i < COLS; i++) {
        const x = i * SQUARE_SIZE + SQUARE_SIZE / 2;
        ctx.beginPath(); ctx.moveTo(x, SQUARE_SIZE / 2); ctx.lineTo(x, RIVER_Y_CENTER - SQUARE_SIZE / 2); ctx.stroke();
        ctx.beginPath(); ctx.moveTo(x, RIVER_Y_CENTER + SQUARE_SIZE / 2); ctx.lineTo(x, BOARD_HEIGHT - SQUARE_SIZE / 2); ctx.stroke();
    }
    for (let i = 0; i < ROWS; i++) {
        const y = i * SQUARE_SIZE + SQUARE_SIZE / 2;
        ctx.beginPath(); ctx.moveTo(SQUARE_SIZE / 2, y); ctx.lineTo(BOARD_WIDTH - SQUARE_SIZE / 2, y); ctx.stroke();
    }
    ctx.font = `bold ${SQUARE_SIZE * 0.4}px sans-serif`; ctx.fillStyle = '#4a391d'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    const textY = RIVER_Y_CENTER;
    ctx.save(); ctx.translate(BOARD_WIDTH / 4, textY); ctx.rotate(-Math.PI / 2); ctx.fillText('楚', 0, 0); ctx.restore();
    ctx.save(); ctx.translate(BOARD_WIDTH / 4 + ctx.measureText('楚').width / 1.5, textY); ctx.rotate(-Math.PI / 2); ctx.fillText('河', 0, 0); ctx.restore();
    ctx.save(); ctx.translate(BOARD_WIDTH * 3 / 4, textY); ctx.rotate(Math.PI / 2); ctx.fillText('漢', 0, 0); ctx.restore();
    ctx.save(); ctx.translate(BOARD_WIDTH * 3 / 4 - ctx.measureText('漢').width / 1.5, textY); ctx.rotate(Math.PI / 2); ctx.fillText('界', 0, 0); ctx.restore();
    function drawPalaceLine(x1, y1, x2, y2) {
        ctx.beginPath(); ctx.moveTo(x1*SQUARE_SIZE+SQUARE_SIZE/2, y1*SQUARE_SIZE+SQUARE_SIZE/2); ctx.lineTo(x2*SQUARE_SIZE+SQUARE_SIZE/2, y2*SQUARE_SIZE+SQUARE_SIZE/2); ctx.stroke();
    }
    drawPalaceLine(3, 0, 5, 2); drawPalaceLine(5, 0, 3, 2); drawPalaceLine(3, 7, 5, 9); drawPalaceLine(5, 7, 3, 9);
}

function drawPieces() {
    if (!boardState) return;
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

function redrawBoard() {
    ctx.clearRect(0, 0, BOARD_WIDTH, BOARD_HEIGHT);
    drawGrid();
    drawPieces();
}

// --- 事件處理 ---
function handleCanvasClick(event) {
    // 分析板模式下，只要連接成功就可以操作
    if (!webSocket || webSocket.readyState !== WebSocket.OPEN) {
         setMessage("未連接到伺服器");
         return;
    }
     // 遊戲是否 '開始' 在分析板模式下不那麼重要，但後端可能仍會發送 start_game
    // if (!gameStarted) { setMessage("遊戲尚未開始 (等待後端信號)"); return; }

    const rect = canvas.getBoundingClientRect();
    const clickX = event.clientX - rect.left;
    const clickY = event.clientY - rect.top;
    const col = Math.floor(clickX / SQUARE_SIZE);
    const row = Math.floor(clickY / SQUARE_SIZE);

    if (col < 0 || col >= COLS || row < 0 || row >= ROWS) return;

    const clickedPieceData = boardState?.[row]?.[col];

    if (selectedPiece) {
        const moveData = { type: 'move', from: { x: selectedPiece.x, y: selectedPiece.y }, to: { x: col, y: row } };
        webSocket.send(JSON.stringify(moveData));
        console.log("分析板: 嘗試移動:", moveData);
        selectedPiece = null;
        redrawBoard(); // 清除高亮，等待後端確認
    } else if (clickedPieceData) {
        selectedPiece = { x: col, y: row, piece: clickedPieceData };
        setMessage(""); // 清空消息，準備移動
        redrawBoard(); // 高亮選擇
    }
}

// --- WebSocket 通信 ---
function connectWebSocket() {
    const wsUrl = 'ws://localhost:8080'; // !!! 確認地址 !!!
    console.log(`嘗試連接 WebSocket: ${wsUrl}`);
    setMessage("正在連接伺服器...");
    if (startButton) startButton.disabled = true;

    webSocket = new WebSocket(wsUrl);

    webSocket.onopen = () => {
        console.log('WebSocket 連接已建立');
        setMessage("已連接，等待棋盤信息...");
        if (startButton) startButton.textContent = "已連接";
    };

    webSocket.onmessage = (event) => {
        try {
            const message = JSON.parse(event.data);
            console.log('收到消息:', message);

            switch (message.type) {
                case 'assign_info': // 後端仍然可能分配顏色，但在分析板模式下前端忽略
                    if (playerColorSpan) { // 如果還保留了顯示元素
                        playerColorSpan.textContent = message.color === 'red' ? '紅方' : '黑方';
                        playerColorSpan.style.color = message.color;
                    }
                    boardState = message.board;
                    currentTurn = message.turn; // 記錄後端認為的輪次
                    updateTurnInfo();
                    redrawBoard();
                    setMessage("收到棋盤信息");
                    // 分析板模式下，收到棋盤就可以開始操作了
                    gameStarted = true; // 標記可以開始點擊
                    if (startButton) startButton.textContent = "分析中...";
                    break;
                case 'start_game': // 後端可能仍然發送開始信號
                    gameStarted = true;
                    if (startButton) startButton.textContent = "分析中...";
                    setMessage(`遊戲信號已開始，輪到 ${currentTurn === 'red' ? '紅方' : '黑方'} (提示)`);
                    if (message.timers) updateTimers(message.timers.red, message.timers.black);
                    redrawBoard();
                    break;
                case 'update_state': // 棋盤狀態更新
                    boardState = message.board;
                    currentTurn = message.turn; // 更新提示輪次
                    updateTurnInfo();
                    if (message.timers) updateTimers(message.timers.red, message.timers.black);
                    selectedPiece = null; // 清除選擇
                    redrawBoard();
                    setMessage(message.lastMoveInfo || `輪到 ${currentTurn === 'red' ? '紅方' : '黑方'} (提示)`);
                    break;
                case 'illegal_move': // 移動不符合規則 (非輪次錯誤，而是走法錯誤或自將)
                    setMessage(`非法移動: ${message.reason}`);
                    selectedPiece = null;
                    redrawBoard();
                    setTimeout(() => { // 短暫顯示錯誤後恢復提示
                         if (gameStarted && messageArea.textContent.startsWith('非法移動')) {
                             setMessage(`輪到 ${currentTurn === 'red' ? '紅方' : '黑方'} (提示)`);
                         }
                    }, 1500);
                    break;
                case 'game_over': // 將死或困斃等
                    gameStarted = false; // 停止操作
                    setMessage(`遊戲結束! ${message.winner ? (message.winner === 'red' ? '紅方勝！' : '黑方勝！') : '和棋！'} 原因: ${message.reason}`);
                    if (startButton) startButton.textContent = "遊戲已結束";
                    if (startButton) startButton.disabled = true; // 禁用按鈕直到重置
                    if (message.timers) updateTimers(message.timers.red, message.timers.black);
                    break;
                case 'timer_update':
                    if (message.timers) updateTimers(message.timers.red, message.timers.black);
                    break;
                 case 'opponent_disconnected': // 在分析板模式下通常無意義
                     // setMessage("提示：另一連接已斷開");
                     break;
                case 'error':
                    setMessage(`伺服器錯誤: ${message.content}`);
                    break;
                case 'message':
                    setMessage(message.content);
                    break;
                default:
                    console.warn('收到未知的消息類型:', message.type);
            }
        } catch (error) {
            console.error('處理 WebSocket 消息時出錯:', error, '原始數據:', event.data);
            setMessage("處理伺服器消息時發生錯誤");
        }
    };

    webSocket.onclose = (event) => {
        console.log('WebSocket 連接已關閉。 Code:', event.code, 'Reason:', event.reason);
        setMessage("與伺服器斷開連接");
        gameStarted = false;
        boardState = null;
        if (playerColorSpan) { playerColorSpan.textContent = 'N/A'; playerColorSpan.style.color = 'black';}
        if (turnInfoSpan) turnInfoSpan.textContent = '已斷開';
        if (startButton) startButton.textContent = "連接已斷開";
        if (startButton) startButton.disabled = true;
        updateTimers(null, null);
        redrawBoard(); // 重繪空棋盤
    };

    webSocket.onerror = (error) => {
        console.error('WebSocket 錯誤:', error);
        setMessage("WebSocket 連接錯誤");
        if (startButton) startButton.textContent = "連接失敗";
        if (startButton) startButton.disabled = true;
    };
}

// --- 輔助 UI 函數 ---
function setMessage(msg) { if (messageArea) messageArea.textContent = msg; }
function updateTurnInfo() { if (turnInfoSpan) { turnInfoSpan.textContent = currentTurn === 'red' ? '紅方' : '黑方'; turnInfoSpan.style.color = currentTurn; } }
function formatTime(seconds) { if (seconds === null || seconds === undefined || seconds < 0) return "--:--"; const mins = Math.floor(seconds / 60); const secs = Math.floor(seconds % 60); return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`; }
function updateTimers(redSeconds, blackSeconds) { if (redTimerDisplay && blackTimerDisplay) { redTimerDisplay.textContent = formatTime(redSeconds); blackTimerDisplay.textContent = formatTime(blackSeconds); } }

// --- 初始化 ---
document.addEventListener('DOMContentLoaded', () => {
    if (canvas && canvas.getContext) {
        ctx.imageSmoothingEnabled = true; // 嘗試啟用平滑
        redrawBoard();
        connectWebSocket();
        canvas.addEventListener('click', handleCanvasClick);
    } else {
        console.error("無法找到 Canvas 元素！");
        setMessage("錯誤：無法初始化棋盤 Canvas。");
        if(startButton) startButton.disabled = true;
    }
});