# -*- coding: utf-8 -*-
from config import (BOARD_SIZE, EMPTY, BLACK, WHITE, EDGE, DIRECTIONS)
from utils import is_on_board  # 假設 is_on_board 在 utils.py

# --- Rule Checking Functions ---

def count_line(r, c, player, board):
    """計算從 (r, c) 開始沿指定方向的 'player' 連續棋子數量及開放端點數。
       需要傳入棋盤狀態。"""
    lines = {}
    for direction in DIRECTIONS:
        dr, dc = direction
        count = 1
        open_ends = 0

        # 向前檢查
        cr, cc = r + dr, c + dc
        while is_on_board(cr, cc) and board[cr][cc] == player:
            count += 1
            cr, cc = cr + dr, cc + dc
        if is_on_board(cr, cc) and board[cr][cc] == EMPTY:
            open_ends += 1

        # 向後檢查
        cr, cc = r - dr, c - dc
        while is_on_board(cr, cc) and board[cr][cc] == player:
            count += 1
            cr, cc = cr - dr, cc - dc
        if is_on_board(cr, cc) and board[cr][cc] == EMPTY:
            open_ends += 1

        lines[direction] = (count, open_ends)
    return lines  # 返回包含所有方向結果的字典


def check_win_condition_at(r, c, player, board):
    """檢查在 (r, c) 落子是否為 'player' 帶來勝利。"""
    lines_info = count_line(r, c, player, board)
    for direction, (count, _) in lines_info.items():
        if player == BLACK and count == 5:
            return True
        if player == WHITE and count >= 5:
            return True
    return False


def check_specific_line_at(r, c, player, board, dr_dc, target):
    """檢查特定方向是否形成指定長度線段及是否活三。"""
    dr, dc = dr_dc
    line = []
    idx = -1
    T = target

    # 獲取指定方向上的棋子序列
    for i in range(T + 1, 0, -1):
        cr, cc = r - i * dr, c - i * dc
        if is_on_board(cr, cc):
            line.append(board[cr][cc])
        else:
            line.append(EDGE)

    line.append(player)
    idx = len(line) - 1

    for i in range(1, T + 2):
        cr, cc = r + i * dr, c + i * dc
        if is_on_board(cr, cc):
            line.append(board[cr][cc])
        else:
            line.append(EDGE)

    found = False
    open3 = False

    # 檢查是否形成指定長度的線段
    for i in range(len(line) - T + 1):
        sub = line[i:i + T]
        if all(s == player for s in sub) and i <= idx < i + T:
            left = line[i - 1] if i > 0 else EDGE
            right = line[i + T] if (i + T) < len(line) else EDGE
            longer = (left == player or right == player)

            if not longer:
                found = True
                if T == 3 and left == EMPTY and right == EMPTY:
                    open3 = True
                    break

    if T == 3:
        return found, open3
    else:
        return found, False


def check_forbidden_move_at(r, c, board):
    """檢查黑棋在 (r, c) 落子是否為禁手 (假設已臨時落子)。"""
    player = BLACK
    lines_info = count_line(r, c, player, board)  # 計算各個方向的連續棋子數量

    # 檢查長連
    for count, _ in lines_info.values():
        if count >= 6:
            return "長連"

    # 檢查雙三和雙四
    threes = 0
    fours = 0
    for direction in DIRECTIONS:
        is_four, _ = check_specific_line_at(r, c, player, board, direction, 4)
        if is_four:
            count4, _ = lines_info[direction]  # 使用預先計算的數量
            if count4 == 4:
                fours += 1

        is_three, is_open3 = check_specific_line_at(r, c, player, board, direction, 3)
        if is_open3:
            count3, _ = lines_info[direction]  # 使用預先計算的數量
            if count3 == 3:
                threes += 1

    if fours >= 2:
        return "四四"
    if threes >= 2 and fours < 2:
        return "三三"

    return None


def is_legal_move(r, c, player, move_count, board):
    """綜合檢查落子是否合法 (邊界, 佔用, 天元規則, 禁手)。"""
    if not is_on_board(r, c) or board[r][c] != EMPTY:
        return False, "Occupied or Off-board"

    if player == BLACK:
        if move_count == 0:  # 第一步規則
            return (True, None) if (r, c) == (7, 7) else (False, "First move must be Tengen (7,7)")
        else:  # 後續的黑棋走法 - 檢查禁手
            # 臨時模擬落子以檢查規則
            board[r][c] = player
            is_win = check_win_condition_at(r, c, player, board)
            forbidden_reason = None
            if not is_win:
                forbidden_reason = check_forbidden_move_at(r, c, board)
            board[r][c] = EMPTY  # 還原模擬
            return (False, forbidden_reason) if forbidden_reason else (True, None)
    else:  # 白棋
        return True, None  # 白棋沒有禁手或第一步規則