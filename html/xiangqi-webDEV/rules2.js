// rules.js - 中國象棋規則引擎模塊

// --- 輔助函數 ---

function getPieceAt(board, x, y) {
    if (y < 0 || y >= 10 || x < 0 || x >= 9) {
        return null;
    }
    return board[y]?.[x]; // Optional chaining for safety
}

function isWithinBoard(x, y) {
    return x >= 0 && x < 9 && y >= 0 && y < 10;
}

function isWithinPalace(x, y, color) {
    if (x < 3 || x > 5) return false;
    if (color === 'red') {
        return y >= 7 && y <= 9;
    } else { // black
        return y >= 0 && y <= 2;
    }
}

function countPiecesBetween(board, fromX, fromY, toX, toY) {
    let count = 0;
    if (fromY === toY) { // Horizontal
        const start = Math.min(fromX, toX) + 1;
        const end = Math.max(fromX, toX);
        for (let x = start; x < end; x++) {
            if (getPieceAt(board, x, fromY)) {
                count++;
            }
        }
    } else if (fromX === toX) { // Vertical
        const start = Math.min(fromY, toY) + 1;
        const end = Math.max(fromY, toY);
        for (let y = start; y < end; y++) {
            if (getPieceAt(board, fromX, y)) {
                count++;
            }
        }
    }
    return count;
}

// 檢查棋子是否能 *純粹地* (不考慮輪到誰, 不考慮是否會導致自己被將) 移動到目標點
// 主要用於 isKingInCheck 函數
function canPieceMechanicallyReach(board, piece, fromX, fromY, toX, toY) {
    const targetPiece = getPieceAt(board, toX, toY);

    if (!isWithinBoard(toX, toY)) return false;

    const dx = toX - fromX;
    const dy = toY - fromY;

    switch (piece.name) {
        case '車': case '俥':
            if (dx !== 0 && dy !== 0) return false;
            return countPiecesBetween(board, fromX, fromY, toX, toY) === 0;
        case '馬': case '傌':
            const isValidHorseMove = (Math.abs(dx) === 1 && Math.abs(dy) === 2) || (Math.abs(dx) === 2 && Math.abs(dy) === 1);
            if (!isValidHorseMove) return false;
            let blockX, blockY;
            if (Math.abs(dx) === 2) { blockX = fromX + dx / 2; blockY = fromY; }
            else { blockX = fromX; blockY = fromY + dy / 2; }
            return !getPieceAt(board, blockX, blockY);
        case '象': case '相':
             if (!(Math.abs(dx) === 2 && Math.abs(dy) === 2)) return false;
             if ((piece.color === 'black' && toY > 4) || (piece.color === 'red' && toY < 5)) return false;
             const blockEyeX = fromX + dx / 2;
             const blockEyeY = fromY + dy / 2;
             return !getPieceAt(board, blockEyeX, blockEyeY);
        case '士': case '仕':
             if (!(Math.abs(dx) === 1 && Math.abs(dy) === 1)) return false;
             return isWithinPalace(toX, toY, piece.color);
        case '將': case '帥':
             //將帥的 '移動' 能力在這裡只用於檢查 '照面' 情況，由 isKingInCheck 主函數處理
             //一個將帥不能直接 '吃掉' 另一個將帥來形成將軍，所以這裡返回 false
             // return (Math.abs(dx) + Math.abs(dy) === 1) && isWithinPalace(toX, toY, piece.color);
             return false; // 將帥不直接通過此函數判斷攻擊對方將帥
        case '炮':
             if (dx !== 0 && dy !== 0) return false;
             const piecesBetween = countPiecesBetween(board, fromX, fromY, toX, toY);
             if (targetPiece) { // 吃子
                return piecesBetween === 1;
             } else { // 移動
                return piecesBetween === 0;
             }
        case '卒': case '兵':
             const forwardY = (piece.color === 'black') ? 1 : -1;
             const riverY = (piece.color === 'black') ? 4 : 5; // 過河的 Y 坐標 (0-based index)
              // 注意：Y 坐標定義，假設 0 是黑方底線，9 是紅方底線
              // 黑卒過河 Y >= 5, 紅兵過河 Y <= 4
              const isAcrossRiver = (piece.color === 'black' && fromY >= riverY) || (piece.color === 'red' && fromY <= riverY);

              if (!isAcrossRiver) { // 未過河
                 return (dx === 0 && dy === forwardY);
             } else { // 已過河
                 const isForward = (dx === 0 && dy === forwardY);
                 const isSideways = (dy === 0 && Math.abs(dx) === 1);
                 return (isForward || isSideways);
             }
        default:
            return false;
    }
}


// --- 主要導出的函數 ---

/**
 * 檢查指定顏色的王是否處於被將軍狀態
 * @param {Array<Array<Object|null>>} board - 當前棋盤狀態
 * @param {String} kingColor - 要檢查的王的顏色 ('red' or 'black')
 * @returns {boolean} - 如果被將軍則返回 true，否則返回 false
 */
function isKingInCheck(board, kingColor) {
    let kingX = -1, kingY = -1;
    let opponentKingX = -1, opponentKingY = -1;
    const kingName = kingColor === 'red' ? '帥' : '將';
    const opponentKingName = kingColor === 'red' ? '將' : '帥';
    const opponentColor = kingColor === 'red' ? 'black' : 'red';

    // 1. 找到雙方將/帥的位置
    for (let y = 0; y < 10; y++) {
        for (let x = 0; x < 9; x++) {
            const p = board[y][x];
            if (p) {
                if (p.name === kingName && p.color === kingColor) {
                    kingX = x;
                    kingY = y;
                } else if (p.name === opponentKingName && p.color === opponentColor) {
                    opponentKingX = x;
                    opponentKingY = y;
                }
            }
        }
    }

    if (kingX === -1) {
         console.error(`無法在棋盤上找到 ${kingColor} 方的將/帥! (isKingInCheck)`);
         return false; // 或者拋出錯誤
    }

    // 2. 檢查是否有對方棋子能攻擊到己方將/帥
    for (let y = 0; y < 10; y++) {
        for (let x = 0; x < 9; x++) {
            const attackerPiece = board[y][x];
            if (attackerPiece && attackerPiece.color === opponentColor) {
                if (canPieceMechanicallyReach(board, attackerPiece, x, y, kingX, kingY)) {
                    // console.log(`Check detected: ${attackerPiece.color} ${attackerPiece.name} at (${x},${y}) can attack ${kingColor} King at (${kingX},${kingY})`);
                    return true; // 被將軍
                }
            }
        }
    }

     // 3. 檢查將帥是否照面
     if (kingX === opponentKingX && opponentKingX !== -1) { // 必須在同一列且對方將帥也已找到
        if (countPiecesBetween(board, kingX, kingY, opponentKingX, opponentKingY) === 0) {
            // console.log(`Check detected: Facing Generals at column ${kingX}`);
           return true; // 將帥照面，被將軍
        }
     }

    return false; // 未被將軍
}


/**
 * 檢查一步棋是否符合規則（包括棋子移動方式和是否會導致己方被將）
 * @param {Object} gameState - 當前的遊戲狀態對象，至少包含 board 和 turn
 * @param {Object} from - 起始坐標 { x: col, y: row }
 * @param {Object} to - 目標坐標 { x: col, y: row }
 * @param {String} playerColor - 執行移動的玩家顏色 ('red' or 'black')
 * @returns {Object} - { valid: boolean, reason: string }
 */
function isValidMove(gameState, from, to, playerColor) {
    const board = gameState.board;

    // --- 基礎檢查 ---
    if (!isWithinBoard(from.x, from.y) || !isWithinBoard(to.x, to.y)) {
        return { valid: false, reason: "位置超出棋盤範圍" };
    }
    const piece = getPieceAt(board, from.x, from.y);
    if (!piece) {
        return { valid: false, reason: "起始位置沒有棋子" };
    }
    if (piece.color !== playerColor) {
        return { valid: false, reason: "不能移動對方的棋子" };
    }
    // 輪到誰走的檢查應該在調用此函數之前完成，但也可以在這裡加一道保險
    if (gameState.turn !== playerColor) {
         return { valid: false, reason: "還沒輪到你走" };
    }
    if (from.x === to.x && from.y === to.y) {
        return { valid: false, reason: "起始點和目標點相同" };
    }
    const targetPiece = getPieceAt(board, to.x, to.y);
    if (targetPiece && targetPiece.color === playerColor) {
        return { valid: false, reason: "不能吃自己的棋子" };
    }

    // --- 棋子專屬移動規則檢查 (純機械移動) ---
    const dx = to.x - from.x;
    const dy = to.y - from.y;
    let mechanicallyValid = false; // 標記是否通過了純粹的移動規則

    switch (piece.name) {
        case '車': case '俥':
            if ((dx === 0 || dy === 0) && countPiecesBetween(board, from.x, from.y, to.x, to.y) === 0) {
                 mechanicallyValid = true;
            } else if (dx !== 0 && dy !== 0) {
                 return { valid: false, reason: "車只能走直線" };
            } else {
                 return { valid: false, reason: "車移動路徑上有障礙" };
            }
            break;

        case '馬': case '傌':
            const isValidHorseMove = (Math.abs(dx) === 1 && Math.abs(dy) === 2) || (Math.abs(dx) === 2 && Math.abs(dy) === 1);
            if (!isValidHorseMove) {
                return { valid: false, reason: "馬只能走日字" };
            }
            let blockX, blockY;
            if (Math.abs(dx) === 2) { blockX = from.x + dx / 2; blockY = from.y; }
            else { blockX = from.x; blockY = from.y + dy / 2; }
            if (getPieceAt(board, blockX, blockY)) {
                return { valid: false, reason: "馬被蹩馬腿" };
            }
            mechanicallyValid = true;
            break;

        case '象': case '相':
            if (!(Math.abs(dx) === 2 && Math.abs(dy) === 2)) {
                return { valid: false, reason: "象/相只能走田字" };
            }
            const riverYElephant = (piece.color === 'black') ? 4 : 5; // 河界線
            if ((piece.color === 'black' && to.y > riverYElephant) || (piece.color === 'red' && to.y < riverYElephant)) {
                return { valid: false, reason: "象/相不能過河" };
            }
            const blockEyeX = from.x + dx / 2;
            const blockEyeY = from.y + dy / 2;
            if (getPieceAt(board, blockEyeX, blockEyeY)) {
                return { valid: false, reason: "被塞象眼" };
            }
            mechanicallyValid = true;
            break;

        case '士': case '仕':
            if (!(Math.abs(dx) === 1 && Math.abs(dy) === 1)) {
                return { valid: false, reason: "士/仕只能斜走一格" };
            }
            if (!isWithinPalace(to.x, to.y, piece.color)) {
                return { valid: false, reason: "士/仕不能出九宮" };
            }
            mechanicallyValid = true;
            break;

        case '將': case '帥':
            if (!(Math.abs(dx) + Math.abs(dy) === 1)) {
                return { valid: false, reason: "將/帥只能直走或橫走一格" };
            }
            if (!isWithinPalace(to.x, to.y, piece.color)) {
                return { valid: false, reason: "將/帥不能出九宮" };
            }
            mechanicallyValid = true;
            // 將帥照面規則在 isKingInCheck 中處理，並在最終的自將檢查中體現
            break;

        case '炮':
            if (dx !== 0 && dy !== 0) {
                 return { valid: false, reason: "炮只能走直線" };
            }
            const piecesBetween = countPiecesBetween(board, from.x, from.y, to.x, to.y);
            if (targetPiece) { // 吃子
                if (piecesBetween !== 1) {
                    return { valid: false, reason: "炮吃子必須隔一個棋子（炮架）" };
                }
            } else { // 移動
                if (piecesBetween !== 0) {
                    return { valid: false, reason: "炮移動路徑上不能有棋子" };
                }
            }
            mechanicallyValid = true;
            break;

        case '卒': case '兵':
            const forwardY = (piece.color === 'black') ? 1 : -1;
            const riverYPawn = (piece.color === 'black') ? 4 : 5; // 過河的 Y 坐標
            const isAcrossRiver = (piece.color === 'black' && from.y >= riverYPawn) || (piece.color === 'red' && from.y <= riverYPawn);

            let allowedMove = false;
            if (!isAcrossRiver) { // 未過河
                if (dx === 0 && dy === forwardY) allowedMove = true;
            } else { // 已過河
                if ((dx === 0 && dy === forwardY) || (dy === 0 && Math.abs(dx) === 1)) {
                    allowedMove = true;
                }
            }
            if (!allowedMove) {
                 const beforeRiverMsg = "過河前只能向前走一格";
                 const afterRiverMsg = "過河後只能向前或橫走一格";
                 return { valid: false, reason: !isAcrossRiver ? beforeRiverMsg : afterRiverMsg };
            }
            mechanicallyValid = true;
            break;

        default:
            console.error(`未知的棋子類型: ${piece.name}`);
            return { valid: false, reason: `未知的棋子類型: ${piece.name}` };
    }

    // 如果基礎移動規則都不滿足，提前返回
    if (!mechanicallyValid) {
        // 理論上不應該執行到這裡，因為前面每個 case 都有 return
        console.error("代碼邏輯錯誤：mechanicallyValid 為 false 但未返回");
        return { valid: false, reason: "未知棋子移動錯誤" };
    }


    // --- 最終檢查：移動後是否會導致己方被將軍 ---
    // 創建一個臨時棋盤模擬移動
    const tempBoard = createBoardCopy(board);
    tempBoard[to.y][to.x] = tempBoard[from.y][from.x];
    tempBoard[from.y][from.x] = null;

    // 在臨時棋盤上檢查己方是否被將軍
    if (isKingInCheck(tempBoard, playerColor)) {
        return { valid: false, reason: "移動後會導致己方將/帥被將軍" };
    }

    // 所有檢查通過
    return { valid: true, reason: "" };
}


/**
 * 創建棋盤狀態的深拷貝副本
 * @param {Array<Array<Object|null>>} board - 原始棋盤狀態
 * @returns {Array<Array<Object|null>>} - 棋盤的深拷貝副本
 */
function createBoardCopy(board) {
    return board.map(row => row.map(piece => piece ? {...piece} : null));
}


// --- 導出需要在 server.js 中使用的函數 ---
module.exports = {
    isValidMove,
    isKingInCheck,
    // isCheckmate, // 將來可以添加
    // isStalemate, // 將來可以添加
    createBoardCopy // 這個在 server.js 的自將檢查邏輯中需要用到
    // 輔助函數如 getPieceAt, canPieceMechanicallyReach 等是內部實現細節，不需要導出
};