// server.js (修改為分析板模式)

const WebSocket = require('ws');
const XiangqiRules = require('./rules.js'); // 引入規則模塊

const wss = new WebSocket.Server({ port: 8080 });
console.log('WebSocket 伺服器 (分析板模式) 正在監聽端口 8080...');

let gameIdCounter = 0;
const games = {}; // 存儲活躍遊戲

// --- 初始棋盤 ---
function getInitialBoard() {
    return [
        [{name:'車', color:'black'}, {name:'馬', color:'black'}, {name:'象', color:'black'}, {name:'士', color:'black'}, {name:'將', color:'black'}, {name:'士', color:'black'}, {name:'象', color:'black'}, {name:'馬', color:'black'}, {name:'車', color:'black'}],
        [null, null, null, null, null, null, null, null, null],
        [null, {name:'炮', color:'black'}, null, null, null, null, null, {name:'炮', color:'black'}, null],
        [{name:'卒', color:'black'}, null, {name:'卒', color:'black'}, null, {name:'卒', color:'black'}, null, {name:'卒', color:'black'}, null, {name:'卒', color:'black'}],
        [null, null, null, null, null, null, null, null, null],
        [null, null, null, null, null, null, null, null, null],
        [{name:'兵', color:'red'}, null, {name:'兵', color:'red'}, null, {name:'兵', color:'red'}, null, {name:'兵', color:'red'}, null, {name:'兵', color:'red'}],
        [null, {name:'炮', color:'red'}, null, null, null, null, null, {name:'炮', color:'red'}, null],
        [null, null, null, null, null, null, null, null, null],
        [{name:'俥', color:'red'}, {name:'傌', color:'red'}, {name:'相', color:'red'}, {name:'仕', color:'red'}, {name:'帥', color:'red'}, {name:'仕', color:'red'}, {name:'相', color:'red'}, {name:'傌', color:'red'}, {name:'俥', color:'red'}]
    ];
}

// --- 遊戲狀態 ---
function createNewGame(player1Ws, player2Ws) {
    const gameId = ++gameIdCounter;
    const gameState = {
        id: gameId,
        board: getInitialBoard(),
        turn: 'red', // 初始輪次提示
        // 分析板模式下，players 列表可能只需要維護連接即可
        clients: [player1Ws], // 用 clients 數組存儲所有連接
        // timers: { red: 1200, black: 1200, increment: 5, lastMoveTimestamp: null, timerInterval: null }, // 計時器可選
        gameOver: false,
        winner: null,
        reason: '',
        history: []
    };
    games[gameId] = gameState;
    player1Ws.gameId = gameId;
    // 分配顏色可能不再嚴格需要，但可以保留以便客戶端顯示
    player1Ws.playerColor = 'red';
    if (player2Ws) {
        gameState.clients.push(player2Ws);
        player2Ws.gameId = gameId;
        player2Ws.playerColor = 'black';
    }
    console.log(`創建/加入遊戲 ${gameId}, 當前客戶端數: ${gameState.clients.length}`);
    return gameState;
}

// --- 時間管理 (可選) ---
function stopTimer(gameState) { /* ... */ }
function startTimer(gameState) { /* ... */ }

// --- 消息廣播 ---
function broadcast(gameId, message) {
    const game = games[gameId];
    if (!game || !game.clients) return;
    const messageString = JSON.stringify(message);
    // 過濾掉已關閉的連接
    game.clients = game.clients.filter(client => client.readyState === WebSocket.OPEN);
    game.clients.forEach(client => {
        client.send(messageString);
    });
}

function broadcastGameOver(gameState) {
    // stopTimer(gameState); // 如果使用計時器
    broadcast(gameState.id, {
        type: 'game_over',
        winner: gameState.winner,
        reason: gameState.reason
    });
    console.log(`遊戲 ${gameState.id} 結束: ${gameState.reason}`);
}

// --- WebSocket 連接處理 ---
// 分析板模式下，允許多個客戶端連接到同一個遊戲實例
let analysisGameId = null; // 可以只維護一個全局分析板遊戲

wss.on('connection', (ws) => {
    console.log('一個客戶端已連接 (分析板)');

    let gameState;
    if (analysisGameId === null || !games[analysisGameId]) {
        // 創建第一個分析板遊戲
        gameState = createNewGame(ws, null);
        analysisGameId = gameState.id;
        // 立刻發送狀態給第一個連接者
        ws.send(JSON.stringify({ type: 'assign_info', color: 'red', board: gameState.board, turn: gameState.turn }));
        // 可以直接開始
        setTimeout(() => ws.send(JSON.stringify({ type: 'start_game' })), 100);

    } else {
        // 加入已存在的分析板遊戲
        gameState = games[analysisGameId];
        ws.gameId = analysisGameId;
        gameState.clients.push(ws); // 添加到客戶端列表
        // 分配一個顏色給它（用於界面顯示，非強制）
        ws.playerColor = gameState.clients.length % 2 === 0 ? 'black' : 'red'; // 交替分配
        console.log(`客戶端加入遊戲 ${analysisGameId}, 當前客戶端數: ${gameState.clients.length}`);
        // 發送當前狀態給新連接者
        ws.send(JSON.stringify({ type: 'assign_info', color: ws.playerColor, board: gameState.board, turn: gameState.turn }));
        // 如果遊戲已開始，也發送開始信號
        if (gameState.clients.length > 0) { // 只要有客戶端就認為是開始狀態
             setTimeout(() => ws.send(JSON.stringify({ type: 'start_game' })), 100);
        }
    }


    // --- 處理來自客戶端的消息 ---
    ws.on('message', (message) => {
        try {
            const data = JSON.parse(message);
            const gameId = ws.gameId;

            if (!gameId || !games[gameId]) {
                 console.warn("收到來自無效遊戲客戶端的消息"); return;
            }
            const currentGameState = games[gameId]; // 使用 currentGameState 避免與外層 gameState 混淆

            if (currentGameState.gameOver) { return; } // 遊戲已結束

            console.log(`收到來自 Game ${gameId} 的消息:`, data);

            if (data.type === 'move') {
                const { from, to } = data;
                const pieceToMove = currentGameState.board[from.y]?.[from.x];

                if (!pieceToMove) {
                    ws.send(JSON.stringify({ type: 'illegal_move', reason: "起始位置無棋子" })); return;
                }

                // *** 分析板核心：調用不檢查輪次的驗證 ***
                const validationResult = XiangqiRules.isValidMoveInternal(currentGameState.board, from, to, pieceToMove.color);

                if (validationResult.valid) {
                    // 移動有效
                    // stopTimer(currentGameState); // 可選
                    // if (currentGameState.timers) currentGameState.timers[pieceToMove.color] += currentGameState.timers.increment; // 可選

                    const movedPiece = currentGameState.board[from.y][from.x];
                    const targetPiece = currentGameState.board[to.y][to.x];
                    currentGameState.board[to.y][to.x] = movedPiece;
                    currentGameState.board[from.y][from.x] = null;
                    currentGameState.history.push({ from, to, piece: movedPiece.name, color: movedPiece.color, captured: targetPiece ? targetPiece.name : null });

                    // 更新界面提示輪次
                    currentGameState.turn = pieceToMove.color === 'red' ? 'black' : 'red';

                    // 檢查對方是否被將死或困斃
                    let checkInfo = "";
                    const opponentColor = currentGameState.turn;
                    if (XiangqiRules.isKingInCheck(currentGameState.board, opponentColor)) {
                        checkInfo = `${opponentColor === 'red' ? '紅方' : '黑方'} 被將軍!`;
                        if (XiangqiRules.isCheckmate(currentGameState.board, opponentColor)) {
                            currentGameState.gameOver = true;
                            currentGameState.winner = pieceToMove.color;
                            currentGameState.reason = "絕殺";
                        }
                    } else {
                        if (XiangqiRules.isStalemate(currentGameState.board, opponentColor)) {
                            currentGameState.gameOver = true;
                            currentGameState.winner = null;
                            currentGameState.reason = "困斃和棋";
                        }
                    }
                    // TODO: 其他和棋規則

                    if (currentGameState.gameOver) {
                         broadcast(gameId, { type: 'update_state', board: currentGameState.board, turn: currentGameState.turn, lastMoveInfo: checkInfo }); // 先更新最後一步
                         setTimeout(() => broadcastGameOver(currentGameState), 100); // 再發送結束
                    } else {
                        // 廣播新狀態
                        broadcast(gameId, {
                            type: 'update_state',
                            board: currentGameState.board,
                            turn: currentGameState.turn,
                            // timers: currentGameState.timers, // 可選
                            lastMoveInfo: checkInfo
                        });
                        // startTimer(currentGameState); // 可選
                    }
                } else {
                    // 移動非法 (走法錯誤或自將)
                    ws.send(JSON.stringify({ type: 'illegal_move', reason: validationResult.reason }));
                }
            }
            // ... 其他消息類型 ...
        } catch (error) {
            console.error('處理消息錯誤:', error);
            ws.send(JSON.stringify({ type: 'error', content: '伺服器處理消息出錯' }));
        }
    });

    // --- 連接關閉 ---
    ws.on('close', () => {
        console.log('一個客戶端已斷開連接 (分析板)');
        const gameId = ws.gameId;
        if (gameId && games[gameId]) {
            const currentGameState = games[gameId];
            // 從客戶端列表中移除
            currentGameState.clients = currentGameState.clients.filter(client => client !== ws);
            console.log(`客戶端離開遊戲 ${gameId}, 剩餘客戶端數: ${currentGameState.clients.length}`);
            // 可選：如果所有客戶端都離開了，可以考慮重置或刪除遊戲
            if (currentGameState.clients.length === 0) {
                 console.log(`遊戲 ${gameId} 已無客戶端，可重置`);
                 // delete games[gameId]; // 刪除遊戲
                 // analysisGameId = null; // 允許創建新遊戲
                 // 或者重置遊戲狀態
                 // games[gameId].board = getInitialBoard();
                 // games[gameId].turn = 'red';
                 // ... 其他重置邏輯 ...
            }
             // 不需要廣播斷開連接給其他人，因為是分析板
        }
    });

    ws.on('error', (error) => {
        console.error('WebSocket 發生錯誤:', error);
    });
});

console.log("伺服器設置完成。");