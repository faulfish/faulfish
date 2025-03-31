// script.js - 前端邏輯 (完整版，適用於本地對弈/雙窗口模式)

// --- DOM 元素引用 ---
const canvas = document.getElementById('xiangqi-board');
const ctx = canvas.getContext('2d');
const messageArea = document.getElementById('message-area');
const turnInfoSpan = document.getElementById('current-turn'); // Renamed for clarity
const playerColorSpan = document.getElementById('player-color'); // To show assigned color
const redTimerDisplay = document.getElementById('red-timer');
const blackTimerDisplay = document.getElementById('black-timer');
const startButton = document.getElementById('start-button');

// --- 棋盤常量 ---
const BOARD_WIDTH = canvas.width;   // 540
const BOARD_HEIGHT = canvas.height; // 600
const COLS = 9;  // 9 列
const ROWS = 10; // 10 行 (包括 9 條橫線和楚河漢界)
const SQUARE_SIZE = BOARD_WIDTH / COLS; // 每格寬度 (540 / 9 = 60)
// 確保 SQUARE_SIZE * ROWS === BOARD_HEIGHT (60 * 10 = 600)
const RIVER_Y_CENTER = BOARD_HEIGHT / 2; // 楚河漢界中心 Y 坐標
const PIECE_RADIUS = SQUARE_SIZE * 0.4; // 棋子繪製半徑 (60 * 0.4 = 24)

// --- 遊戲狀態變量 ---
let boardState = null;      // 由後端發送的棋盤數據 (二維數組)
let selectedPiece = null;   // 當前選中的棋子 { x: col, y: row, piece: {name, color} }
let currentTurn = 'red';    // 當前輪到哪方走棋 (從後端同步)
let gameStarted = false;    // 遊戲是否已開始
let webSocket = null;       // WebSocket 連接對象

// --- 繪圖函數 ---

// 繪製棋盤格線、九宮、楚河漢界
function drawGrid() {
    ctx.strokeStyle = '#6b4e2a'; // 線條顏色
    ctx.lineWidth = 1;

    // 繪製豎線 (分開繪製，避開楚河漢界中間)
    for (let i = 0; i < COLS; i++) {
        const x = i * SQUARE_SIZE + SQUARE_SIZE / 2;
        // 上半部分
        ctx.beginPath();
        ctx.moveTo(x, SQUARE_SIZE / 2);
        ctx.lineTo(x, RIVER_Y_CENTER - SQUARE_SIZE / 2);
        ctx.stroke();
        // 下半部分
        ctx.beginPath();
        ctx.moveTo(x, RIVER_Y_CENTER + SQUARE_SIZE / 2);
        ctx.lineTo(x, BOARD_HEIGHT - SQUARE_SIZE / 2);
        ctx.stroke();
    }

    // 繪製橫線
    for (let i = 0; i < ROWS; i++) {
        const y = i * SQUARE_SIZE + SQUARE_SIZE / 2;
        ctx.beginPath();
        ctx.moveTo(SQUARE_SIZE / 2, y);
        ctx.lineTo(BOARD_WIDTH - SQUARE_SIZE / 2, y);
        ctx.stroke();
    }

    // 繪製楚河漢界文字
    ctx.font = `bold ${SQUARE_SIZE * 0.4}px sans-serif`;
    ctx.fillStyle = '#4a391d';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    const textY = RIVER_Y_CENTER;
    ctx.save();
    ctx.translate(BOARD_WIDTH / 4, textY);
    ctx.rotate(-Math.PI / 2);
    ctx.fillText('楚', 0, 0);
    ctx.restore();
    ctx.save();
    ctx.translate(BOARD_WIDTH / 4 + ctx.measureText('楚').width / 1.5, textY);
    ctx.rotate(-Math.PI / 2);
    ctx.fillText('河', 0, 0);
    ctx.restore();
    ctx.save();
    ctx.translate(BOARD_WIDTH * 3 / 4, textY);
    ctx.rotate(Math.PI / 2);
    ctx.fillText('漢', 0, 0);
    ctx.restore();
    ctx.save();
    ctx.translate(BOARD_WIDTH * 3 / 4 - ctx.measureText('漢').width / 1.5, textY);
    ctx.rotate(Math.PI / 2);
    ctx.fillText('界', 0, 0);
    ctx.restore();

    // 繪製九宮格斜線
    function drawPalaceLine(x1, y1, x2, y2) {
        ctx.beginPath();
        ctx.moveTo(x1 * SQUARE_SIZE + SQUARE_SIZE / 2, y1 * SQUARE_SIZE + SQUARE_SIZE / 2);
        ctx.lineTo(x2 * SQUARE_SIZE + SQUARE_SIZE / 2, y2 * SQUARE_SIZE + SQUARE_SIZE / 2);
        ctx.stroke();
    }
    drawPalaceLine(3, 0, 5, 2);
    drawPalaceLine(5, 0, 3, 2);
    drawPalaceLine(3, 7, 5, 9);
    drawPalaceLine(5, 7, 3, 9);
}

// 根據 boardState 繪製棋子
function drawPieces() {
    if (!boardState) return;

    ctx.font = `bold ${PIECE_RADIUS * 1.2}px sans-serif`;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';

    for (let y = 0; y < ROWS; y++) {
        for (let x = 0; x < COLS; x++) {
            const piece = boardState[y][x];
            if (piece) {
                const drawX = x * SQUARE_SIZE + SQUARE_SIZE / 2;
                const drawY = y * SQUARE_SIZE + SQUARE_SIZE / 2;

                // 繪製棋子外形 (圓形)
                ctx.beginPath();
                ctx.arc(drawX, drawY, PIECE_RADIUS, 0, Math.PI * 2);
                ctx.fillStyle = '#f7e0b8';
                ctx.fill();
                ctx.strokeStyle = piece.color === 'red' ? '#e03030' : '#333';
                ctx.lineWidth = 2;
                ctx.stroke();

                 // 繪製棋子內層邊框
                 ctx.beginPath();
                 ctx.arc(drawX, drawY, PIECE_RADIUS * 0.85, 0, Math.PI * 2);
                 ctx.strokeStyle = piece.color === 'red' ? '#f06060' : '#666';
                 ctx.lineWidth = 1;
                 ctx.stroke();

                // 繪製棋子文字
                ctx.fillStyle = piece.color === 'red' ? 'red' : 'black';
                ctx.fillText(piece.name, drawX, drawY);

                // 如果棋子被選中，繪製高亮邊框
                if (selectedPiece && selectedPiece.x === x && selectedPiece.y === y) {
                    ctx.beginPath();
                    ctx.arc(drawX, drawY, PIECE_RADIUS * 1.05, 0, Math.PI * 2);
                    ctx.strokeStyle = 'gold';
                    ctx.lineWidth = 4;
                    ctx.stroke();
                }
            }
        }
    }
}

// 清空並重新繪製整個棋盤
function redrawBoard() {
    ctx.clearRect(0, 0, BOARD_WIDTH, BOARD_HEIGHT);
    drawGrid();
    drawPieces();
}

// --- 事件處理 ---

// 處理 Canvas 點擊事件
function handleCanvasClick(event) {
    if (!gameStarted) {
        setMessage("遊戲尚未開始");
        return;
    }

    // 本地對弈/雙窗口模式: 不檢查 playerColor 或 currentTurn，允許操作任何一方

    const rect = canvas.getBoundingClientRect();
    const clickX = event.clientX - rect.left;
    const clickY = event.clientY - rect.top;

    const col = Math.floor(clickX / SQUARE_SIZE);
    const row = Math.floor(clickY / SQUARE_SIZE);

    if (col < 0 || col >= COLS || row < 0 || row >= ROWS) return;

    const clickedPieceData = boardState?.[row]?.[col];

    if (selectedPiece) {
        // --- 第二次點擊：嘗試移動 ---
        const moveData = {
            type: 'move',
            from: { x: selectedPiece.x, y: selectedPiece.y },
            to: { x: col, y: row }
        };

        if (webSocket && webSocket.readyState === WebSocket.OPEN) {
            webSocket.send(JSON.stringify(moveData));
            console.log(`窗口 ${playerColorSpan.textContent} 嘗試移動:`, moveData);
        } else {
             setMessage("WebSocket 未連接，無法發送移動");
        }

        selectedPiece = null;
        redrawBoard();

    } else if (clickedPieceData) {
        // --- 第一次點擊：選擇棋子 ---
        selectedPiece = { x: col, y: row, piece: clickedPieceData };
        setMessage("");
        redrawBoard();
    }
}

// --- WebSocket 通信 ---

function connectWebSocket() {
    const wsUrl = 'ws://localhost:8080'; // !!! 再次確認這個地址 !!!
    console.log(`嘗試連接 WebSocket: ${wsUrl}`);
    setMessage("正在連接伺服器...");

    webSocket = new WebSocket(wsUrl);

    webSocket.onopen = () => {
        console.log('WebSocket 連接已建立');
        setMessage("已連接，等待遊戲信息...");
        startButton.textContent = "等待遊戲信息...";
        startButton.disabled = true;
    };

    webSocket.onmessage = (event) => {
        try {
            const message = JSON.parse(event.data);
            console.log('收到消息:', message);

            switch (message.type) {
                case 'assign_info':
                    playerColorSpan.textContent = message.color === 'red' ? '紅方' : '黑方';
                    playerColorSpan.style.color = message.color;
                    boardState = message.board;
                    currentTurn = message.turn;
                    updateTurnInfo();
                    redrawBoard();
                    setMessage("收到遊戲分配，等待開始...");
                    break;
                case 'start_game':
                    gameStarted = true;
                    startButton.textContent = "遊戲進行中";
                    startButton.disabled = true;
                    setMessage(`遊戲開始！輪到 ${currentTurn === 'red' ? '紅方' : '黑方'}`);
                    if (message.timers) updateTimers(message.timers.red, message.timers.black);
                    redrawBoard();
                    break;
                case 'update_state':
                    boardState = message.board;
                    currentTurn = message.turn;
                    updateTurnInfo();
                    if (message.timers) updateTimers(message.timers.red, message.timers.black);
                    selectedPiece = null; // 確保清除選擇
                    redrawBoard();
                    setMessage(message.lastMoveInfo || `輪到 ${currentTurn === 'red' ? '紅方' : '黑方'}`);
                    break;
                case 'illegal_move':
                    setMessage(`非法移動: ${message.reason}`);
                    selectedPiece = null; // 取消選擇
                    redrawBoard(); // 重繪移除高亮
                    // 短暫顯示錯誤提示後恢復輪次提示
                    setTimeout(() => {
                         if (gameStarted && !messageArea.textContent.startsWith('遊戲結束')) { // 避免覆蓋遊戲結束信息
                            setMessage(`輪到 ${currentTurn === 'red' ? '紅方' : '黑方'}`);
                         }
                    }, 1500); // 1.5秒後恢復
                    break;
                case 'game_over':
                    gameStarted = false;
                    setMessage(`遊戲結束! ${message.winner ? (message.winner === 'red' ? '紅方勝！' : '黑方勝！') : '和棋！'} 原因: ${message.reason}`);
                    startButton.textContent = "遊戲已結束";
                    startButton.disabled = true;
                    if (message.timers) updateTimers(message.timers.red, message.timers.black);
                    break;
                case 'timer_update':
                    if (message.timers) updateTimers(message.timers.red, message.timers.black);
                    break;
                 case 'opponent_disconnected':
                     setMessage("提示：另一窗口連接已斷開");
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
        playerColorSpan.textContent = 'N/A';
        playerColorSpan.style.color = 'black';
        turnInfoSpan.textContent = '已斷開';
        startButton.textContent = "連接已斷開";
        startButton.disabled = true;
        updateTimers(null, null); // 清空計時器顯示
        redrawBoard();
    };

    webSocket.onerror = (error) => {
        console.error('WebSocket 錯誤:', error);
        setMessage("WebSocket 連接錯誤，請檢查服務器及控制台");
        startButton.textContent = "連接失敗";
        startButton.disabled = true;
    };
}

// --- 輔助 UI 函數 ---

function setMessage(msg) {
    if (messageArea) messageArea.textContent = msg;
}

function updateTurnInfo() {
    if (turnInfoSpan) {
        turnInfoSpan.textContent = currentTurn === 'red' ? '紅方' : '黑方';
        turnInfoSpan.style.color = currentTurn;
    }
}

function formatTime(seconds) {
    if (seconds === null || seconds === undefined || seconds < 0) return "--:--";
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}

function updateTimers(redSeconds, blackSeconds) {
    if (redTimerDisplay && blackTimerDisplay) {
        redTimerDisplay.textContent = formatTime(redSeconds);
        blackTimerDisplay.textContent = formatTime(blackSeconds);
    }
}

// --- 初始化 ---
// 確保 DOM 加載完成後執行
document.addEventListener('DOMContentLoaded', () => {
    if (canvas && canvas.getContext) {
        redrawBoard();
        connectWebSocket();
        canvas.addEventListener('click', handleCanvasClick);
    } else {
        console.error("無法找到 Canvas 元素或獲取其上下文！");
        setMessage("錯誤：無法初始化棋盤 Canvas。");
        if(startButton) startButton.disabled = true; // 禁用按鈕
    }
});