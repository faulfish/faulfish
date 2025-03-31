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
    // 修正邊界線被畫兩次的問題（上面循環已包含邊界）
    // ctx.strokeRect(SQUARE_SIZE / 2, SQUARE_SIZE / 2, BOARD_WIDTH - SQUARE_SIZE, BOARD_HEIGHT - SQUARE_SIZE); // 畫外框線

    // 繪製橫線
    for (let i = 0; i < ROWS; i++) {
        const y = i * SQUARE_SIZE + SQUARE_SIZE / 2;
        ctx.beginPath();
        ctx.moveTo(SQUARE_SIZE / 2, y);
        ctx.lineTo(BOARD_WIDTH - SQUARE_SIZE / 2, y);
        ctx.stroke();
    }

    // 繪製楚河漢界文字
    ctx.font = `bold ${SQUARE_SIZE * 0.4}px sans-serif`; // 字體大小與格子大小關聯
    ctx.fillStyle = '#4a391d';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle'; // 確保文字垂直居中
    const textY = RIVER_Y_CENTER;
    // 分開寫，避免文字重疊
    ctx.save(); // 保存繪圖狀態
    ctx.translate(BOARD_WIDTH / 4, textY); // 移動到第一個文字位置
    ctx.rotate(-Math.PI / 2); // 旋轉90度
    ctx.fillText('楚', 0, 0);
    ctx.restore(); // 恢復繪圖狀態

    ctx.save();
    ctx.translate(BOARD_WIDTH / 4 + ctx.measureText('楚').width / 1.5, textY); // 調整位置避免重疊
    ctx.rotate(-Math.PI / 2);
    ctx.fillText('河', 0, 0);
    ctx.restore();

    ctx.save();
    ctx.translate(BOARD_WIDTH * 3 / 4, textY);
    ctx.rotate(Math.PI / 2); // 旋轉另一方向
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
    drawPalaceLine(3, 0, 5, 2); // 黑方九宮
    drawPalaceLine(5, 0, 3, 2);
    drawPalaceLine(3, 7, 5, 9); // 紅方九宮
    drawPalaceLine(5, 7, 3, 9);

    // TODO: 添加炮位、兵卒起始位的標記 (小十字或L形短線)
}

// 根據 boardState 繪製棋子
function drawPieces() {
    if (!boardState) return; // 如果還沒有棋盤數據，則不繪製

    ctx.font = `bold ${PIECE_RADIUS * 1.2}px sans-serif`; // 棋子文字大小
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';

    for (let y = 0; y < ROWS; y++) {
        for (let x = 0; x < COLS; x++) {
            const piece = boardState[y][x];
            if (piece) {
                const drawX = x * SQUARE_SIZE + SQUARE_SIZE / 2; // 棋子中心 X
                const drawY = y * SQUARE_SIZE + SQUARE_SIZE / 2; // 棋子中心 Y

                // 繪製棋子外形 (圓形)
                ctx.beginPath();
                ctx.arc(drawX, drawY, PIECE_RADIUS, 0, Math.PI * 2);
                ctx.fillStyle = '#f7e0b8'; // 棋子背景色
                ctx.fill();
                ctx.strokeStyle = piece.color === 'red' ? '#e03030' : '#333'; // 邊框顏色區分
                ctx.lineWidth = 2;
                ctx.stroke();

                 // 繪製棋子內層邊框 (可選，增加立體感)
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
                    ctx.arc(drawX, drawY, PIECE_RADIUS * 1.05, 0, Math.PI * 2); // 稍大一點的圓
                    ctx.strokeStyle = 'gold'; // 高亮顏色
                    ctx.lineWidth = 4; // 高亮線寬
                    ctx.stroke();
                }
            }
        }
    }
}

// 清空並重新繪製整個棋盤
function redrawBoard() {
    ctx.clearRect(0, 0, BOARD_WIDTH, BOARD_HEIGHT); // 清空畫布
    drawGrid();   // 繪製棋盤背景
    drawPieces(); // 繪製棋子
}

// --- 事件處理 ---

// 處理 Canvas 點擊事件
function handleCanvasClick(event) {
    if (!gameStarted) {
        setMessage("遊戲尚未開始");
        return;
    }

    // 本地對弈模式: 不檢查 playerColor 或 currentTurn，允許操作任何一方

    const rect = canvas.getBoundingClientRect();
    const clickX = event.clientX - rect.left;
    const clickY = event.clientY - rect.top;

    // 計算點擊位置對應的棋盤行列 (0-based)
    const col = Math.floor(clickX / SQUARE_SIZE);
    const row = Math.floor(clickY / SQUARE_SIZE);

    // 檢查點擊是否在棋盤有效範圍內
    if (col < 0 || col >= COLS || row < 0 || row >= ROWS) return;

    const clickedPieceData = boardState?.[row]?.[col]; // 獲取點擊位置的棋子數據

    if (selectedPiece) {
        // --- 第二次點擊：嘗試移動或取消選擇 ---
        const moveData = {
            type: 'move',
            from: { x: selectedPiece.x, y: selectedPiece.y },
            to: { x: col, y: row }
        };

        // 將移動請求發送給後端進行驗證（後端會檢查輪次和規則）
        if (webSocket && webSocket.readyState === WebSocket.OPEN) {
            webSocket.send(JSON.stringify(moveData));
            console.log("Attempting move (local mode):", moveData);
        } else {
             setMessage("WebSocket 未連接，無法發送移動");
        }

        selectedPiece = null; // 無論如何先取消選擇狀態，等待後端更新
        redrawBoard(); // 清除高亮

    } else if (clickedPieceData) {
        // --- 第一次點擊：選擇棋子 ---
        selectedPiece = { x: col, y: row, piece: clickedPieceData };
        setMessage(""); // 清除消息
        redrawBoard(); // 高亮選中棋子
    }
    // 如果第一次點擊空地，則無操作
}

// --- WebSocket 通信 ---

function connectWebSocket() {
    // !!! 關鍵: 確保這個地址和端口與你的 server.js 監聽的一致 !!!
    // 如果 server.js 在另一台機器上，需要替換 localhost 為服務器 IP 地址
    const wsUrl = 'ws://localhost:8080';
    console.log(`Attempting to connect to WebSocket at ${wsUrl}`);
    setMessage("正在連接伺服器...");

    webSocket = new WebSocket(wsUrl);

    webSocket.onopen = () => {
        console.log('WebSocket 連接已建立');
        setMessage("已連接，等待對手或遊戲信息...");
        startButton.textContent = "等待遊戲信息...";
        startButton.disabled = true;
        // 你可以在這裡發送一個 'hello' 或 'ready' 消息給後端（如果後端需要）
        // webSocket.send(JSON.stringify({ type: 'client_ready' }));
    };

    webSocket.onmessage = (event) => {
        try {
            const message = JSON.parse(event.data);
            console.log('收到消息:', message);

            switch (message.type) {
                case 'assign_info': // 後端分配顏色和初始狀態
                    // playerColor = message.color; // 可以記錄但不強制使用
                    playerColorSpan.textContent = message.color === 'red' ? '紅方' : '黑方';
                    playerColorSpan.style.color = message.color;
                    boardState = message.board;
                    currentTurn = message.turn;
                    updateTurnInfo();
                    redrawBoard();
                    setMessage("收到遊戲分配，等待開始...");
                    break;
                case 'start_game': // 遊戲開始信號
                    gameStarted = true;
                    startButton.textContent = "遊戲進行中";
                    startButton.disabled = true;
                    setMessage(`遊戲開始！輪到 ${currentTurn === 'red' ? '紅方' : '黑方'}`);
                    if (message.timers) { // 確保後端發送了計時器信息
                        updateTimers(message.timers.red, message.timers.black);
                    }
                    redrawBoard(); // 以防萬一需要重繪
                    break;
                case 'update_state': // 遊戲狀態更新 (移動後)
                    boardState = message.board;
                    currentTurn = message.turn;
                    updateTurnInfo();
                     if (message.timers) {
                        updateTimers(message.timers.red, message.timers.black);
                    }
                    selectedPiece = null; // 移動成功後清除選擇
                    redrawBoard();
                    // 顯示將軍等提示，或默認顯示輪到誰
                    setMessage(message.lastMoveInfo || `輪到 ${currentTurn === 'red' ? '紅方' : '黑方'}`);
                    break;
                case 'illegal_move': // 非法移動反饋
                    setMessage(`非法移動: ${message.reason}`);
                    selectedPiece = null; // 取消選擇
                    redrawBoard(); // 重繪以移除可能的高亮
                    break;
                case 'game_over': // 遊戲結束
                    gameStarted = false;
                    setMessage(`遊戲結束! ${message.winner ? (message.winner === 'red' ? '紅方勝！' : '黑方勝！') : '和棋！'} 原因: ${message.reason}`);
                    startButton.textContent = "遊戲已結束";
                    startButton.disabled = true;
                     if (message.timers) { // 顯示最終時間
                        updateTimers(message.timers.red, message.timers.black);
                    }
                    break;
                case 'timer_update': // 計時器更新
                     if (message.timers) {
                        updateTimers(message.timers.red, message.timers.black);
                     }
                     break;
                 case 'opponent_disconnected': // 對手斷開連接
                     // 在本地模式下可以提示一下，但不一定需要結束遊戲
                     setMessage("提示：另一窗口連接已斷開");
                     // 可以選擇是否禁用按鈕或改變狀態
                     // startButton.textContent = "對手斷開";
                     // startButton.disabled = true;
                     // gameStarted = false; // 可以選擇是否停止遊戲
                     break;
                case 'error': // 後端發送的錯誤消息
                    setMessage(`伺服器錯誤: ${message.content}`);
                    break;
                case 'message': // 後端發送的普通消息
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
        boardState = null; // 清空棋盤狀態
        // playerColor = null;
        playerColorSpan.textContent = 'N/A';
        playerColorSpan.style.color = 'black';
        turnInfoSpan.textContent = '已斷開';
        startButton.textContent = "連接已斷開";
        startButton.disabled = true;
        redrawBoard(); // 重繪空棋盤
    };

    webSocket.onerror = (error) => {
        // !!! 這個回調非常重要，用於診斷連接問題 !!!
        console.error('WebSocket 錯誤:', error);
        setMessage("WebSocket 連接錯誤，請檢查服務器是否運行，以及瀏覽器控制台");
        startButton.textContent = "連接失敗";
        startButton.disabled = true;
    };
}

// --- 輔助 UI 函數 ---

// 設置消息區域文本
function setMessage(msg) {
    if (messageArea) {
        messageArea.textContent = msg;
    } else {
        console.warn("無法找到 messageArea 元素");
    }
}

// 更新輪次顯示
function updateTurnInfo() {
    if (turnInfoSpan) {
        turnInfoSpan.textContent = currentTurn === 'red' ? '紅方' : '黑方';
        turnInfoSpan.style.color = currentTurn;
    } else {
        console.warn("無法找到 current-turn 元素");
    }
}

// 格式化時間 (秒 -> MM:SS)
function formatTime(seconds) {
    if (seconds === null || seconds === undefined || seconds < 0) return "--:--";
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}

// 更新計時器顯示
function updateTimers(redSeconds, blackSeconds) {
    if (redTimerDisplay && blackTimerDisplay) {
        redTimerDisplay.textContent = formatTime(redSeconds);
        blackTimerDisplay.textContent = formatTime(blackSeconds);
    } else {
         console.warn("無法找到計時器顯示元素");
    }
}

// --- 初始化 ---
// 確保在 DOM 完全加載後再執行初始化可能更安全，但對於這個簡單應用，直接執行通常沒問題
if (canvas) {
    redrawBoard(); // 初始繪製棋盤背景
    connectWebSocket(); // 發起 WebSocket 連接
    canvas.addEventListener('click', handleCanvasClick); // 綁定點擊事件監聽器
} else {
    console.error("無法找到 ID 為 'xiangqi-board' 的 Canvas 元素！");
    setMessage("錯誤：無法初始化棋盤 Canvas。");
}

// 可選：添加一個按鈕的點擊事件，用於手動重連或開始新遊戲（需要後端支持）
/*
startButton.onclick = () => {
    if (!webSocket || webSocket.readyState === WebSocket.CLOSED) {
        console.log("嘗試重新連接...");
        connectWebSocket();
    } else if (gameStarted === false) { // 如果遊戲結束了，可以發送開始新遊戲請求
        console.log("請求開始新遊戲...");
        // webSocket.send(JSON.stringify({ type: 'request_new_game' }));
    }
};
*/