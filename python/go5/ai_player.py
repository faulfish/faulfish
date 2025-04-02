# -*- coding: utf-8 -*-
import random
from config import (BOARD_SIZE, EMPTY, BLACK, WHITE, DIRECTIONS)
from utils import is_on_board
import rules # 導入 rules 模塊以使用 is_legal_move 等
# --- 從 game_io 導入 OPENING_BOOK 和保存函數 ---
from game_io import OPENING_BOOK, save_opening_book_to_file

# --- AI Decision Logic ---

def find_best_ai_move(board, move_log, move_count, current_player):
    """AI 尋找最佳著法，加入開局庫、天元規則和啟發式隨機選擇。"""
    ai_player = current_player
    opponent_player = WHITE if ai_player == BLACK else BLACK
    used_book_flag = False

    try: # Wrap logic for finally block (though it's empty now)
        # Strategy -1: AI Black First Move
        if move_count == 0 and ai_player == BLACK:
            valid,_ = rules.is_legal_move(7, 7, ai_player, move_count, board) # 使用 rules.
            move = (7, 7) if valid else None
            if move: print(f"AI ({ai_player}) mandatory Tengen"); return move, False

        # Strategy 0: Opening Book
        if move_count > 0:
            # global OPENING_BOOK # Not needed
            seq = tuple(tuple(m[k] for k in ['row','col']) for m in move_log)
            if seq in OPENING_BOOK: # Directly use imported OPENING_BOOK
                possible = OPENING_BOOK[seq]; valid_moves = []
                if isinstance(possible, list): valid_moves=[m for m in possible if rules.is_legal_move(m[0],m[1],ai_player, move_count, board)[0]] # Use rules.
                if valid_moves: move=random.choice(valid_moves); print(f"AI ({ai_player}) using book {move} from {len(valid_moves)}"); return move, True
                else: print(f"AI ({ai_player}) book seq found but no valid moves. Fallback.")

        # Strategies 1, 2, 2.25, 2.5, 2.75, 3
        empty = []; occupied = set();
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE): (empty.append((r,c)) if board[r][c]==EMPTY else occupied.add((r,c)))
        if not empty: print(f"AI ({ai_player}) no empty spots."); return None, False

        # --- Helper (Not needed directly) ---
        # def check_temp_move(...)

        # 1. Win
        for r, c in empty:
            valid, _ = rules.is_legal_move(r, c, ai_player, move_count, board)
            if valid:
                board[r][c] = ai_player
                win = rules.check_win_condition_at(r, c, ai_player, board)
                board[r][c] = EMPTY # Revert
                if win:
                    print(f"AI ({ai_player}) found win at ({r},{c})")
                    return (r, c), False # Return immediately

        # 2. Block Win
        for r, c in empty:
            board[r][c] = opponent_player
            opponent_wins = rules.check_win_condition_at(r, c, opponent_player, board)
            board[r][c] = EMPTY # Revert
            if opponent_wins:
                block_ok, _ = rules.is_legal_move(r, c, ai_player, move_count, board)
                if block_ok:
                    print(f"AI ({ai_player}) blocking win at ({r},{c})")
                    return (r, c), False # Return immediately

        # 2.25 Block Threatening Four
        four_blocks = []
        for r, c in empty:
             board[r][c] = opponent_player
             forms_threatening_four = False
             # --- Corrected Loop ---
             lines_info = rules.count_line(r, c, opponent_player, board) # Calculate once
             for count, ends in lines_info.values():
                 if count == 4 and ends >= 1:
                     forms_threatening_four = True
                     break # Exit inner loop once found
             # --- End Corrected Loop ---
             board[r][c] = EMPTY
             if forms_threatening_four:
                  can_block_here, _ = rules.is_legal_move(r, c, ai_player, move_count, board)
                  if can_block_here: four_blocks.append((r, c))
        if four_blocks:
             move = random.choice(four_blocks)
             print(f"AI ({ai_player}) blocking four at {move}")
             return move, False

        # 2.5 Block Open Three
        three_blocks = []
        for r, c in empty:
             board[r][c] = opponent_player
             forms_open_three = False
             # --- Corrected Loop ---
             for dr_dc in DIRECTIONS:
                 is_three, is_open = rules.check_specific_line_at(r, c, opponent_player, board, dr_dc, 3)
                 if is_open:
                     # Check count explicitly here as check_specific_line only checks pattern
                     lines_info_temp = rules.count_line(r, c, opponent_player, board)
                     count_overall, _ = lines_info_temp[dr_dc]
                     if count_overall == 3:
                         forms_open_three = True
                         break
             # --- End Corrected Loop ---
             board[r][c] = EMPTY
             if forms_open_three:
                  can_block_here, _ = rules.is_legal_move(r, c, ai_player, move_count, board)
                  if can_block_here: three_blocks.append((r, c))
        if three_blocks:
             move = random.choice(three_blocks)
             print(f"AI ({ai_player}) blocking open three at {move}")
             return move, False

        # --- Strategy 2.75: Block Opponent's "Sleeping Three to Four" Threat ---
        # print("Debug: Checking for opponent's sleeping three to four...") # Debug Optional
        sleeping_three_blocks = []
        for r, c in empty:
             can_ai_block_here, _ = rules.is_legal_move(r, c, ai_player, move_count, board)
             if not can_ai_block_here: continue

             board[r][c] = opponent_player # Simulate opponent move
             creates_sleeping_threat = False
             lines_info = rules.count_line(r, c, opponent_player, board)
             for count, open_ends in lines_info.values():
                  if count == 3 and open_ends == 1: # Check for sleeping three pattern
                      creates_sleeping_threat = True
                      break
             board[r][c] = EMPTY # Revert simulation

             if creates_sleeping_threat: sleeping_three_blocks.append((r,c))

        if sleeping_three_blocks:
             block_choice = random.choice(sleeping_three_blocks)
             print(f"AI ({ai_player}) blocking sleeping three threat at {block_choice}")
             return block_choice, False
        # --- End Strategy 2.75 ---


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

        print(f"Error: AI ({ai_player}) failed to determine move after all checks."); return None, False

    finally:
        # No need to manage ai_thinking flag here
        pass


# --- AI Learning Logic ---
def learn_from_ai_loss(final_move_log, current_player_types):
    print("--- Entering AI learn_from_loss ---")
    # global OPENING_BOOK # No need
    if not final_move_log or len(final_move_log)<2: print("Learn: Log too short."); return

    winner=final_move_log[-1].get('player'); loser=WHITE if winner==BLACK else BLACK
    if current_player_types.get(loser)!="ai": print(f"Learn: Loser {loser} not AI."); return

    ai_last_idx = -1;
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
        # --- Corrected Recon Loop ---
        if is_on_board(r, c) and temp_board[r][c] == EMPTY:
            temp_board[r][c] = p
            current_move_count += 1
        else:
            print(f"Learn Err: Recon failed at step {i+1} ({r},{c}). Invalid coord or overwrite.")
            ok = False
            break
        # --- End Corrected Recon Loop ---
    if not ok: print("--- Exit learn (Recon fail) ---"); return
    print("Learn: Board reconstructed.")

    # Find alternatives
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

    # Update book
    book_entry = OPENING_BOOK.get(key_seq)
    updated = False
    if isinstance(book_entry, list):
         if losing_move in book_entry:
             book_entry.remove(losing_move); print(f"Learn: Removed {losing_move} from book list for {key_seq}.")
             if not book_entry: del OPENING_BOOK[key_seq]; print(f"Learn: Removed key {key_seq} as list empty.")
             updated = True
         else: print(f"Learn: Losing move {losing_move} not in book list {book_entry}. No update.")
    elif book_entry == losing_move:
         if alternatives: new_move=random.choice(alternatives); OPENING_BOOK[key_seq]=[new_move]; print(f"Learn: Replaced single losing {losing_move} with [{new_move}] for {key_seq}."); updated = True
         else: del OPENING_BOOK[key_seq]; print(f"Learn: Removed single losing {key_seq} no alternatives.") ; updated = True
    elif book_entry is None and alternatives:
         new_move=random.choice(alternatives); OPENING_BOOK[key_seq]=[new_move]; print(f"Learn: Added new seq {key_seq} to book with [{new_move}]."); updated = True
    else: print(f"Learn: No update needed/possible. Entry: {book_entry}, Alts: {len(alternatives)}")

    if updated: print("Learn: Saving updated book..."); save_opening_book_to_file(OPENING_BOOK); print("Learn: Save called.")
    else: print("Learn: No changes to opening book.")
    print("--- Exiting learn_from_loss ---")