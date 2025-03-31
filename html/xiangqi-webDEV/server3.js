const WebSocket = require('ws');

const wss = new WebSocket.Server({ port: 8080 });
console.log('WebSocket 伺服器正在監聽端口 8080...');

let players = {}; // { 'red': wsClient1, 'black': wsClient2 }
let gameIdCounter = 0; // 簡單的遊戲 ID
const games = {}; // 存儲活躍遊戲: { gameId: gameState }

// --- 初始棋盤數據結構 ---
// 使用對象表示棋子，包含名稱和顏色
function getInitialBoard() {
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
    // 注意：紅方棋子用了不同的字，如果你希望用一樣的字，請修改這裡和前端的繪製邏輯
}

// --- 遊戲狀態 ---
function createNewGame(player1Ws, player2Ws) {
    const gameId = ++gameIdCounter;
    const gameState = {
        id: gameId,
        board: getInitialBoard(),
        turn: 'red', // 紅方先行
        players: {
            red: player1Ws,
            black: player2Ws
        },
        // 甲級聯賽時間（示例：基本時間 20 分鐘，每步加 5 秒）
        timers: {
            red: 20 * 60, // 單位：秒
            black: 20 * 60,
            increment: 5, // 每步加秒
            lastMoveTimestamp: null,
            timerInterval: null // 計時器 interval ID
        },
        gameOver: false,
        winner: null,
        reason: '',
        history: [] // 可以用來判斷長打等規則
    };
    games[gameId] = gameState;

    // 將玩家與遊戲 ID 關聯起來
    player1Ws.gameId = gameId;
    player1Ws.playerColor = 'red';
    player2Ws.gameId = gameId;
    player2Ws.playerColor = 'black';

    return gameState;
}

// --- 核心規則引擎 (極度簡化 - 需要完整實現!) ---
function isValidMove(gameState, from, to, playerColor) {
    // **極其重要的部分：這裡需要實現所有中國象棋的移動規則**
    // 1. 檢查是否輪到該玩家
    if (gameState.turn !== playerColor) {
        return { valid: false, reason: "不是你的回合" };
    }
    // 2. 檢查 'from' 位置是否有該玩家的棋子
    const piece = gameState.board[from.y]?.[from.x]; // 安全訪問
    if (!piece || piece.color !== playerColor) {
        return { valid: false, reason: "起始位置沒有你的棋子" };
    }
    // 3. 檢查 'to' 位置是否在棋盤內
    if (to.x < 0 || to.x >= 9 || to.y < 0 || to.y >= 10) {
         return { valid: false, reason: "目標位置超出棋盤" };
    }
    // 4. 檢查 'to' 位置是否是自己的棋子
    const targetPiece = gameState.board[to.y]?.[to.x];
    if (targetPiece && targetPiece.color === playerColor) {
        return { valid: false, reason: "不能吃自己的棋子" };
    }

    // 5. **實現具體的棋子移動規則 (車、馬、象、士、將、炮、兵)**
    //    - 車: 直線移動，中間不能有子
    //    - 馬: 日字移動，不能被蹩馬腿
    //    - 象: 田字移動，不能過河，不能被塞象眼
    //    - 士: 九宮內斜線移動
    //    - 將/帥: 九宮內直線移動，不能出宮，將帥不能照面
    //    - 炮: 直線移動，吃子時需隔一個子 (炮架)
    //    - 兵/卒: 向前移動，過河後可橫向移動
    //    *** 這是最核心和複雜的邏輯 ***
    //    下面僅做最最簡單的示例判斷（僅允許移動到空格）
    if (targetPiece) {
        // 簡單示例：允許吃子
        console.log(`${playerColor} ${piece.name} eats ${targetPiece.color} ${targetPiece.name}`);
    } else {
         console.log(`${playerColor} ${piece.name} moves`);
    }
     // 假設移動總是合法的（用於演示） - **必須替換為真實規則**
    // return { valid: true, reason: "" };

    // 6. **檢查移動後是否會導致自己被將軍** (非常重要!)
    //    - 模擬移動
    //    - 檢查對方是否能將軍自己
    //    - 如果會，則移動非法

    // **TODO: 在此處插入完整的規則檢查邏輯**
    // 如果沒有實現完整規則，先返回 true 以便測試流程
    console.warn("警告：isValidMove 規則檢查未完整實現！");
    return { valid: true, reason: "" }; // 臨時允許所有移動
}

// 檢查是否將軍 (簡化 - 需要完整實現)
function isCheck(board, targetColor /* 被將軍的顏色 */) {
    // 找到 targetColor 的 將/帥 位置
    // 遍歷所有對方棋子，看是否有合法移動能吃到 將/帥
    // **TODO: 實現檢查將軍邏輯**
    console.warn("警告：isCheck 檢查未實現！");
    return false; // 臨時返回 false
}

// 檢查是否絕殺 (簡化 - 需要完整實現)
function isCheckmate(gameState, targetColor /* 被將死的顏色 */) {
    if (!isCheck(gameState.board, targetColor)) {
        return false; // 沒被將軍，肯定不是絕殺
    }
    // 遍歷 targetColor 的所有棋子
    // 嘗試該棋子的所有合法移動
    // 對於每次模擬移動後的局面，檢查是否仍然被將軍 (isCheck)
    // 如果存在任何一個移動能解除將軍狀態，則不是絕殺
    // 如果所有合法移動都無法解除將軍狀態，則是絕殺
    // **TODO: 實現檢查絕殺邏輯**
    console.warn("警告：isCheckmate 檢查未實現！");
    return false; // 臨時返回 false
}

// 檢查是否困斃 (簡化 - 需要完整實現)
function isStalemate(gameState, targetColor /* 被困斃的顏色 */) {
     if (isCheck(gameState.board, targetColor)) {
        return false; // 被將軍了，可能是絕殺，不是困斃
    }
    // 遍歷 targetColor 的所有棋子
    // 檢查是否存在任何一個合法的移動
    // 如果不存在任何合法移動，則是困斃
    // **TODO: 實現檢查困斃邏輯**
    console.warn("警告：isStalemate 檢查未實現！");
    return false; // 臨時返回 false
}

// --- 時間管理 ---
function stopTimer(gameState) {
    if (gameState.timers.timerInterval) {
        clearInterval(gameState.timers.timerInterval);
        gameState.timers.timerInterval = null;
    }
     // 計算用時
    const now = Date.now();
    if (gameState.timers.lastMoveTimestamp) {
        const elapsedSeconds = (now - gameState.timers.lastMoveTimestamp) / 1000;
        gameState.timers[gameState.turn] -= elapsedSeconds; // 扣除時間
    }
}

function startTimer(gameState) {
    stopTimer(gameState); // 先確保舊計時器停止

    gameState.timers.lastMoveTimestamp = Date.now();

    gameState.timers.timerInterval = setInterval(() => {
        const now = Date.now();
        const elapsedSeconds = (now - gameState.timers.lastMoveTimestamp) / 1000;
        const currentTime = gameState.timers[gameState.turn] - elapsedSeconds;

        // 廣播時間更新給雙方
         broadcast(gameState.id, {
             type: 'timer_update',
             timers: {
                 red: gameState.turn === 'red' ? Math.max(0, currentTime) : Math.max(0, gameState.timers.red),
                 black: gameState.turn === 'black' ? Math.max(0, currentTime) : Math.max(0, gameState.timers.black)
             }
         });


        if (currentTime <= 0) {
            console.log(`${gameState.turn} 超時!`);
            stopTimer(gameState);
            gameState.gameOver = true;
            gameState.winner = gameState.turn === 'red' ? 'black' : 'red'; // 對方贏
            gameState.reason = `${gameState.turn === 'red' ? '紅方' : '黑方'} 超時`;
            broadcastGameOver(gameState);
        }
    }, 1000); // 每秒檢查一次
}

// --- 消息廣播 ---
function broadcast(gameId, message) {
    const game = games[gameId];
    if (!game) return;
    const messageString = JSON.stringify(message);
    if (game.players.red && game.players.red.readyState === WebSocket.OPEN) {
        game.players.red.send(messageString);
    }
    if (game.players.black && game.players.black.readyState === WebSocket.OPEN) {
        game.players.black.send(messageString);
    }
}

function broadcastGameOver(gameState) {
     broadcast(gameState.id, {
        type: 'game_over',
        winner: gameState.winner,
        reason: gameState.reason
    });
     // 清理計時器
     stopTimer(gameState);
     // 可以考慮從 games 中移除已結束的遊戲或標記為結束
     console.log(`遊戲 ${gameState.id} 結束: ${gameState.reason}`);
}


// --- WebSocket 連接處理 ---
let waitingPlayer = null; // 等待對手的玩家

wss.on('connection', (ws) => {
    console.log('一個客戶端已連接');

    if (!waitingPlayer) {
        // 第一個玩家連接
        waitingPlayer = ws;
        ws.send(JSON.stringify({ type: 'message', content: '等待對手加入...' }));
        console.log('玩家1正在等待');
    } else {
        // 第二個玩家連接，開始遊戲
        console.log('玩家2已加入，遊戲開始');
        const player1 = waitingPlayer;
        const player2 = ws;
        waitingPlayer = null; // 清空等待

        const gameState = createNewGame(player1, player2);

        // 向雙方發送初始信息（顏色、棋盤、輪到誰）
        player1.send(JSON.stringify({
            type: 'assign_info',
            color: 'red',
            board: gameState.board,
            turn: gameState.turn
        }));
        player2.send(JSON.stringify({
            type: 'assign_info',
            color: 'black',
            board: gameState.board,
            turn: gameState.turn
        }));

         // 延遲一點點發送開始遊戲和計時器信息，確保客戶端先處理完 assign_info
         setTimeout(() => {
             broadcast(gameState.id, {
                type: 'start_game',
                timers: { // 發送初始時間
                    red: gameState.timers.red,
                    black: gameState.timers.black
                 }
             });
             startTimer(gameState); // 開始紅方計時
         }, 100); // 100毫秒延遲
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
                const validationResult = isValidMove(gameState, from, to, playerColor);

                if (validationResult.valid) {
                    // 執行移動
                    const movedPiece = gameState.board[from.y][from.x];
                    const targetPiece = gameState.board[to.y][to.x]; // 可能為 null

                    gameState.board[to.y][to.x] = movedPiece;
                    gameState.board[from.y][from.x] = null;
                    gameState.history.push({ from, to, piece: movedPiece, captured: targetPiece }); // 記錄歷史

                    // 停止當前玩家計時器，加上步增時間
                    stopTimer(gameState);
                    gameState.timers[playerColor] += gameState.timers.increment;

                    // 切換回合
                    gameState.turn = playerColor === 'red' ? 'black' : 'red';

                    // 檢查遊戲是否結束（將軍、絕殺、困斃、和棋規則）
                    let checkInfo = "";
                    if (isCheck(gameState.board, gameState.turn)) {
                        checkInfo = `${gameState.turn === 'red' ? '紅方' : '黑方'} 被將軍!`;
                        if (isCheckmate(gameState, gameState.turn)) {
                            gameState.gameOver = true;
                            gameState.winner = playerColor; // 移動方獲勝
                            gameState.reason = "絕殺";
                            // 不切換計時器了，直接廣播結束
                        } else if (isStalemate(gameState, gameState.turn)) { // 理論上被將軍時不會困斃，但檢查邏輯要完善
                             gameState.gameOver = true;
                             gameState.winner = null; // 和棋
                             gameState.reason = "困斃和棋";
                        }
                    } else if (isStalemate(gameState, gameState.turn)) {
                         gameState.gameOver = true;
                         gameState.winner = null; // 和棋
                         gameState.reason = "困斃和棋";
                    }
                    // **TODO: 添加其他和棋規則判斷 (如自然限著、長打等)**

                    if (gameState.gameOver) {
                         // 更新最後一步棋盤狀態再廣播結束
                         broadcast(gameId, {
                            type: 'update_state',
                            board: gameState.board,
                            turn: gameState.turn, // 輪到誰不重要了
                            timers: {
                                red: gameState.timers.red,
                                black: gameState.timers.black
                            },
                            lastMoveInfo: checkInfo // 可以附加最後的提示
                         });
                         // 稍作延遲再發送結束消息
                         setTimeout(() => broadcastGameOver(gameState), 100);
                    } else {
                        // 遊戲繼續，廣播新狀態並啟動對方計時器
                        broadcast(gameId, {
                            type: 'update_state',
                            board: gameState.board,
                            turn: gameState.turn,
                             timers: {
                                red: gameState.timers.red,
                                black: gameState.timers.black
                            },
                            lastMoveInfo: checkInfo // 附加將軍提示
                        });
                        startTimer(gameState); // 啟動下一位玩家的計時器
                    }

                } else {
                    // 非法移動
                    ws.send(JSON.stringify({ type: 'illegal_move', reason: validationResult.reason }));
                }
            }
            // 可以添加處理其他消息類型，如 'resign' (認輸), 'draw_offer' (提和) 等

        } catch (error) {
            console.error('處理消息時發生錯誤:', error);
            try {
                 ws.send(JSON.stringify({ type: 'error', content: '伺服器處理消息出錯' }));
            } catch (sendError) {
                 console.error('向客戶端發送錯誤消息失敗:', sendError);
            }
        }
    });

    // --- 處理連接關閉 ---
    ws.on('close', () => {
        console.log('一個客戶端已斷開連接');
        if (ws === waitingPlayer) {
            waitingPlayer = null; // 如果等待的玩家離開了
            console.log('等待中的玩家已離開');
        } else if (ws.gameId && games[ws.gameId]) {
            const gameId = ws.gameId;
            const gameState = games[gameId];
            const disconnectedPlayerColor = ws.playerColor;
            const opponentColor = disconnectedPlayerColor === 'red' ? 'black' : 'red';
            const opponentWs = gameState.players[opponentColor];

            console.log(`遊戲 ${gameId} 中的玩家 ${disconnectedPlayerColor} 已斷開`);

             if (!gameState.gameOver) { // 只有在遊戲進行中斷開才判負
                 gameState.gameOver = true;
                 gameState.winner = opponentColor;
                 gameState.reason = `${disconnectedPlayerColor === 'red' ? '紅方' : '黑方'} 斷開連接`;
                 stopTimer(gameState); // 停止計時器

                 if (opponentWs && opponentWs.readyState === WebSocket.OPEN) {
                     opponentWs.send(JSON.stringify({
                         type: 'game_over',
                         winner: opponentColor,
                         reason: gameState.reason
                     }));
                     opponentWs.send(JSON.stringify({ type: 'opponent_disconnected' })); // 額外通知
                 }
             }

            // 清理遊戲資源 (可以延遲清理或標記為結束)
             delete gameState.players[disconnectedPlayerColor]; // 移除斷開的玩家
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
        // 可以在這裡嘗試關閉連接或處理錯誤
    });
});

console.log("伺服器設置完成。");