import pygame
import sys
import time
import json
import os
from collections import defaultdict

# --- Constants ---
# Board dimensions
BOARD_WIDTH = 9
BOARD_HEIGHT = 10

# Screen dimensions (adjust as needed)
SQUARE_SIZE = 60
INFO_PANEL_HEIGHT = 100
ANALYSIS_PANEL_HEIGHT = 50
SCREEN_WIDTH = BOARD_WIDTH * SQUARE_SIZE
SCREEN_HEIGHT = BOARD_HEIGHT * SQUARE_SIZE + INFO_PANEL_HEIGHT + ANALYSIS_PANEL_HEIGHT

# Colors
BOARD_COLOR_LIGHT = (235, 209, 166)
BOARD_COLOR_DARK = (209, 173, 128)
LINE_COLOR = (0, 0, 0)
HIGHLIGHT_COLOR = (100, 255, 100, 150) # Semi-transparent green for valid moves
SELECTED_COLOR = (255, 255, 0, 150) # Semi-transparent yellow for selected piece circle
RED_COLOR = (200, 0, 0)  # Piece text/border color
BLACK_COLOR = (0, 0, 0) # Piece text/border color
INFO_BG_COLOR = (200, 200, 200)
BUTTON_COLOR = (100, 100, 255)
BUTTON_TEXT_COLOR = (255, 255, 255)
PIECE_BG_COLOR = (240, 217, 181) # Background color for the piece circle
PIECE_BORDER_WIDTH = 2 # Border width for the piece circle

# Piece Representation (Internal)
# Red: K, A, E, H, R, C, P (uppercase)
# Black: k, a, e, h, r, c, p (lowercase)
EMPTY = None

# Initial Board Setup (FEN-like, row by row from top)
INITIAL_BOARD_SETUP = [
    ['r', 'h', 'e', 'a', 'k', 'a', 'e', 'h', 'r'],
    [EMPTY] * 9,
    [EMPTY, 'c', EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, 'c', EMPTY],
    ['p', EMPTY, 'p', EMPTY, 'p', EMPTY, 'p', EMPTY, 'p'],
    [EMPTY] * 9,
    # --- River ---
    [EMPTY] * 9,
    ['P', EMPTY, 'P', EMPTY, 'P', EMPTY, 'P', EMPTY, 'P'],
    [EMPTY, 'C', EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, 'C', EMPTY],
    [EMPTY] * 9,
    ['R', 'H', 'E', 'A', 'K', 'A', 'E', 'H', 'R']
]

# Piece Character Mapping (Chinese)
PIECE_CHARS = {
    'K': '帥', 'A': '仕', 'E': '相', 'H': '傌', 'R': '俥', 'C': '炮', 'P': '兵', # Red
    'k': '將', 'a': '士', 'e': '象', 'h': '馬', 'r': '車', 'c': '砲', 'p': '卒'  # Black
}

# Game States
STATE_PLAYING = 'playing'
STATE_CHECKMATE = 'checkmate'
STATE_STALEMATE = 'stalemate'
STATE_ANALYSIS = 'analysis'

# Default Game Time (seconds) - e.g., 15 minutes
DEFAULT_TIME = 15 * 60

# --- Font Path ---
# IMPORTANT: Assumes 'Noto Sans SC' folder is in the same directory as the script
FONT_FILE_PATH = os.path.join("Noto Sans SC", "NotoSansSC-VariableFont_wght.ttf")
# Fallback system fonts if the specific file fails
FALLBACK_FONTS = ["SimHei", "Microsoft YaHei", "KaiTi", "Heiti SC", "PingFang SC", "Arial Unicode MS", None]


# --- Helper Functions ---
def get_piece_color(piece):
    """Returns 'red', 'black', or None."""
    if piece is None:
        return None
    return 'red' if piece.isupper() else 'black'

def is_valid_coord(r, c):
    """Checks if coordinates are within board bounds."""
    return 0 <= r < BOARD_HEIGHT and 0 <= c < BOARD_WIDTH

def get_king_pos(board, color):
    """Finds the position of the king for a given color."""
    king_char = 'K' if color == 'red' else 'k'
    for r in range(BOARD_HEIGHT):
        for c in range(BOARD_WIDTH):
            if board[r][c] == king_char:
                return (r, c)
    return None # Should not happen in a valid game

def is_in_palace(r, c):
    """Checks if coordinates are within either palace."""
    if not (3 <= c <= 5):
        return False
    # Row check: 0-2 for Black, 7-9 for Red
    return (0 <= r <= 2) or (7 <= r <= 9)

def get_palace_limits(color):
    """Returns the row limits (min_r, max_r) for the palace."""
    return (7, 9) if color == 'red' else (0, 2)

def is_across_river(r, color):
    """Checks if a row is across the river for the given color."""
    if color == 'red':
        return r <= 4
    else: # black
        return r >= 5

def load_font(font_path, size, fallback_list):
    """Loads a specific font file, falling back to system fonts."""
    try:
        font = pygame.font.Font(font_path, size)
        print(f"成功載入字體: {font_path}")
        return font
    except pygame.error as e:
        print(f"警告: 無法載入指定字體 '{font_path}': {e}")
        font = pygame.font.SysFont(fallback_list, size)
        if font:
            print(f"使用系統備選字體: {font.get_name()}")
            return font
        else:
            print(f"錯誤: 找不到任何合適的字體 (包括備選: {fallback_list})。")
            return None # Indicate failure
    except Exception as e:
        print(f"載入字體時發生未預期錯誤: {e}")
        return None


# --- Game Logic Class ---
class XiangqiGame:
    def __init__(self):
        self.board = [row[:] for row in INITIAL_BOARD_SETUP] # Deep copy
        self.current_player = 'red'
        self.selected_piece_pos = None
        self.valid_moves = []
        self.move_log = [] # Stores dicts: {"start":..., "end":..., ...}
        self.game_state = STATE_PLAYING
        self.status_message = "紅方回合 (Red's Turn)"

        # Timing
        self.timers = {'red': DEFAULT_TIME, 'black': DEFAULT_TIME}
        self.last_move_time = time.time()
        self.current_move_start_time = time.time()

        # Analysis Mode
        self.analysis_board_state = None # Stores the board being viewed in analysis
        self.analysis_current_step = -1 # Index in move_log

    def switch_player(self):
        self.current_player = 'black' if self.current_player == 'red' else 'red'
        player_name = "紅方 (Red)" if self.current_player == 'red' else "黑方 (Black)"
        self.status_message = f"{player_name} 回合"
        self.current_move_start_time = time.time() # Reset timer start for the new player

    def select_piece(self, r, c):
        """Handles piece selection."""
        if self.game_state != STATE_PLAYING:
            return False

        piece = self.board[r][c]
        if piece is not None and get_piece_color(piece) == self.current_player:
            self.selected_piece_pos = (r, c)
            # Generate valid moves only if the move doesn't expose the king directly
            self.valid_moves = self.get_valid_moves_for_piece(r, c)
            return True
        else:
             self.selected_piece_pos = None
             self.valid_moves = []
             return False

    def make_move(self, r_end, c_end):
        """Attempts to make a move to the target square."""
        if not self.selected_piece_pos or (r_end, c_end) not in self.valid_moves:
            self.selected_piece_pos = None # Deselect if clicking invalid spot
            self.valid_moves = []
            return False

        r_start, c_start = self.selected_piece_pos
        piece = self.board[r_start][c_start]
        captured_piece = self.board[r_end][c_end]

        # Record time taken for the move
        time_taken = time.time() - self.current_move_start_time

        # --- Create Notation (Using Chinese Characters) ---
        notation = f"{PIECE_CHARS.get(piece, '?')}({r_start},{c_start})-({r_end},{c_end})"
        if captured_piece:
             notation += f"x{PIECE_CHARS.get(captured_piece, '?')}"

        # --- Log the move ---
        self.move_log.append({
            "start": (r_start, c_start),
            "end": (r_end, c_end),
            "piece": piece,
            "captured": captured_piece,
            "notation": notation,
            "time": round(time_taken, 2),
            "player": self.current_player
        })

        # --- Update Board ---
        self.board[r_end][c_end] = piece
        self.board[r_start][c_start] = EMPTY

        # --- Post-Move Updates ---
        self.selected_piece_pos = None
        self.valid_moves = []
        self.last_move_time = time.time()

        # --- Check Game Over Conditions ---
        opponent_color = 'black' if self.current_player == 'red' else 'red'
        # opponent_name = "黑方 (Black)" if opponent_color == 'black' else "紅方 (Red)"
        winner_name = "紅方 (Red)" if self.current_player == 'red' else "黑方 (Black)"

        if self.is_checkmate(opponent_color):
            self.game_state = STATE_CHECKMATE
            self.status_message = f"將死! {winner_name} 勝! (Checkmate!)"
        elif self.is_stalemate(opponent_color):
            self.game_state = STATE_STALEMATE
            self.status_message = "欠行! 和棋! (Stalemate!)"
        else:
            # Switch player only if game is not over
            self.switch_player()
            # Check if the new current player is in check
            if self.is_in_check(self.current_player):
                 player_name = "紅方 (Red)" if self.current_player == 'red' else "黑方 (Black)"
                 self.status_message = f"{player_name} 回合 (將軍!)" # Check!

        return True

    def is_in_check(self, player_color, current_board=None):
        """Checks if the specified player is currently in check on the given board."""
        board_to_check = current_board if current_board else self.board
        king_pos = get_king_pos(board_to_check, player_color)
        if not king_pos: return False # Should not happen

        opponent_color = 'black' if player_color == 'red' else 'red'
        for r in range(BOARD_HEIGHT):
            for c in range(BOARD_WIDTH):
                piece = board_to_check[r][c]
                if piece is not None and get_piece_color(piece) == opponent_color:
                    # Check if any of the opponent's raw moves target the king
                    raw_moves = self._get_raw_valid_moves(r, c, board_to_check)
                    if king_pos in raw_moves:
                        return True
        return False

    def does_move_result_in_check(self, start_pos, end_pos, player_color):
         """Simulates a move and checks if it leaves the player in check."""
         r_start, c_start = start_pos
         r_end, c_end = end_pos
         piece = self.board[r_start][c_start]
         captured = self.board[r_end][c_end]

         # Simulate
         self.board[r_end][c_end] = piece
         self.board[r_start][c_start] = EMPTY

         # Check for self-check
         in_check = self.is_in_check(player_color)

         # Undo simulation
         self.board[r_start][c_start] = piece
         self.board[r_end][c_end] = captured

         return in_check

    def kings_are_exposed(self, current_board=None):
        """Checks if the two kings are facing each other directly without obstruction."""
        board_to_check = current_board if current_board else self.board
        red_k_pos = get_king_pos(board_to_check, 'red')
        black_k_pos = get_king_pos(board_to_check, 'black')

        if not red_k_pos or not black_k_pos:
            return False # One king missing

        r1, c1 = red_k_pos
        r2, c2 = black_k_pos

        if c1 != c2: # Not in the same column
            return False

        # Check for obstructions between them
        for r in range(min(r1, r2) + 1, max(r1, r2)):
            if board_to_check[r][c1] is not None:
                return False # Path is blocked

        return True # Same column and no obstructions


    def get_valid_moves_for_piece(self, r_start, c_start):
        """Gets all valid moves for a piece, considering check and king-facing rules."""
        piece = self.board[r_start][c_start]
        if piece is None:
            return []

        player_color = get_piece_color(piece)
        raw_moves = self._get_raw_valid_moves(r_start, c_start, self.board)
        legal_moves = []

        for r_end, c_end in raw_moves:
            # Simulate the move
            original_piece_at_target = self.board[r_end][c_end]
            self.board[r_end][c_end] = piece
            self.board[r_start][c_start] = EMPTY

            # Check if the move results in self-check OR exposes the kings
            is_self_check = self.is_in_check(player_color)
            is_king_exposed = self.kings_are_exposed()

            # Undo the simulation
            self.board[r_start][c_start] = piece
            self.board[r_end][c_end] = original_piece_at_target

            # Add move only if it's legal (no self-check and no exposed kings)
            if not is_self_check and not is_king_exposed:
                legal_moves.append((r_end, c_end))

        return legal_moves


    def _get_raw_valid_moves(self, r_start, c_start, current_board):
        """Calculates potential moves ignoring check/king-facing (used internally)."""
        moves = []
        piece = current_board[r_start][c_start]
        if piece is None: return []

        color = get_piece_color(piece)
        piece_type = piece.lower()

        def add_move(r, c):
            if is_valid_coord(r, c):
                target_piece = current_board[r][c]
                if target_piece is None:
                    moves.append((r, c))
                    return True # Can continue sliding
                elif get_piece_color(target_piece) != color:
                    moves.append((r, c))
                    return False # Capture, cannot continue sliding
            return False # Off board or blocked by own piece

        # --- King (K/k) ---
        if piece_type == 'k':
            palace_r_min, palace_r_max = get_palace_limits(color)
            for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                r_end, c_end = r_start + dr, c_start + dc
                # Stay within palace 3x3 grid
                if palace_r_min <= r_end <= palace_r_max and 3 <= c_end <= 5:
                    add_move(r_end, c_end)

        # --- Advisor (A/a) ---
        elif piece_type == 'a':
            palace_r_min, palace_r_max = get_palace_limits(color)
            for dr, dc in [(1, 1), (1, -1), (-1, 1), (-1, -1)]:
                r_end, c_end = r_start + dr, c_start + dc
                # Stay within palace 3x3 grid
                if palace_r_min <= r_end <= palace_r_max and 3 <= c_end <= 5:
                    add_move(r_end, c_end)

        # --- Elephant (E/e) ---
        elif piece_type == 'e':
            for dr, dc in [(2, 2), (2, -2), (-2, 2), (-2, -2)]:
                r_end, c_end = r_start + dr, c_start + dc
                # Cannot cross river
                if (color == 'red' and r_end < 5) or \
                   (color == 'black' and r_end > 4):
                    continue
                # Check for blocking piece (Elephant's eye)
                r_block, c_block = r_start + dr // 2, c_start + dc // 2
                if is_valid_coord(r_block, c_block) and current_board[r_block][c_block] is None:
                    add_move(r_end, c_end)

        # --- Horse (H/h) ---
        elif piece_type == 'h':
            # L-shaped moves, check for blocking point first
            for dr, dc, br, bc in [(-2, -1, -1, 0), (-2, 1, -1, 0), # Up
                                   (2, -1, 1, 0), (2, 1, 1, 0),    # Down
                                   (-1, -2, 0, -1), (1, -2, 0, -1), # Left
                                   (-1, 2, 0, 1), (1, 2, 0, 1)]:   # Right
                r_end, c_end = r_start + dr, c_start + dc
                r_block, c_block = r_start + br, c_start + bc # Blocking point
                if is_valid_coord(r_block, c_block) and current_board[r_block][c_block] is None:
                    add_move(r_end, c_end)

        # --- Rook / Chariot (R/r) ---
        elif piece_type == 'r':
            for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]: # Directions
                r_temp, c_temp = r_start, c_start
                while True:
                    r_temp, c_temp = r_temp + dr, c_temp + dc
                    if not add_move(r_temp, c_temp):
                        break # Stop sliding in this direction

        # --- Cannon (C/c) ---
        elif piece_type == 'c':
            for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]: # Directions
                r_temp, c_temp = r_start, c_start
                jumped = False
                while True:
                    r_temp, c_temp = r_temp + dr, c_temp + dc
                    if not is_valid_coord(r_temp, c_temp):
                        break # Off board

                    target_piece = current_board[r_temp][c_temp]

                    if not jumped:
                        if target_piece is None:
                             moves.append((r_temp, c_temp)) # Can move to empty square
                        else:
                             jumped = True # Found the jump platform
                    else: # Have jumped one piece
                        if target_piece is not None:
                            # Must capture to land here
                            if get_piece_color(target_piece) != color:
                                moves.append((r_temp, c_temp))
                            break # Stop after potential capture or hitting own piece
                        # Cannot move to empty square after jump, just continue search? No, cannon stops.
                        # Keep searching along the line for a capture, but don't add empty squares
                        continue # Correction: Cannon can keep going after jump if empty, only stops on 2nd piece

        # --- Pawn (P/p) ---
        elif piece_type == 'p':
            # Forward move
            dr_fwd = -1 if color == 'red' else 1
            r_fwd = r_start + dr_fwd
            add_move(r_fwd, c_start)

            # Sideways move (only after crossing the river)
            if is_across_river(r_start, color):
                add_move(r_start, c_start + 1)
                add_move(r_start, c_start - 1)

        return moves

    def get_all_valid_moves(self, player_color):
        """Gets all possible legal moves for a player."""
        all_moves = []
        for r in range(BOARD_HEIGHT):
            for c in range(BOARD_WIDTH):
                piece = self.board[r][c]
                if piece is not None and get_piece_color(piece) == player_color:
                    valid_piece_moves = self.get_valid_moves_for_piece(r, c) # Uses the check-aware function
                    if valid_piece_moves:
                         all_moves.extend([((r, c), move) for move in valid_piece_moves]) # Store as (start, end) tuples
        return all_moves

    def is_checkmate(self, player_color):
        """Checks if the player is checkmated."""
        return self.is_in_check(player_color) and not self.get_all_valid_moves(player_color)

    def is_stalemate(self, player_color):
        """Checks if the player is stalemated."""
        # In Xiangqi, stalemate (no legal moves, but not in check) is a WIN for the player who delivered the stalemate.
        # However, common online rules treat it as a draw. We'll treat it as a DRAW here for simplicity.
        # If you want the traditional win, change the status message and potentially the game state.
        return not self.is_in_check(player_color) and not self.get_all_valid_moves(player_color)

    def update_timers(self):
        """Updates timers if the game is in playing state."""
        if self.game_state == STATE_PLAYING:
            now = time.time()
            time_elapsed = now - self.last_move_time
            self.last_move_time = now # Update last time check

            player_timer = self.timers[self.current_player]
            player_timer -= time_elapsed
            self.timers[self.current_player] = max(0, player_timer) # Don't go below zero

            if self.timers[self.current_player] <= 0:
                self.game_state = STATE_CHECKMATE # Or a specific timeout state
                opponent = 'black' if self.current_player == 'red' else 'red'
                opponent_name = "黑方 (Black)" if opponent == 'black' else "紅方 (Red)"
                self.status_message = f"時間到! {opponent_name} 勝! (Timeout!)"

    # --- Save/Load/Analysis ---
    def save_game(self, filename="xiangqi_save.json"):
        """Saves the move log to a JSON file."""
        try:
            save_data = {
                "move_log": self.move_log,
                "initial_timers": {'red': DEFAULT_TIME, 'black': DEFAULT_TIME} # Store initial time for context
            }
            with open(filename, 'w', encoding='utf-8') as f: # Ensure UTF-8 for Chinese chars
                json.dump(save_data, f, indent=4, ensure_ascii=False) # ensure_ascii=False is crucial
            print(f"棋譜已儲存至 {filename}")
            self.status_message = f"棋譜已儲存至 {filename}"
        except Exception as e:
            print(f"儲存遊戲錯誤: {e}")
            self.status_message = "儲存遊戲錯誤."

    def load_game(self, filename="xiangqi_save.json"):
        """Loads a move log from JSON and enters analysis mode."""
        try:
            if not os.path.exists(filename):
                 self.status_message = f"找不到檔案: {filename}"
                 print(f"找不到存檔檔案: {filename}")
                 return False

            with open(filename, 'r', encoding='utf-8') as f: # Ensure UTF-8
                save_data = json.load(f)

            # Reset game state for analysis
            self.__init__() # Re-initialize basic state (board, etc.)

            self.move_log = save_data.get("move_log", [])
            # Optional: Restore timers if needed for context, but they don't run in analysis
            # initial_timers = save_data.get("initial_timers", {'red': DEFAULT_TIME, 'black': DEFAULT_TIME})
            # self.timers = initial_timers.copy()

            self.game_state = STATE_ANALYSIS
            self.analysis_current_step = -1 # Start before the first move
            self.analysis_board_state = [row[:] for row in INITIAL_BOARD_SETUP] # Start with initial board
            self.status_message = f"分析模式: 已載入 {len(self.move_log)} 步棋. 使用方向鍵瀏覽."
            print(f"從 {filename} 載入遊戲. 進入分析模式.")
            return True

        except Exception as e:
            print(f"載入遊戲錯誤: {e}")
            self.status_message = "載入遊戲錯誤."
            # Revert to playing state maybe? Or handle error state
            self.__init__() # Reset to a clean state
            return False

    def analysis_navigate(self, direction):
        """Navigates through moves in analysis mode."""
        if self.game_state != STATE_ANALYSIS:
            return

        current_total_moves = len(self.move_log)
        if direction == 'next':
            if self.analysis_current_step < current_total_moves - 1:
                self.analysis_current_step += 1
                self._apply_analysis_move(self.analysis_current_step)
            else: # Already at the last move
                self.analysis_current_step = current_total_moves -1
        elif direction == 'prev':
            if self.analysis_current_step >= 0:
                self.analysis_current_step -= 1
                self._reconstruct_board_to_step(self.analysis_current_step)
            else: # Already at the beginning
                 self.analysis_current_step = -1
        elif direction == 'first':
            self.analysis_current_step = -1
            self._reconstruct_board_to_step(self.analysis_current_step)
        elif direction == 'last':
            self.analysis_current_step = current_total_moves - 1
            self._reconstruct_board_to_step(self.analysis_current_step)

        # Update status after navigation
        self.status_message = self._get_analysis_status()


    def _apply_analysis_move(self, move_index):
        """Applies a single move to the analysis board state. Assumes board is correct state for move_index-1."""
        if 0 <= move_index < len(self.move_log):
            move_data = self.move_log[move_index]
            r_start, c_start = move_data["start"]
            r_end, c_end = move_data["end"]
            piece = move_data["piece"]

            # Apply the move to the analysis board
            if self.analysis_board_state: # Should always exist in analysis mode after load/reconstruct
                 self.analysis_board_state[r_end][c_end] = piece
                 self.analysis_board_state[r_start][c_start] = EMPTY
            # Status is updated in analysis_navigate


    def _reconstruct_board_to_step(self, target_step_index):
        """Rebuilds the analysis board state from the start up to a specific move index."""
        self.analysis_board_state = [row[:] for row in INITIAL_BOARD_SETUP] # Start fresh
        current_internal_step = -1

        for i in range(target_step_index + 1): # Apply moves up to and including target_step_index
            if i < len(self.move_log):
                 move_data = self.move_log[i]
                 r_start, c_start = move_data["start"]
                 r_end, c_end = move_data["end"]
                 piece = move_data["piece"]
                 self.analysis_board_state[r_end][c_end] = piece
                 self.analysis_board_state[r_start][c_start] = EMPTY
                 current_internal_step = i # Keep track of the last applied step index

        self.analysis_current_step = current_internal_step # Set the main step counter
        # Status is updated in analysis_navigate


    def _get_analysis_status(self):
        """Generates the status message for analysis mode."""
        if self.game_state != STATE_ANALYSIS: return ""

        total_moves = len(self.move_log)
        current_move_num = self.analysis_current_step + 1 # 1-based index for display

        if self.analysis_current_step == -1:
            return f"分析: 初始局面 (0/{total_moves})"
        elif 0 <= self.analysis_current_step < total_moves:
            move_data = self.move_log[self.analysis_current_step]
            notation = move_data["notation"]
            time_taken = move_data["time"]
            player = "紅方" if move_data["player"] == 'red' else "黑方"
            return f"分析: 第 {current_move_num}/{total_moves} 步 ({player}): {notation} (思考: {time_taken}s)"
        else:
            # If somehow index is out of bounds, reset to last move view
             self.analysis_current_step = max(-1, min(self.analysis_current_step, total_moves - 1))
             if total_moves > 0 and self.analysis_current_step != -1:
                move_data = self.move_log[self.analysis_current_step]
                notation = move_data["notation"]
                time_taken = move_data["time"]
                player = "紅方" if move_data["player"] == 'red' else "黑方"
                return f"分析: 第 {total_moves}/{total_moves} 步 ({player}): {notation} (思考: {time_taken}s) - 終局"
             elif total_moves == 0:
                  return "分析: 無棋步記錄"
             else: # At initial position
                  return f"分析: 初始局面 (0/{total_moves})"


# --- Drawing Functions ---
def draw_board(screen, font):
    """Draws the Xiangqi board grid, river, and palaces."""
    screen.fill(BOARD_COLOR_LIGHT)

    # Vertical lines
    for c in range(BOARD_WIDTH):
        x = c * SQUARE_SIZE + SQUARE_SIZE // 2
        # Draw full line across river gap for simplicity in grid structure
        pygame.draw.line(screen, LINE_COLOR, (x, SQUARE_SIZE // 2), (x, BOARD_HEIGHT * SQUARE_SIZE - SQUARE_SIZE // 2), 1)
        # Thicken lines bordering the river later if desired

    # Horizontal lines
    for r in range(BOARD_HEIGHT):
        y = r * SQUARE_SIZE + SQUARE_SIZE // 2
        pygame.draw.line(screen, LINE_COLOR, (SQUARE_SIZE // 2, y), (BOARD_WIDTH * SQUARE_SIZE - SQUARE_SIZE // 2, y), 1)

    # River (Clear the lines and draw text)
    river_rect = pygame.Rect(SQUARE_SIZE // 2, 4 * SQUARE_SIZE + SQUARE_SIZE // 2, (BOARD_WIDTH-1) * SQUARE_SIZE, SQUARE_SIZE)
    pygame.draw.rect(screen, BOARD_COLOR_LIGHT, river_rect) # Erase lines in the river area

    if font: # Only draw text if font loaded successfully
        river_font_size = SQUARE_SIZE // 3
        # Use the provided font object, but adjust size
        try:
             river_font = pygame.font.Font(FONT_FILE_PATH, river_font_size)
        except: # Fallback if resizing fails or path issue remains
             river_font = pygame.font.SysFont(FALLBACK_FONTS, river_font_size)

        if river_font:
            text_chu = river_font.render("楚", True, LINE_COLOR)
            text_he = river_font.render("河", True, LINE_COLOR)
            text_han = river_font.render("漢", True, LINE_COLOR)
            text_jie = river_font.render("界", True, LINE_COLOR)
            # Position text centrally in the river gap
            river_y_center = 4.5 * SQUARE_SIZE + SQUARE_SIZE // 2
            screen.blit(text_chu, text_chu.get_rect(center=(2 * SQUARE_SIZE , river_y_center)))
            screen.blit(text_he, text_he.get_rect(center=(3 * SQUARE_SIZE , river_y_center)))
            screen.blit(text_han, text_han.get_rect(center=(6 * SQUARE_SIZE , river_y_center)))
            screen.blit(text_jie, text_jie.get_rect(center=(7 * SQUARE_SIZE , river_y_center)))


    # Palaces (diagonal lines)
    palace_coords = [
        # Top Palace (Black) - Coordinates are intersection points
        ((3 * SQUARE_SIZE + SQUARE_SIZE // 2, SQUARE_SIZE // 2), (5 * SQUARE_SIZE + SQUARE_SIZE // 2, 2 * SQUARE_SIZE + SQUARE_SIZE // 2)),
        ((5 * SQUARE_SIZE + SQUARE_SIZE // 2, SQUARE_SIZE // 2), (3 * SQUARE_SIZE + SQUARE_SIZE // 2, 2 * SQUARE_SIZE + SQUARE_SIZE // 2)),
        # Bottom Palace (Red)
        ((3 * SQUARE_SIZE + SQUARE_SIZE // 2, 7 * SQUARE_SIZE + SQUARE_SIZE // 2), (5 * SQUARE_SIZE + SQUARE_SIZE // 2, 9 * SQUARE_SIZE + SQUARE_SIZE // 2)),
        ((5 * SQUARE_SIZE + SQUARE_SIZE // 2, 7 * SQUARE_SIZE + SQUARE_SIZE // 2), (3 * SQUARE_SIZE + SQUARE_SIZE // 2, 9 * SQUARE_SIZE + SQUARE_SIZE // 2)),
    ]
    for start, end in palace_coords:
        pygame.draw.line(screen, LINE_COLOR, start, end, 1)

    # Add markings for cannon/pawn starting points (optional visual aid)
    pawn_marks = [(0,3), (2,3), (4,3), (6,3), (8,3), (0,6), (2,6), (4,6), (6,6), (8,6)]
    cannon_marks = [(1,2), (7,2), (1,7), (7,7)]
    mark_len = SQUARE_SIZE // 8
    for c, r in pawn_marks + cannon_marks:
         x = c * SQUARE_SIZE + SQUARE_SIZE // 2
         y = r * SQUARE_SIZE + SQUARE_SIZE // 2
         # Draw small L-shaped marks around the intersection
         # Exclude edges of board
         if c > 0: # Left mark
             pygame.draw.line(screen, LINE_COLOR, (x - mark_len*1.5, y - mark_len), (x - mark_len*0.5, y - mark_len), 1)
             pygame.draw.line(screen, LINE_COLOR, (x - mark_len, y - mark_len*1.5), (x - mark_len, y - mark_len*0.5), 1)
         if c < BOARD_WIDTH - 1: # Right mark
             pygame.draw.line(screen, LINE_COLOR, (x + mark_len*0.5, y - mark_len), (x + mark_len*1.5, y - mark_len), 1)
             pygame.draw.line(screen, LINE_COLOR, (x + mark_len, y - mark_len*1.5), (x + mark_len, y - mark_len*0.5), 1)
         if c > 0: # Bottom left
             pygame.draw.line(screen, LINE_COLOR, (x - mark_len*1.5, y + mark_len), (x - mark_len*0.5, y + mark_len), 1)
             pygame.draw.line(screen, LINE_COLOR, (x - mark_len, y + mark_len*0.5), (x - mark_len, y + mark_len*1.5), 1)
         if c < BOARD_WIDTH - 1: # Bottom right
             pygame.draw.line(screen, LINE_COLOR, (x + mark_len*0.5, y + mark_len), (x + mark_len*1.5, y + mark_len), 1)
             pygame.draw.line(screen, LINE_COLOR, (x + mark_len, y + mark_len*0.5), (x + mark_len, y + mark_len*1.5), 1)


def draw_pieces(screen, board, piece_font):
    """Draws the pieces using text rendering."""
    if not piece_font: return # Don't draw if font failed to load

    radius = SQUARE_SIZE // 2 - 4 # Radius of the piece circle

    for r in range(BOARD_HEIGHT):
        for c in range(BOARD_WIDTH):
            piece = board[r][c]
            if piece is not None:
                char = PIECE_CHARS.get(piece, "?") # Get Chinese character
                color = RED_COLOR if get_piece_color(piece) == 'red' else BLACK_COLOR

                # Calculate center position on the intersection
                center_x = c * SQUARE_SIZE + SQUARE_SIZE // 2
                center_y = r * SQUARE_SIZE + SQUARE_SIZE // 2

                # Draw background circle (slightly off-white)
                pygame.draw.circle(screen, PIECE_BG_COLOR, (center_x, center_y), radius)
                # Draw border circle
                pygame.draw.circle(screen, color, (center_x, center_y), radius, PIECE_BORDER_WIDTH)

                # Render text
                text_surf = piece_font.render(char, True, color)
                text_rect = text_surf.get_rect(center=(center_x, center_y))

                # Blit text onto the screen
                screen.blit(text_surf, text_rect)

def draw_highlights(screen, selected_pos, valid_moves):
    """Highlights the selected piece and its valid moves."""
    # Highlight selected piece with a larger circle overlay
    if selected_pos:
        r, c = selected_pos
        center_x = c * SQUARE_SIZE + SQUARE_SIZE // 2
        center_y = r * SQUARE_SIZE + SQUARE_SIZE // 2
        radius = SQUARE_SIZE // 2 # Outer radius for selection highlight
        highlight_surface = pygame.Surface((radius*2, radius*2), pygame.SRCALPHA)
        pygame.draw.circle(highlight_surface, SELECTED_COLOR, (radius, radius), radius)
        screen.blit(highlight_surface, (center_x - radius, center_y - radius))

    # Highlight valid moves with small markers
    marker_size = SQUARE_SIZE // 6 # Size of the small highlight marker
    highlight_surface = pygame.Surface((marker_size, marker_size), pygame.SRCALPHA)
    highlight_surface.fill(HIGHLIGHT_COLOR) # Small semi-transparent square/circle

    for r, c in valid_moves:
        center_x = c * SQUARE_SIZE + SQUARE_SIZE // 2
        center_y = r * SQUARE_SIZE + SQUARE_SIZE // 2
        rect = highlight_surface.get_rect(center=(center_x, center_y))
        screen.blit(highlight_surface, rect)


def draw_info_panel(screen, game, font_small, font_large):
    """Draws timers, current turn, and status messages."""
    panel_rect = pygame.Rect(0, BOARD_HEIGHT * SQUARE_SIZE, SCREEN_WIDTH, INFO_PANEL_HEIGHT)
    pygame.draw.rect(screen, INFO_BG_COLOR, panel_rect)

    if not font_small or not font_large: return None, None # Cant draw text if fonts missing

    # Timers
    red_time = game.timers['red']
    black_time = game.timers['black']
    red_mins, red_secs = divmod(int(red_time), 60)
    black_mins, black_secs = divmod(int(black_time), 60)

    timer_text_red = font_small.render(f"紅方: {red_mins:02d}:{red_secs:02d}", True, RED_COLOR if game.current_player == 'red' or game.game_state != STATE_PLAYING else BLACK_COLOR)
    timer_text_black = font_small.render(f"黑方: {black_mins:02d}:{black_secs:02d}", True, BLACK_COLOR if game.current_player == 'black' or game.game_state != STATE_PLAYING else BLACK_COLOR)

    screen.blit(timer_text_red, (10, panel_rect.top + 10))
    screen.blit(timer_text_black, (panel_rect.width - timer_text_black.get_width() - 10, panel_rect.top + 10)) # Align right

    # Status Message
    status_surf = font_large.render(game.status_message, True, BLACK_COLOR)
    status_rect = status_surf.get_rect(center=(panel_rect.centerx, panel_rect.top + 35)) # Position status centrally
    screen.blit(status_surf, status_rect)

    # Save/Load Buttons (only visible when not in analysis)
    save_button_rect, load_button_rect = None, None # Initialize
    if game.game_state != STATE_ANALYSIS:
        button_font = font_small # Use the small font for buttons
        save_button_rect = pygame.Rect(10, panel_rect.bottom - 40, 80, 30)
        load_button_rect = pygame.Rect(100, panel_rect.bottom - 40, 80, 30)
        pygame.draw.rect(screen, BUTTON_COLOR, save_button_rect, border_radius=5)
        pygame.draw.rect(screen, BUTTON_COLOR, load_button_rect, border_radius=5)
        save_text = button_font.render("儲存", True, BUTTON_TEXT_COLOR)
        load_text = button_font.render("載入", True, BUTTON_TEXT_COLOR)
        screen.blit(save_text, save_text.get_rect(center=save_button_rect.center))
        screen.blit(load_text, load_text.get_rect(center=load_button_rect.center))

    return save_button_rect, load_button_rect

def draw_analysis_panel(screen, game, font):
    """Draws navigation controls for analysis mode."""
    if game.game_state != STATE_ANALYSIS:
        return {} # No buttons needed

    panel_rect = pygame.Rect(0, SCREEN_HEIGHT - ANALYSIS_PANEL_HEIGHT, SCREEN_WIDTH, ANALYSIS_PANEL_HEIGHT)
    pygame.draw.rect(screen, INFO_BG_COLOR, panel_rect)

    if not font: return {} # Can't draw buttons if font missing

    buttons = {}
    button_texts = {"first": "<< 首", "prev": "< 上步", "next": "下步 >", "last": "末 >>"} # Chinese Button Text
    button_width = 75 # Adjust width for longer text
    button_height = 30
    spacing = 10
    total_button_width = len(button_texts) * button_width + (len(button_texts) - 1) * spacing
    start_x = (SCREEN_WIDTH - total_button_width) // 2
    current_x = start_x

    for key, text in button_texts.items():
        rect = pygame.Rect(current_x, panel_rect.centery - button_height // 2, button_width, button_height)
        pygame.draw.rect(screen, BUTTON_COLOR, rect, border_radius=5)
        text_surf = font.render(text, True, BUTTON_TEXT_COLOR)
        text_rect = text_surf.get_rect(center=rect.center)
        screen.blit(text_surf, text_rect)
        buttons[key] = rect
        current_x += button_width + spacing

    return buttons

def get_clicked_square(pos):
    """Converts mouse click coordinates to board row and column (intersection based)."""
    x, y = pos

    # Ignore clicks outside the board + buffer area
    buffer = SQUARE_SIZE * 0.5
    if not (buffer <= x < BOARD_WIDTH * SQUARE_SIZE - buffer / 2 and \
            buffer <= y < BOARD_HEIGHT * SQUARE_SIZE - buffer / 2) :
         # Check if click is within board grid area first (more accurate than panel check)
         if y >= BOARD_HEIGHT * SQUARE_SIZE :
             return None # Clicked in info/analysis panel area

    # Calculate the nearest intersection indices
    col = round((x - SQUARE_SIZE // 2) / SQUARE_SIZE)
    row = round((y - SQUARE_SIZE // 2) / SQUARE_SIZE)

    # Clamp indices to board limits
    col = max(0, min(BOARD_WIDTH - 1, col))
    row = max(0, min(BOARD_HEIGHT - 1, row))

    # Check if the click is close enough to the calculated intersection center
    center_x = col * SQUARE_SIZE + SQUARE_SIZE // 2
    center_y = row * SQUARE_SIZE + SQUARE_SIZE // 2
    click_radius_sq = (SQUARE_SIZE * 0.55) ** 2 # Allow clicking within roughly half a square radius

    dist_sq = (x - center_x)**2 + (y - center_y)**2
    if dist_sq <= click_radius_sq:
        return row, col
    else:
        return None # Click was too far from any intersection


# --- Main Game Loop ---
def main():
    pygame.init()

    # --- Initialize Fonts ---
    # Attempt to load the specific Noto Sans font first
    piece_font_size = SQUARE_SIZE // 2
    info_font_size_small = 24
    info_font_size_large = 30

    piece_font = load_font(FONT_FILE_PATH, piece_font_size, FALLBACK_FONTS)
    info_font_small = load_font(FONT_FILE_PATH, info_font_size_small, FALLBACK_FONTS)
    info_font_large = load_font(FONT_FILE_PATH, info_font_size_large, FALLBACK_FONTS)
    # Use small info font for analysis buttons too
    analysis_font = info_font_small

    # Exit if essential fonts (piece font) failed to load
    if not piece_font:
         print("錯誤: 棋子字體無法載入，程式無法執行。")
         pygame.quit()
         sys.exit()
    # ---

    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Python Xiangqi - 象棋")
    clock = pygame.time.Clock()
    game = XiangqiGame()

    running = True
    save_btn_rect, load_btn_rect = None, None
    analysis_buttons = {}

    while running:
        # --- Event Handling ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1: # Left mouse button
                    pos = pygame.mouse.get_pos()
                    clicked_button = False

                    # 1. Check UI Button Clicks First
                    if game.game_state != STATE_ANALYSIS:
                        if save_btn_rect and save_btn_rect.collidepoint(pos):
                            game.save_game()
                            clicked_button = True
                        elif load_btn_rect and load_btn_rect.collidepoint(pos):
                            if game.load_game(): # load_game handles state change
                                 analysis_buttons = {} # Clear old buttons if load fails then returns here
                            clicked_button = True
                    else: # Analysis Mode Button Clicks
                        for key, rect in analysis_buttons.items():
                            if rect.collidepoint(pos):
                                game.analysis_navigate(key)
                                clicked_button = True
                                break # Only one button per click

                    # 2. If no button was clicked, check for Board Click
                    if not clicked_button:
                        board_coords = get_clicked_square(pos)
                        if board_coords:
                            if game.game_state == STATE_PLAYING:
                                r, c = board_coords
                                # If no piece is selected, try to select one
                                if game.selected_piece_pos is None:
                                    game.select_piece(r, c)
                                # If a piece is selected, try to move or change selection
                                else:
                                    # Try to make the move to (r, c)
                                    if not game.make_move(r, c):
                                        # Move failed. Check if the click was on another valid piece to select it instead.
                                        current_piece_on_board = game.board[r][c]
                                        if current_piece_on_board is not None and \
                                           get_piece_color(current_piece_on_board) == game.current_player:
                                             game.select_piece(r, c) # Select the new piece
                                        else:
                                             # Clicked on empty square (invalid move) or opponent piece, deselect.
                                             game.selected_piece_pos = None
                                             game.valid_moves = []
                            elif game.game_state == STATE_ANALYSIS:
                                # Allow clicking squares in analysis? Maybe highlight piece history? (Future feature)
                                pass


            if event.type == pygame.KEYDOWN:
                 if game.game_state == STATE_ANALYSIS:
                     if event.key == pygame.K_RIGHT:
                         game.analysis_navigate('next')
                     elif event.key == pygame.K_LEFT:
                         game.analysis_navigate('prev')
                     elif event.key == pygame.K_UP or event.key == pygame.K_HOME:
                         game.analysis_navigate('first')
                     elif event.key == pygame.K_DOWN or event.key == pygame.K_END:
                         game.analysis_navigate('last')
                 # Add shortcut keys? e.g., Ctrl+S to save?


        # --- Game Logic Update ---
        if game.game_state == STATE_PLAYING:
            game.update_timers()


        # --- Drawing ---
        screen.fill((200, 200, 200)) # Background color

        # Determine which board state to draw
        board_to_draw = game.analysis_board_state if game.game_state == STATE_ANALYSIS else game.board

        # Pass font for river text
        draw_board(screen, info_font_small)

        if board_to_draw: # Make sure board exists before drawing pieces
             draw_pieces(screen, board_to_draw, piece_font)

        # Draw highlights only in playing mode
        if game.game_state == STATE_PLAYING:
            draw_highlights(screen, game.selected_piece_pos, game.valid_moves)

        # Draw UI Panels (passing necessary fonts)
        save_btn_rect, load_btn_rect = draw_info_panel(screen, game, info_font_small, info_font_large) # Update button rects
        analysis_buttons = draw_analysis_panel(screen, game, analysis_font) # Update analysis button rects


        pygame.display.flip()
        clock.tick(30) # Limit FPS

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    # Check if font file exists before starting pygame
    if not os.path.exists(FONT_FILE_PATH):
        print(f"錯誤: 字體文件未找到於 '{FONT_FILE_PATH}'")
        print("請確保 'Noto Sans SC' 文件夾及 'NotoSansSC-VariableFont_wght.ttf' 文件")
        print("與 Python 腳本在同一個目錄下。")
    else:
        main()