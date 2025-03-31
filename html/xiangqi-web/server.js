// server.js (分析板模式 + 棋譜處理)

const WebSocket = require('ws');
const XiangqiRules = require('./rules.js');
const XiangqiUtils = require('./utils.js'); // *** 引入 utils ***

const wss = new WebSocket.Server({ port: 8080 });
console.log('WebSocket 伺服器 (分析板模式) 正在監聽端口 8080...');

let gameIdCounter = 0;
const games = {};
let analysisGameId = null; // 全局分析板 ID

// --- 初始棋盤 ---
function getInitialBoard() { /* ... (同上一個版本) ... */
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
function createNewGame(player1Ws) {
    const gameId = ++gameIdCounter;
    const gameState = {
        id: gameId,
        board: getInitialBoard(),
        turn: 'red',
        clients: [player1Ws],
        gameOver: false,
        winner: null,
        reason: '',
        history: []
    };
    games[gameId] = gameState;
    player1Ws.gameId = gameId;
    player1Ws.playerColor = 'red'; // Assign a default color for display
    console.log(`創建新分析板遊戲 ${gameId}`);
    return gameState;
}

// --- 消息廣播 ---
function broadcast(gameId, message) {
    const game = games[gameId];
    if (!game || !game.clients) return;
    const messageString = JSON.stringify(message);
    game.clients = game.clients.filter(client => client.readyState === WebSocket.OPEN);
    game.clients.forEach(client => {
        try {
            client.send(messageString);
        } catch (e) {
            console.error(`發送消息給客戶端失敗 (Game ${gameId}):`, e);
        }
    });
}

function broadcastGameOver(gameState) {
    broadcast(gameState.id, {
        type: 'game_over',
        winner: gameState.winner,
        reason: gameState.reason
    });
    console.log(`遊戲 ${gameState.id} 結束: ${gameState.reason}`);
}

// --- WebSocket 連接處理 ---
wss.on('connection', (ws) => {
    console.log('一個客戶端已連接 (分析板)');
    let gameState;
    if (analysisGameId === null || !games[analysisGameId] || games[analysisGameId].clients.length === 0) {
        // 如果沒有分析板或分析板沒人了，創建新的
        gameState = createNewGame(ws);
        analysisGameId = gameState.id;
    } else {
        // 加入現有分析板
        gameState = games[analysisGameId];
        ws.gameId = analysisGameId;
        gameState.clients.push(ws);
        ws.playerColor = gameState.clients.length % 2 === 0 ? 'black' : 'red'; // 交替分配顯示顏色
        console.log(`客戶端加入遊戲 ${analysisGameId}, 當前客戶端數: ${gameState.clients.length}`);
    }

    // 發送當前狀態給新連接者
    ws.send(JSON.stringify({
        type: 'assign_info',
        color: ws.playerColor,
        board: gameState.board,
        turn: gameState.turn
    }));
    // 只要遊戲存在就認為是開始狀態
    setTimeout(() => ws.send(JSON.stringify({ type: 'start_game' })), 100);


    // --- 處理來自客戶端的消息 ---
    ws.on('message', (message) => {
        let data;
        try {
            data = JSON.parse(message);
        } catch (e) {
            console.error("無法解析收到的消息:", message, e);
            return; // 忽略無法解析的消息
        }

        const gameId = ws.gameId;
        if (!gameId || !games[gameId]) { return; } // 無效遊戲
        const currentGameState = games[gameId];

        if (currentGameState.gameOver && data.type !== 'load_fen' && data.type !== 'get_game_record') {
            // 遊戲結束後只允許加載和獲取棋譜
            return;
        }

        console.log(`收到來自 Game ${gameId} 的消息:`, data);

        try { // Add try-catch around message processing
            if (data.type === 'load_fen' && typeof data.fen === 'string') {
                console.log(`Game ${gameId}: 收到加載 FEN 請求: ${data.fen}`);
                const newState = XiangqiUtils.fenToBoard(data.fen);
                if (newState) {
                    currentGameState.board = newState.board;
                    currentGameState.turn = newState.turn;
                    currentGameState.history = [];
                    currentGameState.gameOver = false;
                    currentGameState.winner = null;
                    currentGameState.reason = '';
                    console.log(`Game ${gameId}: FEN 加載成功，輪到 ${currentGameState.turn}`);
                    broadcast(gameId, {
                        type: 'update_state',
                        board: currentGameState.board,
                        turn: currentGameState.turn,
                        lastMoveInfo: "棋盤已從 FEN 加載"
                    });
                } else {
                    ws.send(JSON.stringify({ type: 'error', content: '無效的 FEN 字符串' }));
                }
            } else if (data.type === 'get_game_record') {
                 const fen = XiangqiUtils.boardToFen(currentGameState.board, currentGameState.turn);
                 const moveList = currentGameState.history.map(move =>
                     `${move.from.y}${move.from.x}-${move.to.y}${move.to.x}`
                 ).join(' ');
                 const record = `[FEN "${fen}"]\n\n${moveList}`;
                 ws.send(JSON.stringify({ type: 'game_record', record: record }));
             } else if (data.type === 'move') {
                const { from, to } = data;
                const pieceToMove = currentGameState.board[from.y]?.[from.x];
                if (!pieceToMove) { ws.send(JSON.stringify({ type: 'illegal_move', reason: "起始位置無棋子" })); return; }

                // *** 分析板核心：調用不檢查輪次的驗證 ***
                const validationResult = XiangqiRules.isValidMoveInternal(currentGameState.board, from, to, pieceToMove.color);

                if (validationResult.valid) {
                    const movedPiece = currentGameState.board[from.y][from.x];
                    const targetPiece = currentGameState.board[to.y][to.x];
                    // 更新歷史記錄
                    currentGameState.history.push({ from: {x: from.x, y: from.y}, to: {x: to.x, y: to.y}, piece: movedPiece.name, color: movedPiece.color, captured: targetPiece ? targetPiece.name : null });
                    // 更新棋盤
                    currentGameState.board[to.y][to.x] = movedPiece;
                    currentGameState.board[from.y][from.x] = null;
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

                    if (currentGameState.gameOver) {
                         broadcast(gameId, { type: 'update_state', board: currentGameState.board, turn: currentGameState.turn, lastMoveInfo: checkInfo });
                         setTimeout(() => broadcastGameOver(currentGameState), 100);
                    } else {
                        broadcast(gameId, {
                            type: 'update_state',
                            board: currentGameState.board,
                            turn: currentGameState.turn,
                            lastMoveInfo: checkInfo
                        });
                    }
                } else {
                    ws.send(JSON.stringify({ type: 'illegal_move', reason: validationResult.reason }));
                }
            }
            // ... 其他消息 ...
        } catch (error) {
            console.error('處理消息錯誤:', error);
            // 安全起見，向客戶端發送通用錯誤
            try { ws.send(JSON.stringify({ type: 'error', content: '伺服器處理消息時發生內部錯誤' })); } catch (e) {}
        }
    });

    // --- 連接關閉 ---
    ws.on('close', () => {
        console.log('一個客戶端已斷開連接 (分析板)');
        const gameId = ws.gameId;
        if (gameId && games[gameId]) {
            const currentGameState = games[gameId];
            currentGameState.clients = currentGameState.clients.filter(client => client !== ws);
            console.log(`客戶端離開遊戲 ${gameId}, 剩餘客戶端數: ${currentGameState.clients.length}`);
            if (currentGameState.clients.length === 0) {
                 console.log(`分析板遊戲 ${gameId} 已無客戶端，可重置`);
                 // 可選重置邏輯
                 // games[gameId].board = getInitialBoard(); games[gameId].turn = 'red'; games[gameId].history = []; games[gameId].gameOver = false;
            }
        }
    });
    ws.on('error', (error) => console.error('WebSocket 發生錯誤:', error));
});

console.log("伺服器設置完成。");