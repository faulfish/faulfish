# -*- coding: utf-8 -*-
import time
import json
import os
from config import (GameState, BOARD_SIZE, EMPTY, BLACK, WHITE, EDGE,
                    DIRECTIONS, DEFAULT_TIME_LIMIT)
from utils import is_on_board

class RenjuGame:
    """Handles the core logic, state, and rules of the Renju game."""
    def __init__(self):
        self.board = [[EMPTY for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
        self.current_player = BLACK
        self.game_state = GameState.PLAYING
        self.last_move = None # Stores (row, col) of the last move
        self.move_count = 0
        self.status_message = "黑方回合" # Message displayed to the user
        self.move_log = [] # List to store move history for saving/analysis
        self.timers = {BLACK: DEFAULT_TIME_LIMIT, WHITE: DEFAULT_TIME_LIMIT}
        self.last_update_time = time.time() # For timer calculations
        self.current_move_start_time = self.last_update_time
        self.pause_start_time = None # Timestamp when pause began
        self.accumulated_pause_time = 0.0 # Total time paused during current move

        # Analysis mode specific
        self.analysis_step = -1 # Index of the move being viewed in analysis (-1 is initial state)
        self.analysis_board = [[EMPTY for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)] # Board state for analysis view

    def restart_game(self):
        """Resets the game to its initial state."""
        self.__init__() # Re-initialize the object

    def pause_game(self):
        """Pauses the game if it's currently playing."""
        if self.game_state == GameState.PLAYING:
            self.game_state = GameState.PAUSED
            self.pause_start_time = time.time()
            # Update timer for the time elapsed *before* pausing
            elapsed_since_last_update = self.pause_start_time - self.last_update_time
            self.timers[self.current_player] = max(0, self.timers[self.current_player] - elapsed_since_last_update)
            self.status_message = "遊戲暫停 (按鈕恢復)"
            print("Game Paused")

    def resume_game(self):
        """Resumes the game if it's paused."""
        if self.game_state == GameState.PAUSED and self.pause_start_time is not None:
            pause_duration = time.time() - self.pause_start_time
            self.accumulated_pause_time += pause_duration # Track pause time for the *current* move log
            self.last_update_time = time.time() # Reset timer update reference point
            self.game_state = GameState.PLAYING
            self.pause_start_time = None
            player_name = "黑方" if self.current_player == BLACK else "白方"
            self.status_message = f"{player_name} 回合"
            print(f"Game Resumed (Paused for {pause_duration:.1f}s)")
        elif self.game_state == GameState.PAUSED:
            # Handle case where resume is called without a valid pause start time (less likely)
            self.game_state = GameState.PLAYING
            self.last_update_time = time.time()
            print("Warning: Resuming game potentially from an inconsistent pause state.")

    def update_timers(self):
        """Updates player timers if the game is playing."""
        if self.game_state != GameState.PLAYING:
            return
        now = time.time()
        elapsed = now - self.last_update_time
        self.last_update_time = now
        self.timers[self.current_player] = max(0, self.timers[self.current_player] - elapsed)

        if self.timers[self.current_player] <= 0:
            loser = self.current_player
            winner = WHITE if loser == BLACK else BLACK
            self.game_state = GameState.BLACK_WINS if winner == BLACK else GameState.WHITE_WINS
            winner_name = "黑方" if winner == BLACK else "白方"
            self.status_message = f"超時! {winner_name} 勝!"
            print("Timeout!")

    def make_move(self, r, c):
        """Attempts to place a stone for the current player at (r, c)."""
        if self.game_state != GameState.PLAYING:
            self.status_message = "遊戲已結束或暫停"
            return False # Cannot make move if game is not active

        if not is_on_board(r, c) or self.board[r][c] != EMPTY:
            self.status_message = "無效位置!"
            return False # Invalid move position

        player = self.current_player

        # --- Renju Rule: Check for Forbidden Moves (Black Only) ---
        if player == BLACK:
            # Temporarily place the stone to check rules
            self.board[r][c] = player
            is_win_move = self.check_win_condition(r, c, player)
            forbidden_reason = None
            if not is_win_move: # Only check forbidden if it's not a winning move
                forbidden_reason = self.check_forbidden_move(r, c)
            # Remove the temporary stone
            self.board[r][c] = EMPTY

            if forbidden_reason:
                self.status_message = f"禁手: {forbidden_reason}! 請選他處."
                print(f"Forbidden move attempt by Black: {forbidden_reason} at ({r},{c})")
                return False # Move is forbidden

        # --- Place the Stone Permanently ---
        self.board[r][c] = player
        self.last_move = (r, c)
        self.move_count += 1

        # --- Log the Move ---
        thinking_time = time.time() - self.current_move_start_time
        self.move_log.append({
            "player": player,
            "row": r,
            "col": c,
            "time": round(thinking_time, 1), # Time spent on this move
            "pause": round(self.accumulated_pause_time, 1) # Pause time during this move
        })
        self.accumulated_pause_time = 0.0 # Reset accumulated pause for the next move

        # --- Check for Win Condition ---
        if self.check_win_condition(r, c, player):
            self.game_state = GameState.BLACK_WINS if player == BLACK else GameState.WHITE_WINS
            winner = "黑方" if player == BLACK else "白方"
            self.status_message = f"{winner} 連珠五子勝!"
            print(f"Win condition met for {winner} at ({r},{c})")
            return True

        # --- Check for Draw Condition ---
        if self.move_count == BOARD_SIZE * BOARD_SIZE:
            self.game_state = GameState.DRAW
            self.status_message = "平局!"
            print("Draw game: Board is full.")
            return True

        # --- Switch Player ---
        self.switch_player()
        return True

    def switch_player(self):
        """Switches the current player and updates status."""
        self.current_player = WHITE if self.current_player == BLACK else BLACK
        player_name = "黑方" if self.current_player == BLACK else "白方"
        self.status_message = f"{player_name} 回合"
        # Reset timers for the next player's turn
        now = time.time()
        self.last_update_time = now
        self.current_move_start_time = now

    def count_line(self, r, c, player, dr_dc):
        """Counts consecutive stones for 'player' starting from (r, c) along direction dr_dc."""
        dr, dc = dr_dc
        count = 1 # Start with the stone at (r, c) itself
        open_ends = 0

        # Count forward
        cr, cc = r + dr, c + dc
        while is_on_board(cr, cc) and self.board[cr][cc] == player:
            count += 1
            cr += dr
            cc += dc
        # Check if the line is open at the forward end
        if is_on_board(cr, cc) and self.board[cr][cc] == EMPTY:
            open_ends += 1

        # Count backward
        cr, cc = r - dr, c - dc
        while is_on_board(cr, cc) and self.board[cr][cc] == player:
            count += 1
            cr -= dr
            cc -= dc
        # Check if the line is open at the backward end
        if is_on_board(cr, cc) and self.board[cr][cc] == EMPTY:
            open_ends += 1

        return count, open_ends

    def check_win_condition(self, r, c, player):
        """Checks if placing a stone at (r, c) results in a win for 'player'."""
        for dr_dc in DIRECTIONS:
            count, _ = self.count_line(r, c, player, dr_dc)
            if player == BLACK and count == 5: # Black wins with exactly 5
                return True
            if player == WHITE and count >= 5: # White wins with 5 or more (no overline rule)
                return True
        return False

    def check_forbidden_move(self, r, c):
        """Checks if placing a BLACK stone at (r, c) is a forbidden move (3-3, 4-4, overline).
           Assumes the black stone has ALREADY BEEN TEMPORARILY PLACED for the check."""
        player = BLACK # Only Black has forbidden moves

        # 1. Check for Overline (長連 - Six or more stones in a row)
        for dr_dc in DIRECTIONS:
            count, _ = self.count_line(r, c, player, dr_dc)
            if count >= 6:
                return "長連" # Overline is forbidden

        # 2. Check for Double Three (三三) and Double Four (四四)
        open_threes_count = 0
        fours_count = 0

        for dr_dc in DIRECTIONS:
            # Important: Use the specialized check that correctly identifies open threes
            is_four, _ = self.check_specific_line(r, c, player, dr_dc, 4)
            if is_four:
                 # Check if this four is actually part of an overline (which is handled above)
                 count_overall, _ = self.count_line(r,c, player, dr_dc)
                 if count_overall < 6: # Only count as a 'four' if it's not part of an overline
                    fours_count += 1


            # Check for open threes only if it doesn't also form a four or more in that line
            # (A common point can be part of a three and a four simultaneously,
            # but we prioritize checking 4-4 and overlines)
            # Re-check the line length to avoid counting threes within longer lines inappropriately
            # The check_specific_line handles the 'open' part correctly.
            is_three, is_open_three = self.check_specific_line(r, c, player, dr_dc, 3)
            if is_open_three:
                # Check if making this three *also* makes a five (winning move)
                # or an overline (handled above). An open three that wins is not forbidden.
                 count_overall, _ = self.count_line(r,c, player, dr_dc)
                 if count_overall < 5: # If it doesn't form 5 or more, count it as an open three
                    open_threes_count += 1


        if fours_count >= 2:
            return "四四" # Double four is forbidden
        if open_threes_count >= 2:
             # Make sure this 3-3 isn't also a 4-4 (4-4 takes precedence)
             # This check might be implicitly handled by counting fours first, but let's be explicit
             if fours_count < 2:
                return "三三" # Double three is forbidden (if not also 4-4)


        return None # No forbidden move detected


    def check_specific_line(self, r, c, player, dr_dc, target_count):
        """
        Helper for forbidden checks (3-3, 4-4). Checks if placing a stone at (r, c)
        creates a line of EXACTLY target_count stones along the given direction (dr_dc).
        For target_count=3, it also checks if it's an "open three".
        Assumes the stone at (r,c) is already placed on the board for the check.
        Returns: (bool: found_line_of_target_count, bool: is_open_three)
                 is_open_three is only relevant if target_count is 3.
        """
        dr, dc = dr_dc
        line = [] # Stores sequence of stones/empty/edge along the axis through (r,c)
        new_stone_index = -1 # Will store the index of the newly placed stone (r,c) in 'line'

        # Scan backward from (r,c)
        for i in range(target_count + 1, 0, -1): # Scan enough steps backward
            cr, cc = r - i * dr, c - i * dc
            if is_on_board(cr, cc):
                line.append(self.board[cr][cc])
            else:
                line.append(EDGE) # Mark board edge

        # Add the newly placed stone itself
        line.append(player)
        new_stone_index = len(line) - 1

        # Scan forward from (r,c)
        for i in range(1, target_count + 2): # Scan enough steps forward
            cr, cc = r + i * dr, c + i * dc
            if is_on_board(cr, cc):
                line.append(self.board[cr][cc])
            else:
                line.append(EDGE) # Mark board edge

        # --- Analysis of the collected line sequence ---
        found_target_count_line = False
        is_specifically_open_three = False # Only set if target_count == 3 and it's open

        # Iterate through all possible sub-sequences of target_count length
        for i in range(len(line) - target_count + 1):
            sub_seq = line[i : i + target_count]

            # Check if this sub-sequence consists only of the player's stones
            if all(s == player for s in sub_seq):
                 # Ensure the newly placed stone (r,c) is part of this specific sequence
                if i <= new_stone_index < i + target_count:

                    # Now check the ends for emptiness or blockage
                    left_end = line[i - 1] if i > 0 else EDGE
                    right_end = line[i + target_count] if (i + target_count) < len(line) else EDGE

                    # --- Check for Overline ---
                    # An overline is NOT a "four" or a "three" for forbidden purposes.
                    # If the sequence continues with the player's stone on either side, it's part of a longer line.
                    is_part_of_longer = (left_end == player or right_end == player)

                    if not is_part_of_longer:
                        found_target_count_line = True # Found a line of *exactly* target_count

                        # --- Specific check for OPEN THREE ---
                        if target_count == 3:
                             # An open three requires EMPTY spaces on BOTH ends: _OOO_
                            if left_end == EMPTY and right_end == EMPTY:
                                is_specifically_open_three = True
                                # Found one open three in this direction, no need to check other 3-stone sequences in this same line
                                break

        # For non-three checks (like four), we just need found_target_count_line
        # For three checks, we need both found_target_count_line AND is_specifically_open_three
        if target_count == 3:
            return found_target_count_line, is_specifically_open_three
        else: # For target_count == 4 (or others if needed)
            return found_target_count_line, False # Second value is irrelevant


    def save_game(self, filename="renju_save.json"):
        """Saves the current move log to a JSON file."""
        save_data = {"move_log": self.move_log}
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, indent=2, ensure_ascii=False)
            self.status_message = f"棋譜已存檔至 {filename}"
            print(f"Game saved successfully to {filename}")
        except IOError as e:
            self.status_message = "存檔失敗!"
            print(f"Error saving game to {filename}: {e}")
        except Exception as e:
            self.status_message = "存檔時發生錯誤!"
            print(f"An unexpected error occurred during saving: {e}")

    def load_game(self, filename="renju_save.json"):
        """Loads a move log from a JSON file and enters analysis mode."""
        try:
            if not os.path.exists(filename):
                self.status_message = f"找不到檔案: {filename}"
                print(f"Load failed: File not found at {filename}")
                return False

            with open(filename, 'r', encoding='utf-8') as f:
                save_data = json.load(f)

            # Reset game state before loading
            self.restart_game()

            self.move_log = save_data.get("move_log", [])

            if not self.move_log:
                 self.status_message = "載入空棋譜"
                 print("Loaded an empty move log.")
                 # Remain in initial state, maybe switch to ANALYSIS? Or keep PLAYING? Let's go ANALYSIS.
                 self.game_state = GameState.ANALYSIS
                 self.analysis_step = -1
                 self._reconstruct_board_to_step(self.analysis_step) # Ensure analysis board is empty
            else:
                self.status_message = "棋譜載入 - 分析模式"
                self.game_state = GameState.ANALYSIS
                self.analysis_step = -1 # Start viewing from the beginning
                self._reconstruct_board_to_step(self.analysis_step) # Reconstruct to initial state
                print(f"Game loaded successfully from {filename}. Entering Analysis mode.")

            return True

        except json.JSONDecodeError as e:
            self.restart_game() # Reset on error
            self.status_message = "載入失敗: 檔案格式錯誤!"
            print(f"Error loading game from {filename}: Invalid JSON format. {e}")
            return False
        except IOError as e:
            self.restart_game() # Reset on error
            self.status_message = "載入失敗: 無法讀取檔案!"
            print(f"Error loading game from {filename}: {e}")
            return False
        except Exception as e:
            self.restart_game() # Reset on error
            self.status_message = "載入時發生未知錯誤!"
            print(f"An unexpected error occurred during loading: {e}")
            return False

    def analysis_navigate(self, direction):
        """Navigates through moves in analysis mode."""
        if self.game_state != GameState.ANALYSIS or not self.move_log:
            return # Only works in analysis mode with a loaded log

        target_step = self.analysis_step
        total_moves = len(self.move_log)

        if direction == 'next':
            target_step = min(self.analysis_step + 1, total_moves - 1)
        elif direction == 'prev':
            target_step = max(self.analysis_step - 1, -1) # -1 represents the initial empty board state
        elif direction == 'first':
            target_step = -1
        elif direction == 'last':
            target_step = total_moves - 1

        if target_step != self.analysis_step:
            self.analysis_step = target_step
            self._reconstruct_board_to_step(self.analysis_step)
            if self.analysis_step == -1:
                 self.status_message = "分析: 初始局面"
            else:
                 move_num = self.analysis_step + 1
                 player = self.move_log[self.analysis_step].get('player', '?')
                 p_name = "黑" if player == BLACK else "白" if player == WHITE else "?"
                 self.status_message = f"分析: 第 {move_num} 手 ({p_name})"


    def _reconstruct_board_to_step(self, target_move_index):
        """Internal helper to set the analysis_board state up to a specific move index."""
        # Reset the analysis board to empty
        self.analysis_board = [[EMPTY for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
        self.last_move = None # Reset last move indicator for analysis board

        # Replay moves up to the target index
        for i in range(target_move_index + 1):
            if i < len(self.move_log):
                move_data = self.move_log[i]
                try:
                    r, c = move_data['row'], move_data['col']
                    player = move_data['player']
                except KeyError:
                    print(f"Warning: Corrupted move data at step {i+1}. Stopping reconstruction.")
                    break # Stop if data is bad

                if is_on_board(r, c) and self.analysis_board[r][c] == EMPTY:
                    self.analysis_board[r][c] = player
                    if i == target_move_index:
                        self.last_move = (r, c) # Set last move for highlighting
                else:
                     # This case should ideally not happen with valid logs, but good to check
                    print(f"Warning: Invalid move found in log at step {i+1} ({r},{c}). Stopping reconstruction.")
                    # Reset last move if the final step was invalid
                    if i == target_move_index: self.last_move = None
                    break