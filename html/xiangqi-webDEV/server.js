// server.js (修改後)

const WebSocket = require('ws');
// 引入規則模塊
const XiangqiRules = require('./rules.js'); // 確保路徑正確

const wss = new WebSocket.Server({ port: 8080 });
console.log('WebSocket 伺服器正在監聽端口 8080...');

let players = {}; // { 'red': wsClient1, 'black': wsClient2 } - 這個全局 players 變量其實不太適合多房間，僅作示例
let gameIdCounter = 0;
const games = {}; // { gameId: gameState }

// --- 初始棋盤數據結構 ---
function getInitialBoard() {
    // ... (保持不變)
    return [
        [{name:'車', color:'black'}, {name:'馬', color:'black'}, {name:'象', color:'black'}, {name:'士', color:'black'}, {name:'將', color:'black'}, {name:'士', color:'black'}, {name:'象', color:'black'}, {name:'馬', color:'black'}, {name:'車', color:'black'}],
        [null, null, null, null, null, null, null, null, null],
        [null, {name:'炮', color:'black'}, null, null, null, null, null, {name:'炮', color:'black'}, null],
        [{name:'卒', color:'black'}, null, {name:'卒', color:'black'}, null, {name:'卒', color:'black'}, null, {name:'卒', color:'black'}, null, {name:'卒', color:'black'}],
        [null, null, null, null, null, null, null, null, null], // 楚河漢界
        [null, null, null, null, null, null, null, null, null],
        [{name:'兵', color:'red'}, null, {name:'兵', color:'red'}, null, {name:'兵', color:'red'}, null, {name:'兵', color:'red'}, null, {name:'兵', color:'red'}],
        [null, {name:'炮', color:'red'}, null, null, null, null, null, {name:'炮', color:'red'}, null],
        [null, null, null, null, null, null, null, null, null],
        [{name:'俥', color:'red'}, {name:'傌', color:'red'}, {name:'相', color:'red'}, {name:'仕', color:'red'}, {name:'帥', color:'red'}, {name:'仕', color:'red'}, {name:'相', color:'red'}, {name:'傌', color:'red'}, {name:'俥', color:'red'}]
    ];
}

// --- 遊戲狀態 ---
function createNewGame(player1Ws, player2Ws) {
    // ... (保持不變)
    const gameId = ++gameIdCounter;
    const gameState = {
        id: gameId,
        board: getInitialBoard(),
        turn: 'red',
        players: { red: player1Ws, black: player2Ws },
        timers: { red: 1200, black: 1200, increment: 5, lastMoveTimestamp: null, timerInterval: null },
        gameOver: false,
        winner: null,
        reason: '',
        history: []
    };
    games[gameId] = gameState;
    player1Ws.gameId = gameId;
    player1Ws.playerColor = 'red';
    player2Ws.gameId = gameId;
    player2Ws.playerColor = 'black';
    return gameState;
}


// --- 核心規則引擎 (現在從 rules.js 引入) ---
// 移除舊的 isValidMove, isKingInCheck, canPieceMechanicallyReach, createBoardCopy, 及相關輔助函數


// --- 檢查是否絕殺 (簡化 - 需要完整實現!) ---
// **TODO:** 這個函數也應該移到 rules.js 中，並利用 isKingInCheck 和 isValidMove
function isCheckmate(gameState, targetColor /* 被將死的顏色 */) {
    // 實現邏輯...需要模擬所有 targetColor 的合法走法
    // 需要使用 XiangqiRules.isValidMove 和 XiangqiRules.isKingInCheck
    console.warn("警告：isCheckmate 檢查未實現！");
    // 臨時實現：先檢查是否被將軍
    if (!XiangqiRules.isKingInCheck(gameState.board, targetColor)) {
       return false;
    }
    // 真正實現需要遍歷所有可能的解將走法
    // ...
    return false; // 臨時返回 false
}

// --- 檢查是否困斃 (簡化 - 需要完整實現!) ---
// **TODO:** 這個函數也應該移到 rules.js 中
function isStalemate(gameState, targetColor /* 被困斃的顏色 */) {
     // 實現邏輯...需要檢查 targetColor 是否有任何合法走法
     // 需要使用 XiangqiRules.isValidMove
    console.warn("警告：isStalemate 檢查未實現！");
     if (XiangqiRules.isKingInCheck(gameState.board, targetColor)) {
        return false; // 被將軍不是困斃
    }
    // 真正實現需要遍歷所有可能的走法
    // ...
    return false; // 臨時返回 false
}

// --- 時間管理 ---
function stopTimer(gameState) {
    // ... (保持不變)
     if (gameState.timers.timerInterval) {
        clearInterval(gameState.timers.timerInterval);
        gameState.timers.timerInterval = null;
    }
     const now = Date.now();
    if (gameState.timers.lastMoveTimestamp) {
        const elapsedSeconds = (now - gameState.timers.lastMoveTimestamp) / 1000;
        // 確保時間不為負
        gameState.timers[gameState.turn] = Math.max(0, gameState.timers[gameState.turn] - elapsedSeconds);
    }
}

function startTimer(gameState) {
    // ... (保持不變)
     stopTimer(gameState);
     gameState.timers.lastMoveTimestamp = Date.now();
     gameState.timers.timerInterval = setInterval(() => {
         // ... (計時器邏輯, 超時判斷) ...
         const now = Date.now();
         const elapsedSeconds = (now - gameState.timers.lastMoveTimestamp) / 1000;
         const currentTime = gameState.timers[gameState.turn] - elapsedSeconds;

         broadcast(gameState.id, {
             type: 'timer_update',
             timers: {
                 red: Math.max(0, gameState.turn === 'red' ? currentTime : gameState.timers.red),
                 black: Math.max(0, gameState.turn === 'black' ? currentTime : gameState.timers.black)
             }
         });

         if (currentTime <= 0) {
             console.log(`${gameState.turn} 超時!`);
             stopTimer(gameState);
             gameState.gameOver = true;
             gameState.winner = gameState.turn === 'red' ? 'black' : 'red';
             gameState.reason = `${gameState.turn === 'red' ? '紅方' : '黑方'} 超時`;
             broadcastGameOver(gameState);
         }
     }, 1000);
}

// --- 消息廣播 ---
function broadcast(gameId, message) {
    // ... (保持不變)
    const game = games[gameId];
    if (!game) return;
    const messageString = JSON.stringify(message);
    // 確保玩家 WebSocket 仍然存在且處於打開狀態
    if (game.players.red && game.players.red.readyState === WebSocket.OPEN) {
        game.players.red.send(messageString);
    }
    if (game.players.black && game.players.black.readyState === WebSocket.OPEN) {
        game.players.black.send(messageString);
    }
}

function broadcastGameOver(gameState) {
    // ... (保持不變)
    stopTimer(gameState); // 確保計時器停止
    broadcast(gameState.id, {
        type: 'game_over',
        winner: gameState.winner,
        reason: gameState.reason
    });
    console.log(`遊戲 ${gameState.id} 結束: ${gameState.reason}`);
    // 可以考慮在這裡從 games 中移除遊戲，或者標記為已結束稍後清理
    // delete games[gameState.id];
}


// --- WebSocket 連接處理 ---
let waitingPlayer = null;

wss.on('connection', (ws) => {
    console.log('一個客戶端已連接');

    // --- 玩家匹配邏輯 (保持不變) ---
    if (!waitingPlayer) {
        waitingPlayer = ws;
        ws.send(JSON.stringify({ type: 'message', content: '等待對手加入...' }));
        console.log('玩家1正在等待');
    } else {
        console.log('玩家2已加入，遊戲開始');
        const player1 = waitingPlayer;
        const player2 = ws;
        waitingPlayer = null;
        const gameState = createNewGame(player1, player2);

        player1.send(JSON.stringify({ type: 'assign_info', color: 'red', board: gameState.board, turn: gameState.turn }));
        player2.send(JSON.stringify({ type: 'assign_info', color: 'black', board: gameState.board, turn: gameState.turn }));

         setTimeout(() => {
             broadcast(gameState.id, {
                type: 'start_game',
                timers: { red: gameState.timers.red, black: gameState.timers.black }
             });
             startTimer(gameState);
         }, 100);
    }

    // --- 處理來自客戶端的消息 ---
    ws.on('message', (message) => {
        try {
            const data = JSON.parse(message);
            const gameId = ws.gameId;
            const playerColor = ws.playerColor;

            if (!gameId || !games[gameId] || !playerColor) {
                 console.warn("收到來自未知或未分配遊戲的客戶端消息");
                 ws.send(JSON.stringify({ type: 'error', content: '你不在一個有效的遊戲中' }));
                 return;
             }

            const gameState = games[gameId];

            if (gameState.gameOver) {
                console.log(`遊戲 ${gameId} 已結束，忽略消息: ${message}`);
                return;
            }

            console.log(`收到來自 ${playerColor} (Game ${gameId}) 的消息:`, data);

            if (data.type === 'move') {
                const { from, to } = data;

                // **** 使用引入的規則函數進行驗證 ****
                // 注意：isValidMove 現在已經包含了自將檢查
                const validationResult = XiangqiRules.isValidMove(gameState, from, to, playerColor);

                if (validationResult.valid) {
                    // **** 移動有效，執行移動 ****
                    stopTimer(gameState); // 停止計時器
                    // 加上步增時間 (如果有的話)
                    if (gameState.timers.increment > 0) {
                         gameState.timers[playerColor] += gameState.timers.increment;
                    }

                    const movedPiece = gameState.board[from.y][from.x];
                    const targetPiece = gameState.board[to.y][to.x];
                    gameState.board[to.y][to.x] = movedPiece;
                    gameState.board[from.y][from.x] = null;
                    gameState.history.push({ from, to, piece: movedPiece.name, color: movedPiece.color, captured: targetPiece ? targetPiece.name : null }); // 記錄更詳細的歷史

                    // 切換回合
                    const previousTurn = gameState.turn;
                    gameState.turn = playerColor === 'red' ? 'black' : 'red';

                    // 檢查遊戲是否結束（將軍、絕殺、困斃、和棋規則）
                    let checkInfo = "";
                    const opponentColor = gameState.turn;
                    if (XiangqiRules.isKingInCheck(gameState.board, opponentColor)) {
                        checkInfo = `${opponentColor === 'red' ? '紅方' : '黑方'} 被將軍!`;
                        // **TODO: 在這裡調用 isCheckmate**
                        if (isCheckmate(gameState, opponentColor)) {
                            gameState.gameOver = true;
                            gameState.winner = playerColor; // 執行移動的一方獲勝
                            gameState.reason = "絕殺";
                        }
                        // 困斃檢查應該在沒被將軍時進行
                    } else {
                        // **TODO: 在這裡調用 isStalemate**
                        if (isStalemate(gameState, opponentColor)) {
                            gameState.gameOver = true;
                            gameState.winner = null; // 和棋
                            gameState.reason = "困斃和棋";
                        }
                    }
                    // **TODO: 添加其他和棋規則判斷 (如自然限著、長打等)**

                    if (gameState.gameOver) {
                         // 廣播最後狀態並結束
                         broadcast(gameState.id, {
                            type: 'update_state',
                            board: gameState.board,
                            turn: gameState.turn,
                            timers: {
                                red: Math.max(0, gameState.timers.red), // 發送更新後的時間
                                black: Math.max(0, gameState.timers.black)
                            },
                            lastMoveInfo: checkInfo
                         });
                         setTimeout(() => broadcastGameOver(gameState), 100);
                    } else {
                        // 遊戲繼續，廣播新狀態並啟動對方計時器
                        broadcast(gameId, {
                            type: 'update_state',
                            board: gameState.board,
                            turn: gameState.turn,
                             timers: {
                                red: Math.max(0, gameState.timers.red),
                                black: Math.max(0, gameState.timers.black)
                            },
                            lastMoveInfo: checkInfo
                        });
                        startTimer(gameState); // 啟動下一位玩家的計時器
                    }

                } else {
                    // 非法移動
                    ws.send(JSON.stringify({ type: 'illegal_move', reason: validationResult.reason }));
                }
            }
            // ... (處理其他消息類型)

        } catch (error) {
            console.error('處理消息時發生錯誤:', error);
            // ... (錯誤處理)
        }
    });

    // --- 處理連接關閉 ---
    ws.on('close', () => {
        // ... (保持不變，處理玩家斷開連接的邏輯)
        console.log('一個客戶端已斷開連接');
        if (ws === waitingPlayer) {
            waitingPlayer = null;
            console.log('等待中的玩家已離開');
        } else if (ws.gameId && games[ws.gameId]) {
            const gameId = ws.gameId;
            const gameState = games[gameId];
            const disconnectedPlayerColor = ws.playerColor;
            const opponentColor = disconnectedPlayerColor === 'red' ? 'black' : 'red';
            const opponentWs = gameState.players[opponentColor];

            console.log(`遊戲 ${gameId} 中的玩家 ${disconnectedPlayerColor} 已斷開`);

             if (!gameState.gameOver) {
                 gameState.gameOver = true;
                 gameState.winner = opponentColor;
                 gameState.reason = `${disconnectedPlayerColor === 'red' ? '紅方' : '黑方'} 斷開連接`;
                 stopTimer(gameState);

                 if (opponentWs && opponentWs.readyState === WebSocket.OPEN) {
                    opponentWs.send(JSON.stringify({
                         type: 'game_over',
                         winner: opponentColor,
                         reason: gameState.reason
                     }));
                     opponentWs.send(JSON.stringify({ type: 'opponent_disconnected' }));
                 }
             }

             delete gameState.players[disconnectedPlayerColor];
             // 可選：如果另一方也離開了，清理遊戲
             if (!gameState.players.red && !gameState.players.black) {
                  console.log(`遊戲 ${gameId} 所有玩家已離開，清理遊戲數據`);
                 if (gameState.timers.timerInterval) clearInterval(gameState.timers.timerInterval);
                 delete games[gameId];
             }

        } else {
             console.log("一個未分配遊戲的客戶端斷開連接");
        }
    });

    ws.on('error', (error) => {
        console.error('WebSocket 發生錯誤:', error);
    });
});

console.log("伺服器設置完成。");