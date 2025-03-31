// rules.js - 中國象棋規則引擎模塊 (包含 isCheckmate/isStalemate)

// --- 輔助函數 ---
function getPieceAt(board, x, y) { if (y < 0 || y >= 10 || x < 0 || x >= 9) return null; return board[y]?.[x] || null; }
function isWithinBoard(x, y) { return x >= 0 && x < 9 && y >= 0 && y < 10; }
function isWithinPalace(x, y, color) { if (x < 3 || x > 5) return false; return (color === 'red') ? (y >= 7 && y <= 9) : (y >= 0 && y <= 2); }
function countPiecesBetween(board, fromX, fromY, toX, toY) {
    let count = 0;
    if (fromY === toY) { const start = Math.min(fromX, toX) + 1; const end = Math.max(fromX, toX); for (let x = start; x < end; x++) if (getPieceAt(board, x, fromY)) count++; }
    else if (fromX === toX) { const start = Math.min(fromY, toY) + 1; const end = Math.max(fromY, toY); for (let y = start; y < end; y++) if (getPieceAt(board, fromX, y)) count++; }
    return count;
}
function createBoardCopy(board) { return board.map(row => row.map(piece => piece ? { ...piece } : null)); }

// --- 核心規則函數 ---
function isKingInCheck(board, kingColor) {
    let kingX = -1, kingY = -1, opponentKingX = -1, opponentKingY = -1;
    const kingName = kingColor === 'red' ? '帥' : '將'; const opponentKingName = kingColor === 'red' ? '將' : '帥'; const opponentColor = kingColor === 'red' ? 'black' : 'red';
    for (let y = 0; y < 10; y++) for (let x = 0; x < 9; x++) { const p = board[y][x]; if (p) { if (p.name === kingName && p.color === kingColor) { kingX = x; kingY = y; } else if (p.name === opponentKingName && p.color === opponentColor) { opponentKingX = x; opponentKingY = y; } } }
    if (kingX === -1) return false;
    for (let y = 0; y < 10; y++) for (let x = 0; x < 9; x++) { const attackerPiece = board[y][x]; if (attackerPiece && attackerPiece.color === opponentColor) if (_canPieceMechanicallyAttack(board, attackerPiece, x, y, kingX, kingY)) return true; }
    if (opponentKingX !== -1 && kingX === opponentKingX) if (countPiecesBetween(board, kingX, kingY, opponentKingX, opponentKingY) === 0) return true;
    return false;
}

function _canPieceMechanicallyAttack(board, piece, fromX, fromY, toX, toY) {
    if (!isWithinBoard(toX, toY)) return false; const dx = toX - fromX; const dy = toY - fromY;
    switch (piece.name) {
        case '車': case '俥': if (dx !== 0 && dy !== 0) return false; return countPiecesBetween(board, fromX, fromY, toX, toY) === 0;
        case '馬': case '傌': const isValidHorseMove = (Math.abs(dx) === 1 && Math.abs(dy) === 2) || (Math.abs(dx) === 2 && Math.abs(dy) === 1); if (!isValidHorseMove) return false; let blockX, blockY; if (Math.abs(dx) === 2) { blockX = fromX + dx / 2; blockY = fromY; } else { blockX = fromX; blockY = fromY + dy / 2; } return !getPieceAt(board, blockX, blockY);
        case '象': case '相': return false;
        case '士': case '仕': return false;
        case '將': case '帥': return false;
        case '炮': if (dx !== 0 && dy !== 0) return false; return countPiecesBetween(board, fromX, fromY, toX, toY) === 1;
        case '卒': case '兵': const forwardY = (piece.color === 'black') ? 1 : -1; const riverY = (piece.color === 'black') ? 4 : 5; const isAcrossRiver = (piece.color === 'black' && fromY >= riverY) || (piece.color === 'red' && fromY <= riverY); if (!isAcrossRiver) return (dx === 0 && dy === forwardY); else { const isForward = (dx === 0 && dy === forwardY); const isSideways = (dy === 0 && Math.abs(dx) === 1); return (isForward || isSideways); }
        default: return false;
    }
}

function generateLegalMovesForPiece(board, fromX, fromY) {
    const piece = getPieceAt(board, fromX, fromY); if (!piece) return []; const legalMoves = []; const playerColor = piece.color;
    for (let toY = 0; toY < 10; toY++) for (let toX = 0; toX < 9; toX++) { const moveResult = isValidMoveInternal(board, { x: fromX, y: fromY }, { x: toX, y: toY }, playerColor); if (moveResult.valid) legalMoves.push({ x: toX, y: toY }); }
    return legalMoves;
}

// *** 核心: 內部使用的移動驗證，不檢查 gameState.turn ***
function isValidMoveInternal(board, from, to, playerColor) {
    if (!isWithinBoard(from.x, from.y) || !isWithinBoard(to.x, to.y)) return { valid: false, reason: "出界" };
    const piece = getPieceAt(board, from.x, from.y);
    if (!piece || piece.color !== playerColor) return { valid: false, reason: "非指定顏色棋子" };
    if (from.x === to.x && from.y === to.y) return { valid: false, reason: "原地踏步" };
    const targetPiece = getPieceAt(board, to.x, to.y);
    if (targetPiece && targetPiece.color === playerColor) return { valid: false, reason: "吃己方子" };

    const dx = to.x - from.x; const dy = to.y - from.y; let mechanicallyValid = false;
    switch (piece.name) {
        case '車': case '俥': if ((dx === 0 || dy === 0) && countPiecesBetween(board, from.x, from.y, to.x, to.y) === 0) mechanicallyValid = true; break;
        case '馬': case '傌': const isValidHorseMove = (Math.abs(dx) === 1 && Math.abs(dy) === 2) || (Math.abs(dx) === 2 && Math.abs(dy) === 1); if (isValidHorseMove) { let blockX, blockY; if (Math.abs(dx) === 2) { blockX = from.x + dx / 2; blockY = from.y; } else { blockX = from.x; blockY = from.y + dy / 2; } if (!getPieceAt(board, blockX, blockY)) mechanicallyValid = true; } break;
        case '象': case '相': if (Math.abs(dx) === 2 && Math.abs(dy) === 2) { const riverYElephant = (piece.color === 'black') ? 4 : 5; if (!((piece.color === 'black' && to.y > riverYElephant) || (piece.color === 'red' && to.y < riverYElephant))) { const blockEyeX = from.x + dx / 2; const blockEyeY = from.y + dy / 2; if (!getPieceAt(board, blockEyeX, blockEyeY)) mechanicallyValid = true; } } break;
        case '士': case '仕': if (Math.abs(dx) === 1 && Math.abs(dy) === 1) if (isWithinPalace(to.x, to.y, piece.color)) mechanicallyValid = true; break;
        case '將': case '帥': if (Math.abs(dx) + Math.abs(dy) === 1) if (isWithinPalace(to.x, to.y, piece.color)) mechanicallyValid = true; break;
        case '炮': if (dx === 0 || dy === 0) { const piecesBetween = countPiecesBetween(board, from.x, from.y, to.x, to.y); if (targetPiece) { if (piecesBetween === 1) mechanicallyValid = true; } else { if (piecesBetween === 0) mechanicallyValid = true; } } break;
        case '卒': case '兵': const forwardY = (piece.color === 'black') ? 1 : -1; const riverYPawn = (piece.color === 'black') ? 4 : 5; const isAcrossRiver = (piece.color === 'black' && from.y >= riverYPawn) || (piece.color === 'red' && from.y <= riverYPawn); if (!isAcrossRiver) { if (dx === 0 && dy === forwardY) mechanicallyValid = true; } else { if ((dx === 0 && dy === forwardY) || (dy === 0 && Math.abs(dx) === 1)) mechanicallyValid = true; } break;
        default: return { valid: false, reason: `未知棋子: ${piece.name}`}; // Add default case
    }
    if (!mechanicallyValid) return { valid: false, reason: "不符合棋子走法" };

    const tempBoard = createBoardCopy(board); tempBoard[to.y][to.x] = tempBoard[from.y][from.x]; tempBoard[from.y][from.x] = null;
    if (isKingInCheck(tempBoard, playerColor)) return { valid: false, reason: "會導致己方被將" };

    return { valid: true, reason: "" };
}

function isCheckmate(board, kingColor) {
    if (!isKingInCheck(board, kingColor)) return false;
    for (let y = 0; y < 10; y++) for (let x = 0; x < 9; x++) { const piece = getPieceAt(board, x, y); if (piece && piece.color === kingColor) if (generateLegalMovesForPiece(board, x, y).length > 0) return false; }
    return true;
}

function isStalemate(board, kingColor) {
    if (isKingInCheck(board, kingColor)) return false;
    for (let y = 0; y < 10; y++) for (let x = 0; x < 9; x++) { const piece = getPieceAt(board, x, y); if (piece && piece.color === kingColor) if (generateLegalMovesForPiece(board, x, y).length > 0) return false; }
    return true;
}

// 公開接口 (如果需要區分標準模式和分析模式)
function isValidMove(gameState, from, to, playerColor) {
     // 標準模式下檢查輪次
     if (gameState.turn !== playerColor) return { valid: false, reason: "還沒輪到你走棋 (標準模式)" };
     // 都調用內部驗證
     return isValidMoveInternal(gameState.board, from, to, playerColor);
}

// --- 導出 ---
module.exports = {
    isValidMove,         // 供標準模式使用 (檢查輪次)
    isValidMoveInternal, // 供分析板模式使用 (不檢查輪次)
    isKingInCheck,
    isCheckmate,
    isStalemate,
    createBoardCopy
};