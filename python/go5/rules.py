# -*- coding: utf-8 -*-
import copy # 為了 temp_board，雖然這裡可能不需要深拷貝

# Assume these are defined elsewhere or replace with actual values/imports
BOARD_SIZE = 15
EMPTY = 0
BLACK = 1
WHITE = 2
EDGE = -1
DIRECTIONS = [(0, 1), (1, 0), (1, 1), (1, -1)] # Horizontal, Vertical, Diag /, Diag \

# Assume is_on_board is defined (e.g., from utils.py)
def is_on_board(r, c):
    """Checks if coordinates are within the board bounds."""
    return 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE

# --- Rule Checking Functions ---

def count_line(r, c, player, board):
    """計算從 (r, c) 開始沿指定方向的 'player' 連續棋子數量及開放端點數。
       (保持原樣，用於長連和勝利檢查)"""
    lines = {}
    for direction in DIRECTIONS:
        dr, dc = direction
        count = 1 # Start counting the stone at (r, c)
        open_ends = 0
        line_indices = [(r, c)] # Keep track of stones in the line

        # 向前檢查 (Positive direction)
        cr, cc = r + dr, c + dc
        while is_on_board(cr, cc) and board[cr][cc] == player:
            count += 1
            line_indices.append((cr, cc))
            cr, cc = cr + dr, cc + dc
        # Check the position *after* the continuous line
        if is_on_board(cr, cc) and board[cr][cc] == EMPTY:
            open_ends += 1
        elif not is_on_board(cr, cc): # Off board counts as blocked
            pass # open_ends remains 0 on this side
        # Else (opponent stone), also blocked

        # 向後檢查 (Negative direction)
        cr, cc = r - dr, c - dc
        while is_on_board(cr, cc) and board[cr][cc] == player:
            count += 1
            line_indices.append((cr, cc)) # Add stones from the other direction too
            cr, cc = cr - dr, cc - dc
        # Check the position *after* the continuous line
        if is_on_board(cr, cc) and board[cr][cc] == EMPTY:
            open_ends += 1
        elif not is_on_board(cr, cc): # Off board counts as blocked
             pass # open_ends contribution remains 0 from this side
        # Else (opponent stone), also blocked

        # Store count and open ends for the full line through (r,c)
        lines[direction] = (count, open_ends)
    return lines


def check_win_condition_at(r, c, player, board):
    """檢查在 (r, c) 落子是否為 'player' 帶來勝利。
       (保持原樣, 注意黑棋只能恰好5子)"""
    lines_info = count_line(r, c, player, board)
    for direction, (count, _) in lines_info.items():
        # Standard rule: White wins with 5 or more, Black wins *only* with exactly 5
        # If Black makes > 5 (long line), it's often a forbidden move, not a win.
        if player == BLACK and count == 5:
            return True
        if player == WHITE and count >= 5:
            return True
    return False

# --- 改良後的 check_specific_line_at ---
# --- 參數和返回值簽名保持不變 ---
# target = 3, 判斷三三禁手 (活三), target = 4, 判斷四四禁手 (任意精確四連)
def check_specific_line_at(r, c, player, board, dr_dc, target):
    """
    (參數和返回值保持不變)
    檢查在棋盤 (board) 的座標 (r, c) 處，模擬落下 'player' 的棋子後，
    在指定的方向 'dr_dc' 上：
    - 若 target=3: 是否會形成「活三」(Open/Live Three)，包含落子點。
    - 若 target=4: 是否會形成「恰好為四」的連線 (Exact Four)，包含落子點且非更長。
    能處理連續和跳子 ('Jump') 形成的情況。

    返回:
        Tuple[bool, bool]:
          - bool: (此返回值在此修改版中意義不大，主要看第二個)
                  為 True 表示可能找到了某種目標長度的模式。
          - bool: - 若 target=3: True 表示找到了「活三」。
                  - 若 target=4: True 表示找到了「恰好為四」的連線。
                                (注意：對於 T=4，我們將第二個返回值用來表示是否找到四，
                                 而非原始碼中的 is_open_three 概念)
    """
    board_size = len(board)
    dr, dc = dr_dc
    line = []
    placed_stone_idx = -1

    # --- 1. 建立檢查線段 ---
    # 採樣足夠的點以檢測包含跳子的模式。
    # 對於目標 T，需要 T 個棋子 + 可能的空位 + 兩側。
    # 向前後各採樣 T+2 步應足以涵蓋 X.XXX 或 XX.XX 類型的跳子。
    max_len = target + 2
    for i in range(max_len, 0, -1): # 向後檢查 max_len 步
        cr, cc = r - i * dr, c - i * dc
        if is_on_board(cr, cc):
            line.append(board[cr][cc])
        else:
            line.append(EDGE)

    # 模擬落子
    line.append(player)
    placed_stone_idx = len(line) - 1 # 記錄模擬落子在線段中的索引

    for i in range(1, max_len + 1): # 向前檢查 max_len 步
        cr, cc = r + i * dr, c + i * dc
        if is_on_board(cr, cc):
            line.append(board[cr][cc])
        else:
            line.append(EDGE)

    # --- 2. 在模擬線段中搜索目標模式 ---
    # 注意：對於三三和四四禁手，我們真正關心的是是否存在 "活三" 或 "任意四連"。
    # 因此，返回值主要依賴於第二個布爾值。

    # --- Target = 3: 檢查活三 (Live Three) ---
    if target == 3:
        # 檢查連續活三: _BBB_
        # 模式: [EMPTY, player, player, player, EMPTY]
        pattern_len = 5
        for i in range(len(line) - pattern_len + 1):
            sub = line[i : i + pattern_len]
            if sub == [EMPTY, player, player, player, EMPTY]:
                # 檢查落子是否為這三個 player 棋子之一
                if i + 1 <= placed_stone_idx <= i + 3:
                    return True, True # (找到了模式, 是活三)

        # 檢查跳活三 (Jump Live Three)
        # 模式 _B.BB_: [EMPTY, player, EMPTY, player, player, EMPTY]
        pattern_len = 6
        for i in range(len(line) - pattern_len + 1):
            sub = line[i : i + pattern_len]
            if sub == [EMPTY, player, EMPTY, player, player, EMPTY]:
                 # 檢查落子是否為 player 棋子之一 (索引相對i: 1, 3, 4)
                 if placed_stone_idx in [i + 1, i + 3, i + 4]:
                      return True, True # (找到了模式, 是活三)

        # 模式 _BB.B_: [EMPTY, player, player, EMPTY, player, EMPTY]
        pattern_len = 6
        for i in range(len(line) - pattern_len + 1):
             sub = line[i : i + pattern_len]
             if sub == [EMPTY, player, player, EMPTY, player, EMPTY]:
                  # 檢查落子是否為 player 棋子之一 (索引相對i: 1, 2, 4)
                  if placed_stone_idx in [i + 1, i + 2, i + 4]:
                       return True, True # (找到了模式, 是活三)

        # 如果以上檢查都沒有找到活三
        return False, False # (未找到模式, 不是活三)

    # --- Target = 4: 檢查任意精確四連 (Exact Four) ---
    elif target == 4:
        # 檢查連續精確四連: XPPPPX (X != player)
        pattern_len = 4
        # 迭代範圍確保可以檢查左右側翼 (i-1 and i+4)
        for i in range(1, len(line) - pattern_len):
            sub = line[i : i + pattern_len]
            if all(s == player for s in sub):
                # 檢查落子是否為這四個 player 棋子之一
                if i <= placed_stone_idx < i + pattern_len:
                    left_flank = line[i-1]
                    right_flank = line[i+pattern_len]
                    # 檢查是否*恰好*為四 (兩側都不是 player)
                    if left_flank != player and right_flank != player:
                        return True, True # (找到了模式, 是四連)

        # 檢查跳四 (Jump Exact Four)
        # 模式 X P.PPP X (X != player)
        pattern_len = 5 # P E P P P
        # 迭代範圍確保可以檢查左右側翼 (i-1 and i+5)
        for i in range(1, len(line) - pattern_len):
            sub = line[i : i + pattern_len]
            if sub == [player, EMPTY, player, player, player]:
                 # player 棋子索引相對i: 0, 2, 3, 4
                 if placed_stone_idx in [i + 0, i + 2, i + 3, i + 4]:
                      left_flank = line[i-1]
                      right_flank = line[i+pattern_len]
                      if left_flank != player and right_flank != player:
                           return True, True # (找到了模式, 是四連)

        # 模式 X PP.PP X (X != player)
        pattern_len = 5 # P P E P P
        for i in range(1, len(line) - pattern_len):
             sub = line[i : i + pattern_len]
             if sub == [player, player, EMPTY, player, player]:
                  # player 棋子索引相對i: 0, 1, 3, 4
                  if placed_stone_idx in [i + 0, i + 1, i + 3, i + 4]:
                       left_flank = line[i-1]
                       right_flank = line[i+pattern_len]
                       if left_flank != player and right_flank != player:
                            return True, True # (找到了模式, 是四連)

        # 模式 X PPP.P X (X != player)
        pattern_len = 5 # P P P E P
        for i in range(1, len(line) - pattern_len):
             sub = line[i : i + pattern_len]
             if sub == [player, player, player, EMPTY, player]:
                  # player 棋子索引相對i: 0, 1, 2, 4
                  if placed_stone_idx in [i + 0, i + 1, i + 2, i + 4]:
                       left_flank = line[i-1]
                       right_flank = line[i+pattern_len]
                       if left_flank != player and right_flank != player:
                            return True, True # (找到了模式, 是四連)

        # 如果以上檢查都沒有找到精確四連
        return False, False # (未找到模式, 不是四連)

    # 如果 target 不是 3 或 4 (理論上不應發生)
    return False, False


# --- Corrected check_forbidden_move_at ---
# --- This function now correctly uses check_specific_line_at results ---

def check_forbidden_move_at(r, c, board):
    """
    檢查黑棋在 (r, c) 落子是否為禁手 (假設已臨時落子在 board 上)。
    使用 check_specific_line_at 判斷三三和四四。
    使用 count_line 判斷長連。
    """
    player = BLACK # Forbidden moves apply only to Black

    # --- 檢查長連 (使用 count_line) ---
    # count_line is suitable here as it counts consecutive stones from the placed point.
    # If Black places a stone and the resulting continuous line has 6 or more stones, it's a long line.
    lines_info = count_line(r, c, player, board)
    for count, _ in lines_info.values():
        if count >= 6:
            # print(f"Debug: Forbidden - Long Line ({count}) at ({r},{c})")
            return "長連"

    # --- 檢查雙三和雙四 (使用 check_specific_line_at) ---
    open_threes_count = 0
    fours_count = 0

    for direction in DIRECTIONS:
        # Check for exact fours formed by this move (handles jumps)
        # found4 will be True if an exact four (_OOOO, OOOO_, O_OOO etc.) is formed.
        # The second return value is ignored as it's always False for target=4.
        found4, _ = check_specific_line_at(r, c, player, board, direction, 4)
        if found4:
            # print(f"Debug: Found exact four at ({r},{c}) in direction {direction}")
            fours_count += 1

        # Check for open threes formed by this move (handles jumps)
        # is_open3 will be True only if an open three (_OOO_) is formed.
        # found3 indicates if *any* exact three (open or closed) was found.
        found3, is_open3 = check_specific_line_at(r, c, player, board, direction, 3)
        if is_open3:
            # print(f"Debug: Found open three at ({r},{c}) in direction {direction}")
            open_threes_count += 1

    # --- 判斷禁手 ---
    # A double four occurs if placing the stone creates two or more lines of exactly four simultaneously.
    if fours_count >= 2:
        # print(f"Debug: Forbidden - Double Four ({fours_count}) at ({r},{c})")
        return "四四"

    # A double three occurs if placing the stone creates two or more *open* threes simultaneously.
    # Importantly, forming fours simultaneously *negates* the double three forbidden rule according to some rule sets.
    # The check `fours < 2` is sometimes added, but standard rules usually prioritize four/five over three.
    # Let's assume forming fours doesn't prevent a three-three if two open threes *also* exist independently.
    # If the intent is that forming a four means it's not a three-three, add `and fours_count == 0`.
    if open_threes_count >= 2:
       # print(f"Debug: Forbidden - Double Three ({open_threes_count}) at ({r},{c})")
       return "三三"

    # No forbidden move detected
    return None


# --- is_legal_move (Remains the same, relies on corrected check_forbidden_move_at) ---

def is_legal_move(r, c, player, move_count, board):
    # print(f"rules is_legal_move({r},{c})")
    """
    綜合檢查落子是否合法 (邊界, 佔用, 天元規則, 禁手)。
    """
    # 1. 檢查邊界
    if not is_on_board(r, c):
        return False, "Occupied or Off-board" # 或者 "Off-board"

    # *** 2. 檢查是否已被佔據 (使用原始 board) *** <--- 新增/修正
    if board[r][c] != EMPTY:
        return False, "Occupied or Off-board" # 或者 "Occupied"
    # ******************************************

    # 3. 檢查天元規則 (僅黑棋第一步)
    if player == BLACK and move_count == 0:
        center = BOARD_SIZE // 2
        if (r, c) != (center, center):
            return False, f"First move must be Tengen ({center},{center})"
        # 如果是天元，不需要再檢查禁手和勝利，直接返回 True
        # （因為不可能在第一步形成禁手或勝利）
        # print(f"center pos")
        return True, None # 天元總是合法的 (如果界內且未佔用)

    # --- 只有在非第一步天元，且未佔用時，才需要模擬和檢查後續 ---
    # --- Create a temporary board copy to simulate the move ---
    # temp_board = [row[:] for row in board] # 淺拷貝通常足夠
    # 或者使用深拷貝確保完全獨立（如果後續檢查會修改列表內部結構）
    temp_board = copy.deepcopy(board)


    # 4. Simulate the move on the temporary board
    temp_board[r][c] = player

    # 5. Check for win condition first (Winning move overrides forbidden moves)
    if check_win_condition_at(r, c, player, temp_board):
        # print(f"win pos")
        return True, None # Winning move is always legal

    # 6. If not a winning move, check for forbidden moves (only for Black)
    if player == BLACK:
        forbidden_reason = check_forbidden_move_at(r, c, temp_board)
        if forbidden_reason:
            # print(f"{r},{c} is {forbidden_reason}")
            return False, forbidden_reason # Return the specific reason
        else:
            # print(f"{r},{c} is legal B")
            return True, None # Not forbidden, not win -> legal for Black
    else: # player == WHITE
        # White has no forbidden moves. If it's not occupied, on board, and not a win, it's legal.
        # print(f"{r},{c} is legal")
        return True, None

# Example usage (conceptual)
# board = [[EMPTY] * BOARD_SIZE for _ in range(BOARD_SIZE)]
# move_count = 0
# player = BLACK
# r, c = 7, 7
# legal, reason = is_legal_move(r, c, player, move_count, board)
# print(f"Move at ({r},{c}) for {player}: Legal={legal}, Reason={reason}")
# # ... place stone ... move_count += 1 ... switch player ...