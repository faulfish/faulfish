// script.js (修改後的部分)

// ... (頂部的變量定義和繪圖函數不變) ...

// --- 遊戲狀態 ---
let boardState = null;
let selectedPiece = null; // { x: col, y: row, piece: '俥' }
// let playerColor = null; // 這個變量現在主要用於顯示，不再用於驗證
let currentTurn = 'red'; // 仍然從後端同步
let gameStarted = false;
let webSocket = null;

// ... (繪圖函數 drawGrid, drawPieces, redrawBoard 不變) ...


// --- 事件處理 (核心修改點) ---
function handleCanvasClick(event) {
    // 只檢查遊戲是否已開始 (從後端接收到 start_game)
    if (!gameStarted) {
        setMessage("遊戲尚未開始");
        return;
    }

    // --- 移除前端對走棋方和顏色的限制 ---
    /*
    // 舊的限制邏輯:
    if (!playerColor || currentTurn !== playerColor) {
        setMessage(currentTurn !== playerColor ? "還沒輪到你!" : "尚未分配顏色或輪次");
        return;
    }
    */

    const rect = canvas.getBoundingClientRect();
    const clickX = event.clientX - rect.left;
    const clickY = event.clientY - rect.top;

    const col = Math.floor(clickX / SQUARE_SIZE);
    const row = Math.floor(clickY / SQUARE_SIZE);

    if (col < 0 || col >= COLS || row < 0 || row >= ROWS) return; // 點擊在棋盤外

    const clickedPieceData = boardState[row]?.[col]; // 安全獲取點擊位置的棋子數據

    if (selectedPiece) {
        // --- 嘗試移動 (無論點擊的是空格、對方棋子還是己方棋子) ---
        // 後端會驗證目標點是否合法 (不能吃自己子) 和走法是否合規
        const moveData = {
            type: 'move',
            from: { x: selectedPiece.x, y: selectedPiece.y },
            to: { x: col, y: row }
        };
        // 將移動請求發送給後端進行驗證
        webSocket.send(JSON.stringify(moveData));
        console.log("Attempting move (local mode):", moveData);
        selectedPiece = null; // 清除選擇，等待後端響應
        redrawBoard(); // 清除高亮

    } else if (clickedPieceData) {
        // --- 選擇棋子 (允許選擇任何一方的棋子) ---
        selectedPiece = { x: col, y: row, piece: clickedPieceData };
        setMessage(""); // 清除之前的消息
        redrawBoard(); // 高亮選中
    }
    // 如果點擊空地且未選中棋子，則無操作
}


// --- WebSocket 通信 ---
function connectWebSocket() {
    webSocket = new WebSocket('ws://localhost:8080'); // 確保地址正確

    webSocket.onopen = () => {
        console.log('WebSocket 連接已建立');
        // 注意：即使是本地模式，仍需要連接後端來獲取初始狀態和驗證走法
        setMessage("已連接到伺服器，等待遊戲信息...");
        startButton.textContent = "等待遊戲信息...";
        startButton.disabled = true;
    };

    webSocket.onmessage = (event) => {
        try {
            const message = JSON.parse(event.data);
            console.log('收到消息:', message);

            switch (message.type) {
                case 'assign_info':
                    // playerColor = message.color; // 記錄顏色，但不再用於強制限制
                    // playerColorDisplay.textContent = playerColor === 'red' ? '紅方' : '黑方'; // 如果保留顯示，則更新
                    // playerColorDisplay.style.color = playerColor;
                    boardState = message.board;
                    currentTurn = message.turn; // 同步當前輪次
                    updateTurnInfo();
                    redrawBoard();
                    setMessage("收到遊戲信息，等待開始信號...");
                    break;
                case 'start_game':
                    gameStarted = true;
                    startButton.textContent = "遊戲進行中";
                    startButton.disabled = true;
                    setMessage(`遊戲開始！輪到 ${currentTurn === 'red' ? '紅方' : '黑方'}`);
                    updateTimers(message.timers.red, message.timers.black);
                    break;
                case 'update_state':
                    boardState = message.board;
                    currentTurn = message.turn; // 更新當前輪次
                    updateTurnInfo();
                    updateTimers(message.timers.red, message.timers.black);
                    selectedPiece = null; // 確保移動後取消選擇
                    redrawBoard();
                    // 顯示後端返回的提示信息 (例如將軍)
                    setMessage(message.lastMoveInfo || `輪到 ${currentTurn === 'red' ? '紅方' : '黑方'}`);
                    break;
                case 'illegal_move':
                    // 即使前端允許操作，後端驗證不通過時仍會收到此消息
                    setMessage(`非法移動: ${message.reason}`);
                    selectedPiece = null; // 非法移動後取消選擇
                    redrawBoard();
                    break;
                case 'game_over':
                    gameStarted = false;
                    setMessage(`遊戲結束! ${message.winner ? (message.winner === 'red' ? '紅方勝！' : '黑方勝！') : '和棋！'} 原因: ${message.reason}`);
                    startButton.textContent = "遊戲已結束";
                    startButton.disabled = true;
                    break;
                case 'timer_update':
                     updateTimers(message.timers.red, message.timers.black);
                     break;
                 case 'opponent_disconnected': // 在本地模式下這個消息意義不大，但可以保留
                     // gameStarted = false;
                     setMessage("收到對手斷開信息 (本地模式下可忽略)");
                     // startButton.textContent = "等待對手...";
                     // startButton.disabled = true;
                     break;
                case 'error':
                    setMessage(`錯誤: ${message.content}`);
                    break;
                // 增加一個處理簡單消息的 case (如果後端有發送的話)
                case 'message':
                    setMessage(message.content);
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
        setMessage("與伺服器斷開連接");
        gameStarted = false;
        // playerColor = null;
        startButton.textContent = "連接已斷開";
        startButton.disabled = true;
    };

    webSocket.onerror = (error) => {
        console.error('WebSocket 錯誤:', error);
        setMessage("WebSocket 連接錯誤");
    };
}

// --- 輔助函數 (setMessage, updateTurnInfo, formatTime, updateTimers 不變) ---
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
redrawBoard(); // 初始繪製空棋盤 (或等待後端數據)
connectWebSocket(); // 連接後端
canvas.addEventListener('click', handleCanvasClick); // 綁定點擊事件

// startButton.onclick = () => { /* 可能需要重置遊戲狀態的邏輯 */ };