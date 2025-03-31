const canvas = document.getElementById('xiangqi-board');
const ctx = canvas.getContext('2d');
const messageArea = document.getElementById('message-area');
const turnInfo = document.getElementById('current-turn');
const playerColorDisplay = document.getElementById('player-color');
const redTimerDisplay = document.getElementById('red-timer');
const blackTimerDisplay = document.getElementById('black-timer');
const startButton = document.getElementById('start-button');

// --- 棋盤參數 ---
const BOARD_WIDTH = canvas.width;
const BOARD_HEIGHT = canvas.height;
const ROWS = 10; // 9 條橫線 + 楚河漢界 = 10 行
const COLS = 9;  // 8 條豎線 = 9 列
const SQUARE_SIZE = BOARD_WIDTH / COLS;
const RIVER_Y = BOARD_HEIGHT / 2;
const PIECE_RADIUS = SQUARE_SIZE * 0.4; // 棋子半徑

// --- 遊戲狀態 ---
let boardState = null; // 將從服務器獲取
let selectedPiece = null; // { x: col, y: row, piece: '俥' }
let playerColor = null; // 'red' or 'black'
let currentTurn = 'red'; // 初始為紅方
let gameStarted = false;
let webSocket = null;

// --- 繪圖函數 ---
function drawGrid() {
    ctx.strokeStyle = '#6b4e2a'; // 線條顏色
    ctx.lineWidth = 1;

    // 繪製豎線
    for (let i = 0; i < COLS; i++) {
        ctx.beginPath();
        ctx.moveTo(i * SQUARE_SIZE + SQUARE_SIZE / 2, SQUARE_SIZE / 2);
        ctx.lineTo(i * SQUARE_SIZE + SQUARE_SIZE / 2, RIVER_Y - SQUARE_SIZE / 2);
        ctx.stroke();
        ctx.beginPath();
        ctx.moveTo(i * SQUARE_SIZE + SQUARE_SIZE / 2, RIVER_Y + SQUARE_SIZE / 2);
        ctx.lineTo(i * SQUARE_SIZE + SQUARE_SIZE / 2, BOARD_HEIGHT - SQUARE_SIZE / 2);
        ctx.stroke();
    }
    // 最外側的兩條豎線補全
    ctx.beginPath();
    ctx.moveTo(SQUARE_SIZE / 2, SQUARE_SIZE / 2);
    ctx.lineTo(SQUARE_SIZE / 2, BOARD_HEIGHT - SQUARE_SIZE / 2);
    ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(BOARD_WIDTH - SQUARE_SIZE / 2, SQUARE_SIZE / 2);
    ctx.lineTo(BOARD_WIDTH - SQUARE_SIZE / 2, BOARD_HEIGHT - SQUARE_SIZE / 2);
    ctx.stroke();


    // 繪製橫線
    for (let i = 0; i < ROWS; i++) {
        ctx.beginPath();
        ctx.moveTo(SQUARE_SIZE / 2, i * SQUARE_SIZE + SQUARE_SIZE / 2);
        ctx.lineTo(BOARD_WIDTH - SQUARE_SIZE / 2, i * SQUARE_SIZE + SQUARE_SIZE / 2);
        ctx.stroke();
    }

    // 繪製楚河漢界 (文字) - 簡單版本
    ctx.font = 'bold 24px sans-serif';
    ctx.fillStyle = '#4a391d';
    ctx.textAlign = 'center';
    ctx.fillText('楚 河', BOARD_WIDTH / 4, RIVER_Y + 5);
    ctx.fillText('漢 界', BOARD_WIDTH * 3 / 4, RIVER_Y + 5);

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

function drawPieces() {
    if (!boardState) return;
    ctx.font = `${PIECE_RADIUS * 1.5}px sans-serif`; // 調整字體大小
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';

    for (let y = 0; y < ROWS; y++) {
        for (let x = 0; x < COLS; x++) {
            const piece = boardState[y][x];
            if (piece) {
                const drawX = x * SQUARE_SIZE + SQUARE_SIZE / 2;
                const drawY = y * SQUARE_SIZE + SQUARE_SIZE / 2;

                // 繪製棋子背景
                ctx.fillStyle = '#f7e0b8'; // 棋子背景色
                ctx.beginPath();
                ctx.arc(drawX, drawY, PIECE_RADIUS, 0, Math.PI * 2);
                ctx.fill();
                ctx.strokeStyle = '#555'; // 棋子邊框
                ctx.lineWidth = 1;
                ctx.stroke();

                // 繪製棋子文字
                ctx.fillStyle = piece.color === 'red' ? 'red' : 'black';
                ctx.fillText(piece.name, drawX, drawY);

                // 高亮選中棋子
                if (selectedPiece && selectedPiece.x === x && selectedPiece.y === y) {
                    ctx.strokeStyle = 'gold';
                    ctx.lineWidth = 3;
                    ctx.stroke();
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
    if (!gameStarted || !playerColor || currentTurn !== playerColor) {
        setMessage(currentTurn !== playerColor ? "還沒輪到你!" : "遊戲尚未開始或未分配顏色");
        return; // 不是你的回合或遊戲未開始
    }

    const rect = canvas.getBoundingClientRect();
    const clickX = event.clientX - rect.left;
    const clickY = event.clientY - rect.top;

    const col = Math.floor(clickX / SQUARE_SIZE);
    const row = Math.floor(clickY / SQUARE_SIZE);

    // 檢查點擊是否在棋盤內有效交叉點附近 (簡化判斷)
    if (col < 0 || col >= COLS || row < 0 || row >= ROWS) return;

    const clickedPiece = boardState[row][col];

    if (selectedPiece) {
        // --- 嘗試移動 ---
        const moveData = {
            type: 'move',
            from: { x: selectedPiece.x, y: selectedPiece.y },
            to: { x: col, y: row }
        };
        // **前端不做完整規則檢查，發送給後端驗證**
        webSocket.send(JSON.stringify(moveData));
        console.log("Attempting move:", moveData);
        selectedPiece = null; // 無論成功失敗，先取消選中狀態，等待後端更新
        redrawBoard(); // 清除高亮

    } else if (clickedPiece && clickedPiece.color === playerColor) {
        // --- 選擇棋子 ---
        selectedPiece = { x: col, y: row, piece: clickedPiece };
        setMessage(""); // 清除之前的消息
        redrawBoard(); // 高亮選中
    } else {
         setMessage("請選擇你的棋子");
    }
}

// --- WebSocket 通信 ---
function connectWebSocket() {
    // **重要:** 將 'localhost' 替換為你的伺服器實際 IP 地址或域名
    webSocket = new WebSocket('ws://localhost:8080');

    webSocket.onopen = () => {
        console.log('WebSocket 連接已建立');
        setMessage("已連接到伺服器，等待對手...");
        // 你可以在這裡發送一個 'join' 或 'ready' 消息
        // webSocket.send(JSON.stringify({ type: 'player_ready' }));
    };

    webSocket.onmessage = (event) => {
        try {
            const message = JSON.parse(event.data);
            console.log('收到消息:', message);

            switch (message.type) {
                case 'assign_info':
                    playerColor = message.color;
                    playerColorDisplay.textContent = playerColor === 'red' ? '紅方' : '黑方';
                    playerColorDisplay.style.color = playerColor;
                    boardState = message.board; // 初始棋盤
                    currentTurn = message.turn;
                    updateTurnInfo();
                    redrawBoard();
                    break;
                case 'start_game':
                    gameStarted = true;
                    startButton.textContent = "遊戲進行中";
                    startButton.disabled = true;
                    setMessage(`遊戲開始！你是 ${playerColor === 'red' ? '紅方' : '黑方'}`);
                    updateTimers(message.timers.red, message.timers.black);
                    break;
                case 'update_state':
                    boardState = message.board;
                    currentTurn = message.turn;
                    updateTurnInfo();
                    updateTimers(message.timers.red, message.timers.black);
                    selectedPiece = null; // 移動成功後清除選擇
                    redrawBoard();
                    setMessage(message.lastMoveInfo || ""); // 顯示將軍等信息
                    break;
                case 'illegal_move':
                    setMessage(`非法移動: ${message.reason}`);
                    selectedPiece = null; // 非法移動後取消選擇
                    redrawBoard();
                    break;
                case 'game_over':
                    gameStarted = false;
                    setMessage(`遊戲結束! ${message.winner ? (message.winner === playerColor ? '你贏了！' : '你輸了！') : '和棋！'} 原因: ${message.reason}`);
                    startButton.textContent = "重新開始?"; // 或類似
                    startButton.disabled = false; // 允許重新開始 (需要後端支持)
                    break;
                case 'timer_update': // 只更新時間
                     updateTimers(message.timers.red, message.timers.black);
                     break;
                 case 'opponent_disconnected':
                     gameStarted = false;
                     setMessage("對手已斷開連接。");
                     startButton.textContent = "等待對手...";
                     startButton.disabled = true;
                     break;
                case 'error':
                    setMessage(`錯誤: ${message.content}`);
                    break;
                default:
                    console.warn('未知的消息類型:', message.type);
            }
        } catch (error) {
            console.error('處理消息時出錯:', error);
            setMessage("收到無法解析的消息");
        }
    };

    webSocket.onclose = () => {
        console.log('WebSocket 連接已關閉');
        setMessage("與伺服器斷開連接，請刷新頁面重試");
        gameStarted = false;
        playerColor = null;
        startButton.textContent = "連接已斷開";
        startButton.disabled = true;
    };

    webSocket.onerror = (error) => {
        console.error('WebSocket 錯誤:', error);
        setMessage("WebSocket 連接錯誤");
    };
}

// --- 輔助函數 ---
function setMessage(msg) {
    messageArea.textContent = msg;
}

function updateTurnInfo() {
    turnInfo.textContent = currentTurn === 'red' ? '紅方' : '黑方';
    turnInfo.style.color = currentTurn;
}

function formatTime(seconds) {
    if (seconds === null || seconds === undefined || seconds < 0) return "--:--";
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}

function updateTimers(redSeconds, blackSeconds) {
    redTimerDisplay.textContent = formatTime(redSeconds);
    blackTimerDisplay.textContent = formatTime(blackSeconds);
}


// --- 初始化 ---
redrawBoard(); // 初始繪製空棋盤
connectWebSocket();
canvas.addEventListener('click', handleCanvasClick);

// startButton.onclick = () => { /* 可以添加重新開始遊戲的邏輯 */ };