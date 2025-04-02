# -*- coding: utf-8 -*-
import random
from config import (BOARD_SIZE, EMPTY, BLACK, WHITE, DIRECTIONS)
from utils import is_on_board
import rules # 導入 rules 模塊以使用 is_legal_move 等
# --- 從 game_io 導入 OPENING_BOOK 和保存函數 ---
from game_io import OPENING_BOOK, save_opening_book_to_file # <-- 確認導入

# --- AI Decision Logic ---

def find_best_ai_move(board, move_log, move_count, current_player):
    """AI 尋找最佳著法，加入開局庫、天元規則和啟發式隨機選擇。"""
    ai_player = current_player
    opponent_player = WHITE if ai_player == BLACK else BLACK
    used_book_flag = False

    # Strategy -1: AI Black First Move
    if move_count == 0 and ai_player == BLACK:
        valid,_ = rules.is_legal_move(7, 7, ai_player, move_count, board) # 使用 rules.
        move = (7, 7) if valid else None
        if move: print(f"AI ({ai_player}) mandatory Tengen"); return move, False

    # Strategy 0: Opening Book
    if move_count > 0:
        # global OPENING_BOOK # 不再需要 global
        current_move_sequence = tuple(tuple(m[k] for k in ['row','col']) for m in move_log)
        if current_move_sequence in OPENING_BOOK: # 直接使用導入的 OPENING_BOOK
            possible = OPENING_BOOK[current_move_sequence]
            valid_moves = []
            if isinstance(possible, list):
                 valid_moves=[m for m in possible if rules.is_legal_move(m[0],m[1],ai_player, move_count, board)[0]] # 使用 rules.
            if valid_moves:
                 move=random.choice(valid_moves); print(f"AI ({ai_player}) using book {move} from {len(valid_moves)}"); return move, True
            else: print(f"AI ({ai_player}) book seq found but no valid moves. Fallback.")

    # Strategies 1, 2, 2.25, 2.5, 3
    empty = []; occupied = set();
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE): (empty.append((r,c)) if board[r][c]==EMPTY else occupied.add((r,c)))
    if not empty: print(f"AI ({ai_player}) no empty spots."); return None, False

    # --- Helper (使用 rules 模塊函數) ---
    def check_temp_move(r, c, player_to_check, check_func, *args):
         if board[r][c] == EMPTY:
             board[r][c] = player_to_check
             result = check_func(r, c, player_to_check, board, *args) # Pass board
             board[r][c] = EMPTY
             return result
         return False

    # 1. Win
    for r,c in empty:
        valid,_ = rules.is_legal_move(r, c, ai_player, move_count, board)
        if valid and check_temp_move(r, c, ai_player, rules.check_win_condition_at):
            print(f"AI ({ai_player}) found win at ({r},{c})"); return (r,c), False

    # 2. Block Win
    for r,c in empty:
        if check_temp_move(r, c, opponent_player, rules.check_win_condition_at):
            block_ok,_ = rules.is_legal_move(r, c, ai_player, move_count, board)
            if block_ok: print(f"AI ({ai_player}) blocking win at ({r},{c})"); return (r,c), False

    # 2.25: Block Threatening Four
    four_blocks = []
    for r, c in empty:
         board[r][c] = opponent_player
         forms_threatening_four = False
         lines_info = rules.count_line(r, c, opponent_player, board) # Use rules.
         for count, ends in lines_info.values():
              if count == 4 and ends >= 1: forms_threatening_four = True; break
         board[r][c] = EMPTY
         if forms_threatening_four:
              can_block_here, _ = rules.is_legal_move(r, c, ai_player, move_count, board)
              if can_block_here: four_blocks.append((r, c))
    if four_blocks: move=random.choice(four_blocks); print(f"AI ({ai_player}) blocking four at {move}"); return move, False

    # 2.5: Block Open Three
    three_blocks = []
    for r, c in empty:
         board[r][c] = opponent_player
         forms_open_three = False
         for dr_dc in DIRECTIONS:
              is_three, is_open = rules.check_specific_line_at(r, c, opponent_player, board, dr_dc, 3) # Use rules.
              if is_open:
                   lines_info_temp = rules.count_line(r, c, opponent_player, board) # Use rules.
                   count_overall, _ = lines_info_temp[dr_dc]
                   if count_overall == 3: forms_open_three = True; break
         board[r][c] = EMPTY
         if forms_open_three:
              can_block_here, _ = rules.is_legal_move(r, c, ai_player, move_count, board)
              if can_block_here: three_blocks.append((r, c))
    if three_blocks: move=random.choice(three_blocks); print(f"AI ({ai_player}) blocking open three at {move}"); return move, False

    # 3. Adjacent/Random
    candidates=[]; adjacent=set(); offsets=[(dr,dc) for dr in [-1,0,1] for dc in [-1,0,1] if not (dr==0 and dc==0)]
    if ai_player==WHITE and move_count==1 and board[7][7]==BLACK:
        for dr,dc in offsets: nr,nc=7+dr,7+dc; adjacent.add((nr,nc)) if is_on_board(nr,nc) and board[nr][nc]==EMPTY else None
    else:
         for r_o,c_o in occupied:
             for dr,dc in offsets: nr,nc=r_o+dr,c_o+dc; adjacent.add((nr,nc)) if is_on_board(nr,nc) and board[nr][nc]==EMPTY else None
    for r_a,c_a in adjacent: valid,_=rules.is_legal_move(r_a,c_a,ai_player, move_count, board); candidates.append((r_a,c_a)) if valid else None

    if candidates: move=random.choice(candidates); print(f"AI ({ai_player}) chose adjacent {move}..."); return move, False
    else:
        all_valid = [m for m in empty if rules.is_legal_move(m[0], m[1], ai_player, move_count, board)[0]]
        if all_valid: move=random.choice(all_valid); print(f"AI ({ai_player}) chose random {move}..."); return move, False
        else: print(f"AI ({ai_player}) no valid moves!"); return None, False

    print(f"Error: AI ({ai_player}) failed to determine move."); return None, False


# --- AI Learning Logic ---
def learn_from_ai_loss(final_move_log, current_player_types):
    """當 AI 輸掉遊戲時，更新開局庫以避免重複同樣的失敗序列。"""
    print("--- Entering AI learn_from_loss ---")
    # global OPENING_BOOK # 不需要 global，直接修改導入的 OPENING_BOOK
    if not final_move_log or len(final_move_log) < 2: print("Learn: Log too short."); return

    winner=final_move_log[-1].get('player'); loser=WHITE if winner==BLACK else BLACK
    if current_player_types.get(loser)!="ai": print(f"Learn: Loser {loser} not AI."); return

    ai_last_idx = -1; # ... (找到 ai_last_idx 的邏輯不變) ...
    for i in range(len(final_move_log)-2, -1, -1):
         if final_move_log[i].get('player') == loser: ai_last_idx=i; break
    if ai_last_idx == -1: print(f"Learn: AI {loser} move not found before loss."); return

    ai_losing_data=final_move_log[ai_last_idx]; losing_move=tuple(ai_losing_data[k] for k in ['row','col'])
    seq_before=final_move_log[:ai_last_idx]; key_seq=tuple(tuple(m[k] for k in ['row','col']) for m in seq_before)
    print(f"Learn: AI {loser} lost. Last AI move {losing_move} at index {ai_last_idx}"); print(f"Learn: Sequence key {key_seq}")

    # Reconstruct board state
    print("Learn: Reconstructing board state...")
    temp_board = [[EMPTY for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]; ok = True; current_move_count = 0
    for i,m in enumerate(seq_before):
        r,c,p=m.get('row',-1),m.get('col',-1),m.get('player',0)
        if is_on_board(r, c) and temp_board[r][c] == EMPTY: temp_board[r][c] = p; current_move_count += 1
        else: print(f"Learn Err: Recon failed {i+1}"); ok = False; break
    if not ok: print("--- Exit learn (Recon fail) ---"); return
    print("Learn: Board reconstructed.")

    # Find alternatives (使用 rules.is_legal_move)
    print(f"Learn: Finding valid moves for player {loser} (move_count={current_move_count})...")
    valid_moves=[]
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if temp_board[r][c]==EMPTY:
                is_valid, _ = rules.is_legal_move(r, c, loser, current_move_count, temp_board)
                if is_valid: valid_moves.append((r,c))

    print(f"Learn: Found {len(valid_moves)} valid moves then: {valid_moves}")
    alternatives=[m for m in valid_moves if m!=losing_move]
    print(f"Learn: Losing move {losing_move}. Found {len(alternatives)} alternatives: {alternatives}")

    # Update book (使用導入的 OPENING_BOOK)
    book_entry = OPENING_BOOK.get(key_seq)
    updated = False
    if isinstance(book_entry, list):
         if losing_move in book_entry:
             book_entry.remove(losing_move); print(f"Learn: Removed {losing_move} from book list for {key_seq}.")
             if not book_entry: del OPENING_BOOK[key_seq]; print(f"Learn: Removed key {key_seq} as list empty.")
             updated = True
         else: print(f"Learn: Losing move {losing_move} not in book list {book_entry}. No update.")
    elif book_entry == losing_move: # Handle potential old format
         if alternatives: new_move = random.choice(alternatives); OPENING_BOOK[key_seq] = [new_move]; print(f"Learn: Replaced single losing {losing_move} with [{new_move}] for {key_seq}."); updated = True
         else: del OPENING_BOOK[key_seq]; print(f"Learn: Removed single losing {key_seq} no alternatives.") ; updated = True
    elif book_entry is None and alternatives: # Sequence not in book
         new_move = random.choice(alternatives); OPENING_BOOK[key_seq] = [new_move]; print(f"Learn: Added new seq {key_seq} to book with [{new_move}]."); updated = True
    else: print(f"Learn: No update needed/possible. Entry: {book_entry}, Alts: {len(alternatives)}")

    if updated: print("Learn: Saving updated book..."); save_opening_book_to_file(OPENING_BOOK); print("Learn: Save called.")
    else: print("Learn: No changes to opening book.")
    print("--- Exiting learn_from_loss ---")