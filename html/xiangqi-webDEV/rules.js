// rules.js - 中國象棋規則引擎模塊 (優化版)

// --- 輔助函數 ---

function getPieceAt(board, x, y) {
    // 確保 y 在 0-9, x 在 0-8 範圍內
    if (y < 0 || y >= 10 || x < 0 || x >= 9) {
        return null;
    }
    // 使用可選鏈 ?. 防止訪問 board[y] 不存在時出錯 (雖然理論上 board 結構是固定的)
    return board[y]?.[x] || null; // 返回棋子對象或 null
}

function isWithinBoard(x, y) {
    return x >= 0 && x < 9 && y >= 0 && y < 10;
}

// 檢查坐標是否在指定顏色的九宮內
function isWithinPalace(x, y, color) {
    if (x < 3 || x > 5) return false;
    return (color === 'red') ? (y >= 7 && y <= 9) : (y >= 0 && y <= 2);
}

// 計算直線上兩點之間的棋子數量（不包括端點）
function countPiecesBetween(board, fromX, fromY, toX, toY) {
    let count = 0;
    if (fromY === toY) { // 水平
        const start = Math.min(fromX, toX) + 1;
        const end = Math.max(fromX, toX);
        for (let x = start; x < end; x++) {
            if (getPieceAt(board, x, fromY)) count++;
        }
    } else if (fromX === toX) { // 垂直
        const start = Math.min(fromY, toY) + 1;
        const end = Math.max(fromY, toY);
        for (let y = start; y < end; y++) {
            if (getPieceAt(board, fromX, y)) count++;
        }
    }
    // 非直線情況不應調用此函數
    return count;
}

// 創建棋盤的深拷貝
function createBoardCopy(board) {
    return board.map(row => row.map(piece => piece ? { ...piece } : null));
}

// --- 核心規則函數 ---

/**
 * 檢查指定顏色的王是否處於被將軍狀態
 * @param {Array<Array<Object|null>>} board - 棋盤狀態
 * @param {String} kingColor - 要檢查的王的顏色 ('red' or 'black')
 * @returns {boolean} - true 如果被將軍, false 否則
 */
function isKingInCheck(board, kingColor) {
    let kingX = -1, kingY = -1;
    let opponentKingX = -1, opponentKingY = -1; // 同時記錄對方王的位置以檢查照面
    const kingName = kingColor === 'red' ? '帥' : '將';
    const opponentKingName = kingColor === 'red' ? '將' : '帥';
    const opponentColor = kingColor === 'red' ? 'black' : 'red';

    // 1. 找到雙方王的位置
    for (let y = 0; y < 10; y++) {
        for (let x = 0; x < 9; x++) {
            const p = board[y][x];
            if (p) {
                if (p.name === kingName && p.color === kingColor) {
                    kingX = x; kingY = y;
                } else if (p.name === opponentKingName && p.color === opponentColor) {
                    opponentKingX = x; opponentKingY = y;
                }
            }
        }
        // 優化：如果雙方王都找到了，可以提前退出外層循環
        // if (kingX !== -1 && opponentKingX !== -1) break;
    }

    if (kingX === -1) {
        // console.error(`無法找到 ${kingColor} 方的王!`);
        return false; // 或者拋出錯誤，取決於你的錯誤處理策略
    }

    // 2. 檢查是否有對方棋子能 *機械地* 攻擊到王
    for (let y = 0; y < 10; y++) {
        for (let x = 0; x < 9; x++) {
            const attackerPiece = board[y][x];
            if (attackerPiece && attackerPiece.color === opponentColor) {
                // 使用內部輔助函數檢查純粹的攻擊路徑
                if (_canPieceMechanicallyAttack(board, attackerPiece, x, y, kingX, kingY)) {
                    return true;
                }
            }
        }
    }

    // 3. 檢查王是否照面 (必須找到對方王且在同一列，中間無子)
    if (opponentKingX !== -1 && kingX === opponentKingX) {
        if (countPiecesBetween(board, kingX, kingY, opponentKingX, opponentKingY) === 0) {
            return true;
        }
    }

    return false; // 所有檢查通過，未被將軍
}


/**
 * 內部輔助函數：檢查一個棋子是否能 *純粹機械地* 移動到目標位置（用於 isKingInCheck）
 * 不考慮輪到誰、是否自將等，只看路徑是否通暢以及是否符合棋子走法
 * @param {Array<Array<Object|null>>} board
 * @param {Object} piece - 要移動的棋子
 * @param {number} fromX - 起始 X
 * @param {number} fromY - 起始 Y
 * @param {number} toX - 目標 X
 * @param {number} toY - 目標 Y
 * @returns {boolean}
 */
function _canPieceMechanicallyAttack(board, piece, fromX, fromY, toX, toY) {
    // 注意：目標點 (toX, toY) 在 isKingInCheck 中是己方王的位置

    if (!isWithinBoard(toX, toY)) return false; // 目標不在棋盤內

    const dx = toX - fromX;
    const dy = toY - fromY;

    switch (piece.name) {
        case '車': case '俥':
            if (dx !== 0 && dy !== 0) return false; // 非直線
            return countPiecesBetween(board, fromX, fromY, toX, toY) === 0; // 路徑無阻礙
        case '馬': case '傌':
            const isValidHorseMove = (Math.abs(dx) === 1 && Math.abs(dy) === 2) || (Math.abs(dx) === 2 && Math.abs(dy) === 1);
            if (!isValidHorseMove) return false; // 非日字
            let blockX, blockY; // 馬腿位置
            if (Math.abs(dx) === 2) { blockX = fromX + dx / 2; blockY = fromY; }
            else { blockX = fromX; blockY = fromY + dy / 2; }
            return !getPieceAt(board, blockX, blockY); // 未蹩腿
        case '象': case '相':
            // 象/相不能直接攻擊到對方九宮內的王，因為中間隔著河界且有塞眼限制，它們只能防守
            return false;
        case '士': case '仕':
            // 士/仕也不能直接攻擊到對方九宮內的王，移動範圍受限
            return false;
        case '將': case '帥':
            // 將/帥的攻擊體現在 "照面" 規則中，由 isKingInCheck 主函數處理，這裡返回 false
            return false;
        case '炮':
            if (dx !== 0 && dy !== 0) return false; // 非直線
            // 炮攻擊必須要跳過一個子（炮架）
            return countPiecesBetween(board, fromX, fromY, toX, toY) === 1;
        case '卒': case '兵':
            const forwardY = (piece.color === 'black') ? 1 : -1; // 前進方向
            const riverY = (piece.color === 'black') ? 4 : 5;   // 過河的 Y 坐標界線 (y <= 4 為紅方區域, y >= 5 為黑方區域)
            const isAcrossRiver = (piece.color === 'black' && fromY >= riverY) || (piece.color === 'red' && fromY <= riverY);

            if (!isAcrossRiver) { // 未過河
                return (dx === 0 && dy === forwardY); // 只能前進
            } else { // 已過河
                const isForward = (dx === 0 && dy === forwardY);
                const isSideways = (dy === 0 && Math.abs(dx) === 1);
                return (isForward || isSideways); // 可前進或橫走
            }
        default:
            return false;
    }
}

/**
 * 生成指定位置棋子的所有 *完全合法* 的走法
 * @param {Array<Array<Object|null>>} board - 當前棋盤
 * @param {number} fromX - 棋子起始 X
 * @param {number} fromY - 棋子起始 Y
 * @returns {Array<Object>} - 返回一個包含所有合法目標點 {x, y} 的數組
 */
function generateLegalMovesForPiece(board, fromX, fromY) {
    const piece = getPieceAt(board, fromX, fromY);
    if (!piece) return []; // 起始點沒棋子

    const legalMoves = [];
    const playerColor = piece.color;

    // 遍歷棋盤所有可能的目標點 (可以優化，例如只檢查棋子能到達的範圍)
    for (let toY = 0; toY < 10; toY++) {
        for (let toX = 0; toX < 9; toX++) {
            // 使用 isValidMove 檢查每一步潛在的移動
            // 注意：isValidMove 内部會處理基礎規則和自將檢查
            // 我們需要傳遞一個最小化的 gameState 結構給它（如果它需要 turn 的話）
            // 或者修改 isValidMove 使其不依賴 gameState.turn
            const moveResult = isValidMoveInternal(board, { x: fromX, y: fromY }, { x: toX, y: toY }, playerColor);
            if (moveResult.valid) {
                legalMoves.push({ x: toX, y: toY });
            }
        }
    }
    return legalMoves;
}


/**
 * 內部使用的 isValidMove 版本，不依賴外部 gameState.turn
 * 檢查單步移動是否符合規則（包含自將檢查）
 * @param {Array<Array<Object|null>>} board - 當前棋盤
 * @param {Object} from - {x, y}
 * @param {Object} to - {x, y}
 * @param {String} playerColor - 移動方的顏色
 * @returns {Object} - { valid: boolean, reason: string }
 */
function isValidMoveInternal(board, from, to, playerColor) {
    // --- 基礎檢查 ---
    if (!isWithinBoard(from.x, from.y) || !isWithinBoard(to.x, to.y)) return { valid: false, reason: "出界" };
    const piece = getPieceAt(board, from.x, from.y);
    if (!piece || piece.color !== playerColor) return { valid: false, reason: "非己方棋子" };
    if (from.x === to.x && from.y === to.y) return { valid: false, reason: "原地踏步" };
    const targetPiece = getPieceAt(board, to.x, to.y);
    if (targetPiece && targetPiece.color === playerColor) return { valid: false, reason: "吃己方子" };

    // --- 棋子專屬移動規則檢查 (純機械) ---
    const dx = to.x - from.x;
    const dy = to.y - from.y;
    let mechanicallyValid = false;

    switch (piece.name) {
        case '車': case '俥':
            if ((dx === 0 || dy === 0) && countPiecesBetween(board, from.x, from.y, to.x, to.y) === 0) {
                mechanicallyValid = true;
            }
            break;
        case '馬': case '傌':
            const isValidHorseMove = (Math.abs(dx) === 1 && Math.abs(dy) === 2) || (Math.abs(dx) === 2 && Math.abs(dy) === 1);
            if (isValidHorseMove) {
                let blockX, blockY;
                if (Math.abs(dx) === 2) { blockX = from.x + dx / 2; blockY = from.y; }
                else { blockX = from.x; blockY = from.y + dy / 2; }
                if (!getPieceAt(board, blockX, blockY)) {
                    mechanicallyValid = true;
                }
            }
            break;
        case '象': case '相':
            if (Math.abs(dx) === 2 && Math.abs(dy) === 2) {
                 const riverYElephant = (piece.color === 'black') ? 4 : 5;
                 if (!((piece.color === 'black' && to.y > riverYElephant) || (piece.color === 'red' && to.y < riverYElephant))) {
                     const blockEyeX = from.x + dx / 2;
                     const blockEyeY = from.y + dy / 2;
                     if (!getPieceAt(board, blockEyeX, blockEyeY)) {
                         mechanicallyValid = true;
                     }
                 }
            }
            break;
        case '士': case '仕':
            if (Math.abs(dx) === 1 && Math.abs(dy) === 1) {
                if (isWithinPalace(to.x, to.y, piece.color)) {
                    mechanicallyValid = true;
                }
            }
            break;
        case '將': case '帥':
            if (Math.abs(dx) + Math.abs(dy) === 1) {
                if (isWithinPalace(to.x, to.y, piece.color)) {
                    mechanicallyValid = true;
                }
            }
            break;
        case '炮':
            if (dx === 0 || dy === 0) {
                const piecesBetween = countPiecesBetween(board, from.x, from.y, to.x, to.y);
                if (targetPiece) { // 吃子
                    if (piecesBetween === 1) mechanicallyValid = true;
                } else { // 移動
                    if (piecesBetween === 0) mechanicallyValid = true;
                }
            }
            break;
        case '卒': case '兵':
            const forwardY = (piece.color === 'black') ? 1 : -1;
            const riverYPawn = (piece.color === 'black') ? 4 : 5;
            const isAcrossRiver = (piece.color === 'black' && from.y >= riverYPawn) || (piece.color === 'red' && from.y <= riverYPawn);
            if (!isAcrossRiver) {
                if (dx === 0 && dy === forwardY) mechanicallyValid = true;
            } else {
                if ((dx === 0 && dy === forwardY) || (dy === 0 && Math.abs(dx) === 1)) {
                    mechanicallyValid = true;
                }
            }
            break;
    }

    if (!mechanicallyValid) {
        return { valid: false, reason: "不符合棋子走法" }; // 如果連機械走法都不滿足，直接返回
    }

    // --- 自將檢查 ---
    const tempBoard = createBoardCopy(board);
    tempBoard[to.y][to.x] = tempBoard[from.y][from.x]; // 模擬移動
    tempBoard[from.y][from.x] = null;

    if (isKingInCheck(tempBoard, playerColor)) {
        return { valid: false, reason: "會導致己方被將" }; // 自將了，非法
    }

    // 所有檢查通過
    return { valid: true, reason: "" };
}


/**
 * 檢查指定顏色的玩家是否被將死 (Checkmate)
 * @param {Array<Array<Object|null>>} board - 當前棋盤狀態
 * @param {String} kingColor - 被檢查是否將死的一方顏色 ('red' or 'black')
 * @returns {boolean} - true 如果被將死, false 否則
 */
function isCheckmate(board, kingColor) {
    // 1. 必須先處於被將軍狀態
    if (!isKingInCheck(board, kingColor)) {
        return false;
    }

    // 2. 檢查是否存在任何一步合法的棋步可以解除將軍狀態
    for (let y = 0; y < 10; y++) {
        for (let x = 0; x < 9; x++) {
            const piece = getPieceAt(board, x, y);
            if (piece && piece.color === kingColor) {
                // 找到該棋子的所有合法走法
                const legalMoves = generateLegalMovesForPiece(board, x, y);
                // 只要存在任何一個合法走法，就說明沒有被將死
                if (legalMoves.length > 0) {
                    return false;
                }
            }
        }
    }

    // 3. 遍歷完所有己方棋子，都找不到任何合法走法，說明被將死
    return true;
}


/**
 * 檢查指定顏色的玩家是否處於無子可動 (Stalemate / 困斃)
 * @param {Array<Array<Object|null>>} board - 當前棋盤狀態
 * @param {String} kingColor - 被檢查是否困斃的一方顏色 ('red' or 'black')
 * @returns {boolean} - true 如果困斃, false 否則
 */
function isStalemate(board, kingColor) {
    // 1. 必須不能處於被將軍狀態
    if (isKingInCheck(board, kingColor)) {
        return false;
    }

    // 2. 檢查是否存在任何一步合法的棋步
    for (let y = 0; y < 10; y++) {
        for (let x = 0; x < 9; x++) {
            const piece = getPieceAt(board, x, y);
            if (piece && piece.color === kingColor) {
                // 找到該棋子的所有合法走法
                const legalMoves = generateLegalMovesForPiece(board, x, y);
                // 只要存在任何一個合法走法，就說明沒有被困斃
                if (legalMoves.length > 0) {
                    return false;
                }
            }
        }
    }

    // 3. 遍歷完所有己方棋子，都找不到任何合法走法，且未被將軍，說明困斃
    return true;
}


/**
 * (公開接口) 檢查一步棋是否合法 (給 server.js 調用)
 * @param {Object} gameState - 包含 board 和 turn
 * @param {Object} from - {x, y}
 * @param {Object} to - {x, y}
 * @param {String} playerColor - 移動方顏色
 */
function isValidMove(gameState, from, to, playerColor) {
     // 可以在這裡加入 gameState.turn 的判斷，如果需要的話
     if (gameState.turn !== playerColor) {
          return { valid: false, reason: "還沒輪到你走棋" };
     }
     // 調用內部實現
     return isValidMoveInternal(gameState.board, from, to, playerColor);
}


// --- 導出公開接口 ---
module.exports = {
    isValidMove,      // 檢查單步移動合法性 (供 server.js 使用)
    isKingInCheck,    // 檢查是否被將軍
    isCheckmate,      // 檢查是否將死
    isStalemate,      // 檢查是否困斃
    createBoardCopy,  // 複製棋盤狀態 (如果 server.js 其他地方需要)
    // generateLegalMovesForPiece // 這個主要供內部使用，可以不導出
};