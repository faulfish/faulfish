// utils.js - 工具函數，例如 FEN 轉換

const pieceToFenChar = {
    '俥': 'R', '傌': 'N', '相': 'B', '仕': 'A', '帥': 'K', '炮': 'C', '兵': 'P',
    '車': 'r', '馬': 'n', '象': 'b', '士': 'a', '將': 'k', '炮': 'c', '卒': 'p'
};

const fenCharToPiece = {
    'R': { name: '俥', color: 'red' }, 'N': { name: '傌', color: 'red' }, 'B': { name: '相', color: 'red' },
    'A': { name: '仕', color: 'red' }, 'K': { name: '帥', color: 'red' }, 'C': { name: '炮', color: 'red' },
    'P': { name: '兵', color: 'red' },
    'r': { name: '車', color: 'black' }, 'n': { name: '馬', color: 'black' }, 'b': { name: '象', color: 'black' },
    'a': { name: '士', color: 'black' }, 'k': { name: '將', color: 'black' }, 'c': { name: '炮', color: 'black' },
    'p': { name: '卒', color: 'black' }
};

/**
 * 將棋盤狀態轉換為 FEN 字符串
 * @param {Array<Array<Object|null>>} board
 * @param {String} turn 'red' or 'black'
 * @returns {String} FEN string
 */
function boardToFen(board, turn) {
    let fen = '';
    for (let y = 0; y < 10; y++) {
        let emptyCount = 0;
        for (let x = 0; x < 9; x++) {
            const piece = board[y]?.[x]; // Use optional chaining for safety
            if (piece) {
                if (emptyCount > 0) {
                    fen += emptyCount;
                    emptyCount = 0;
                }
                fen += pieceToFenChar[piece.name];
            } else {
                emptyCount++;
            }
        }
        if (emptyCount > 0) {
            fen += emptyCount;
        }
        if (y < 9) {
            fen += '/';
        }
    }
    fen += turn === 'red' ? ' w' : ' b';
    fen += ' - - 0 1'; // Placeholder for Xiangqi compatibility
    return fen;
}

/**
 * 將 FEN 字符串轉換回棋盤狀態
 * @param {String} fenString
 * @returns {Object|null} { board: Array<Array>, turn: 'red'|'black' } or null if invalid
 */
function fenToBoard(fenString) {
    const parts = fenString.trim().split(' ');
    if (parts.length < 2) return null;

    const board = Array(10).fill(null).map(() => Array(9).fill(null));
    const rows = parts[0].split('/');
    if (rows.length !== 10) return null;

    try {
        for (let y = 0; y < 10; y++) {
            let x = 0;
            for (const char of rows[y]) {
                if (x >= 9) throw new Error("FEN row too long");
                const num = parseInt(char);
                if (!isNaN(num)) {
                    if (num < 1 || num > 9) throw new Error("Invalid empty count");
                    x += num;
                } else {
                    const piece = fenCharToPiece[char];
                    if (!piece) throw new Error(`Invalid piece char: ${char}`);
                    board[y][x] = { ...piece };
                    x++;
                }
            }
            if (x !== 9) throw new Error("FEN row length mismatch");
        }
    } catch (e) {
        console.error("FEN Parsing Error:", e.message, "FEN:", fenString);
        return null;
    }

    const turn = parts[1].toLowerCase() === 'w' ? 'red' : 'black';
    return { board, turn };
}

module.exports = {
    boardToFen,
    fenToBoard
};