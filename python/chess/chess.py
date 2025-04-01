# -*- coding: utf-8 -*-
import pygame
import sys
import time
import json
import os
from collections import defaultdict
from enum import Enum, auto

# --- Enums ---
class GameState(Enum):
    PLAYING = auto()
    CHECKMATE = auto()
    STALEMATE = auto()
    ANALYSIS = auto()

# --- Constants ---
# Board & Screen Dimensions
BOARD_WIDTH = 9
BOARD_HEIGHT = 10
SQUARE_SIZE = 65
INFO_PANEL_HEIGHT = 110 # Height of the panel below the board
ANALYSIS_PANEL_WIDTH = 220 # Width of the new right-side panel
BOARD_AREA_WIDTH = BOARD_WIDTH * SQUARE_SIZE
BOARD_AREA_HEIGHT = BOARD_HEIGHT * SQUARE_SIZE

SCREEN_WIDTH = BOARD_AREA_WIDTH + ANALYSIS_PANEL_WIDTH # Board Area + Right Panel
SCREEN_HEIGHT = BOARD_AREA_HEIGHT + INFO_PANEL_HEIGHT # Board Area + Bottom Panel

# Colors - Board & Lines
BOARD_COLOR_BG = (222, 184, 135) # Burlywood
LINE_COLOR_DARK = (80, 40, 0)   # Dark Brown
RIVER_TEXT_COLOR = (100, 100, 100) # Muted color for river text

# Colors - Pieces
PIECE_BG_COLOR = (245, 222, 179) # Wheat
RED_COLOR = (190, 0, 0)       # Slightly softer Red
BLACK_COLOR = (30, 30, 30)      # Not pure black

# Colors - Highlights & UI
HIGHLIGHT_COLOR = (100, 200, 100, 170) # Green highlight for moves
SELECTED_COLOR = (255, 215, 0, 150)   # Gold-like highlight for selected piece
INFO_BG_COLOR = (205, 170, 125) # Used for bottom and right panels
BUTTON_COLOR = (139, 69, 19)    # SaddleBrown for buttons
BUTTON_TEXT_COLOR = (255, 255, 240) # Ivory text

# Drawing Parameters
LINE_THICKNESS_NORMAL = 2
LINE_THICKNESS_OUTER = 4
PIECE_BORDER_WIDTH = 2
CLICK_MARGIN_RATIO = 0.45 # Ratio of square size for click detection margin

# Piece Representation (Internal)
EMPTY = None
INITIAL_BOARD_SETUP = [
    ['r', 'h', 'e', 'a', 'k', 'a', 'e', 'h', 'r'],
    [EMPTY] * 9,
    [EMPTY, 'c', EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, 'c', EMPTY],
    ['p', EMPTY, 'p', EMPTY, 'p', EMPTY, 'p', EMPTY, 'p'],
    [EMPTY] * 9, [EMPTY] * 9,
    ['P', EMPTY, 'P', EMPTY, 'P', EMPTY, 'P', EMPTY, 'P'],
    [EMPTY, 'C', EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, 'C', EMPTY],
    [EMPTY] * 9,
    ['R', 'H', 'E', 'A', 'K', 'A', 'E', 'H', 'R']
]

# Piece Character Mapping (Chinese)
PIECE_CHARS = {
    'K': '帥', 'A': '仕', 'E': '相', 'H': '傌', 'R': '俥', 'C': '炮', 'P': '兵',
    'k': '將', 'a': '士', 'e': '象', 'h': '馬', 'r': '車', 'c': '砲', 'p': '卒'
}

# --- Notation Helpers ---
# Chinese numerals for files (Red from right-to-left, Black from left-to-right) and steps
_NUM_CHARS = {1: '一', 2: '二', 3: '三', 4: '四', 5: '五', 6: '六', 7: '七', 8: '八', 9: '九'}
_RED_FILES = {0: '九', 1: '八', 2: '七', 3: '六', 4: '五', 5: '四', 6: '三', 7: '二', 8: '一'}
_BLACK_FILES = {0: '1', 1: '2', 2: '3', 3: '4', 4: '5', 5: '6', 6: '7', 7: '8', 8: '9'}

# Helper to get file notation based on color and column index
def get_file_notation(col, color):
    if color == 'red':
        return _RED_FILES.get(col, '?')
    else: # black
        return _BLACK_FILES.get(col, '?')

# Helper to get step/number notation based on color
def get_step_notation(num, color):
    # Use absolute value for the number/step count
    abs_num = abs(num)
    if color == 'red':
        return _NUM_CHARS.get(abs_num, str(abs_num)) # Fallback to string number if not 1-9
    else: # black
        return str(abs_num) # Black uses Arabic numerals

# --- End Notation Helpers ---


# Game Logic Settings
DEFAULT_TIME = 15 * 60

# Font Path
FONT_FILE_PATH = os.path.join("Noto Sans SC", "NotoSansSC-VariableFont_wght.ttf")
FALLBACK_FONTS = ["SimHei", "Microsoft YaHei", "KaiTi", "Heiti SC", "PingFang SC", "Arial Unicode MS", None]

# --- Helper Functions ---
def get_piece_color(piece):
    if piece is None: return None
    return 'red' if piece.isupper() else 'black'

def is_valid_coord(r, c):
    return 0 <= r < BOARD_HEIGHT and 0 <= c < BOARD_WIDTH

def get_king_pos(board, color):
    king_char = 'K' if color == 'red' else 'k'
    for r in range(BOARD_HEIGHT):
        for c in range(BOARD_WIDTH):
            if board[r][c] == king_char: return (r, c)
    return None

def is_in_palace(r, c):
    if not (3 <= c <= 5): return False
    return (0 <= r <= 2) or (7 <= r <= 9) # Corrected upper bound for palace

def get_palace_limits(color):
    # Corrected red palace limits (bottom)
    return (7, 9) if color == 'red' else (0, 2)

def is_across_river(r, color):
    if color == 'red': return r <= 4
    else: return r >= 5

def load_font(font_path, size, fallback_list):
    try:
        font = pygame.font.Font(font_path, size)
        return font
    except pygame.error as e:
        print(f"警告: 無法載入指定字體 '{font_path}': {e}")
        try:
            valid_fallbacks = [f for f in fallback_list if f]
            if not valid_fallbacks:
                 print(f"錯誤: 沒有有效的備選字體提供。")
                 return None
            font = pygame.font.SysFont(valid_fallbacks, size)
            if font:
                print(f"使用系統備選字體: {font.get_name()} (size {size})")
                return font
            else:
                print(f"錯誤: 找不到任何合適的字體 (包括備選: {valid_fallbacks})。")
                return None
        except Exception as fallback_e:
            print(f"嘗試備選字體時發生錯誤: {fallback_e}")
            return None
    except Exception as e:
        print(f"載入字體時發生未預期錯誤: {e}")
        return None


# --- Game Logic Class (XiangqiGame) ---
class XiangqiGame:
    def __init__(self):
        self.board = [row[:] for row in INITIAL_BOARD_SETUP] # Deep copy
        self.current_player = 'red'
        self.selected_piece_pos = None
        self.valid_moves = []
        self.move_log = [] # Stores dicts: {"start":..., "end":..., ...}
        self.game_state = GameState.PLAYING # Use Enum
        self.status_message = "紅方回合"

        self.timers = {'red': DEFAULT_TIME, 'black': DEFAULT_TIME}
        self.last_move_time = time.time()
        self.current_move_start_time = time.time()

        self.analysis_board_state = None
        self.analysis_current_step = -1

    def switch_player(self):
        self.current_player = 'black' if self.current_player == 'red' else 'red'
        player_name = "紅方" if self.current_player == 'red' else "黑方"
        self.status_message = f"{player_name} 回合"
        self.current_move_start_time = time.time()

    def select_piece(self, r, c):
        if self.game_state != GameState.PLAYING: return False
        if not is_valid_coord(r, c): return False
        piece = self.board[r][c]
        if piece is not None and get_piece_color(piece) == self.current_player:
            self.selected_piece_pos = (r, c)
            self.valid_moves = self.get_valid_moves_for_piece(r, c)
            return True
        else:
             self.selected_piece_pos = None
             self.valid_moves = []
             return False

    def _find_ambiguous_pieces(self, board, r_end, c_end, piece_to_move, color):
        """Finds if other pieces of the same type could also move to the target square."""
        piece_char_lower = piece_to_move.lower() # Use lower case for type comparison
        ambiguous_movers = []
        for r in range(BOARD_HEIGHT):
            for c in range(BOARD_WIDTH):
                piece = board[r][c]
                # Must be same type, same color, but NOT the piece actually moving
                if piece is not None and piece.lower() == piece_char_lower and get_piece_color(piece) == color :
                    # Check if this other piece could potentially move to the target
                    # Using get_valid_moves_for_piece ensures legality check (no self-check, etc.)
                    # Need to temporarily set selected piece to check its valid moves
                    original_selected = self.selected_piece_pos
                    original_valid = self.valid_moves
                    self.selected_piece_pos = (r,c) # Temporarily select this piece
                    potential_moves = self.get_valid_moves_for_piece(r, c) # Get its legal moves
                    self.selected_piece_pos = original_selected # Restore original state
                    self.valid_moves = original_valid

                    if (r_end, c_end) in potential_moves:
                         ambiguous_movers.append((r, c))
        return ambiguous_movers

    def get_algebraic_notation(self, board_before_move, start_pos, end_pos, player_color):
        """Generates standard Chinese algebraic notation for a move."""
        r_start, c_start = start_pos
        r_end, c_end = end_pos
        piece = board_before_move[r_start][c_start]

        if piece is None: return "錯誤：起始位置無棋子" # Error case

        piece_char_display = PIECE_CHARS.get(piece, '?') # Get the display character (e.g., '相')
        piece_type = piece.lower()

        dr = r_end - r_start
        dc = c_end - c_start

        # 1. Determine Direction (進, 退, 平)
        direction = ''
        if dc == 0: # Purely vertical move
            if player_color == 'red':
                direction = '進' if dr < 0 else '退' # Red moves 'up' (decreasing row) is 進
            else: # black
                direction = '進' if dr > 0 else '退' # Black moves 'down' (increasing row) is 進
        elif dr == 0: # Purely horizontal move
            direction = '平'
        else: # Diagonal move (Horse, Elephant, Advisor) - Use 進/退 based on row change
            if player_color == 'red':
                direction = '進' if dr < 0 else '退'
            else: # black
                direction = '進' if dr > 0 else '退'

        # 2. Determine Target Value (File or Steps)
        target_val = ''
        if direction == '平':
            target_val = get_file_notation(c_end, player_color)
        else: # 進 or 退
            if piece_type in ['k', 'a', 'e', 'h']: # King, Advisor, Elephant, Horse use target file
                target_val = get_file_notation(c_end, player_color)
            elif piece_type in ['r', 'c', 'p']: # Rook, Cannon, Pawn use steps moved vertically (absolute value)
                target_val = get_step_notation(dr, player_color)

        # 3. Handle Ambiguity and Pawns (Determine the first part of the notation)
        first_part = piece_char_display
        needs_start_file = False

        if piece_type == 'p': # Pawns always include starting file
            needs_start_file = True
        else: # Check ambiguity for other pieces (R, H, C, E, A)
            # Find other pieces of the same type and color that could *legally* move to the target square
            potential_movers = self._find_ambiguous_pieces(board_before_move, r_end, c_end, piece, player_color)

            # Filter out the actual moving piece from the list of potential movers
            ambiguous_others = [p for p in potential_movers if p != start_pos]

            if ambiguous_others: # If there's at least one other piece that could make the same move
                # Check if they are on different files.
                files = {pos[1] for pos in ambiguous_others} # Files of the *other* ambiguous pieces
                files.add(c_start) # Include the file of the piece actually moving

                if len(files) > 1: # If pieces are on different files, ambiguity exists
                    needs_start_file = True
                else:
                    # If all ambiguous pieces (including the mover) are on the same file
                    # Standard notation might use 前 (front) or 后 (back) based on rank.
                    # This is complex to implement correctly for all cases (e.g., 3+ pieces).
                    # A common simplification (and often acceptable) is to just use the starting file
                    # if ambiguity exists, even if on the same file. Let's adopt this simplification.
                    if piece_type in ['r', 'h', 'c']: # Usually include file for these if ambiguous on same file
                       needs_start_file = True
                    # For E, A, K ambiguity on the same file is less common / handled differently,
                    # but our basic check might still trigger it. We'll omit start file for these cases
                    # unless they are on different files.

        if needs_start_file:
            first_part = get_file_notation(c_start, player_color) + piece_char_display
            # Note the change: File first for Red (e.g., 八馬...), Piece first for Black (e.g., 馬8...)
            # Let's standardize to Piece + File for simplicity and consistency in code logic
            # Common notation varies slightly, but Piece+File is understandable.
            first_part = piece_char_display + get_file_notation(c_start, player_color)


        # Combine: Piece/File + Direction + Target/Steps
        return f"{first_part}{direction}{target_val}"


    def make_move(self, r_end, c_end):
        if not self.selected_piece_pos or (r_end, c_end) not in self.valid_moves:
            self.selected_piece_pos = None
            self.valid_moves = []
            return False
        r_start, c_start = self.selected_piece_pos
        piece_to_move = self.board[r_start][c_start] # Get piece before it's moved
        captured_piece = self.board[r_end][c_end]
        time_taken = time.time() - self.current_move_start_time

        # --- Generate Algebraic Notation BEFORE updating the board ---
        board_state_before_move = [row[:] for row in self.board] # Critical: Copy board BEFORE move
        notation = self.get_algebraic_notation(board_state_before_move, (r_start, c_start), (r_end, c_end), self.current_player)
        # -------------------------------------------------------------

        # Append captured piece info to notation (Optional, not standard algebraic)
        # if captured_piece: notation += f" 吃{PIECE_CHARS.get(captured_piece, '?')}"

        # Update Move Log
        self.move_log.append({
            "start": (r_start, c_start), "end": (r_end, c_end), "piece": piece_to_move,
            "captured": captured_piece, "notation": notation, # Store the NEW notation
            "time": round(time_taken, 2), "player": self.current_player
        })

        # Update Board State
        self.board[r_end][c_end] = piece_to_move
        self.board[r_start][c_start] = EMPTY
        self.selected_piece_pos = None
        self.valid_moves = []
        self.last_move_time = time.time()

        # Check Game End Conditions
        opponent_color = 'black' if self.current_player == 'red' else 'red'
        winner_name = "紅方" if self.current_player == 'red' else "黑方"
        if self.is_checkmate(opponent_color):
            self.game_state = GameState.CHECKMATE
            self.status_message = f"將死! {winner_name} 勝!"
        elif self.is_stalemate(opponent_color):
            self.game_state = GameState.STALEMATE
            self.status_message = "欠行! 和棋!"
        else:
            # Switch player and check for check on the new player
            self.switch_player() # switch_player updates status to "Player 回合"
            if self.is_in_check(self.current_player):
                 player_name = "紅方" if self.current_player == 'red' else "黑方"
                 self.status_message = f"{player_name} 回合 (將軍!)" # Append check status

        return True


    def is_in_check(self, player_color, current_board=None):
        board_to_check = current_board if current_board else self.board
        king_pos = get_king_pos(board_to_check, player_color)
        if not king_pos: return False # Should not happen in a normal game
        opponent_color = 'black' if player_color == 'red' else 'red'
        for r in range(BOARD_HEIGHT):
            for c in range(BOARD_WIDTH):
                piece = board_to_check[r][c]
                if piece is not None and get_piece_color(piece) == opponent_color:
                    # Check raw moves - if any raw move targets the king, it's check
                    # (Legality check is not needed here, only reachability)
                    raw_moves = self._get_raw_valid_moves(r, c, board_to_check)
                    if king_pos in raw_moves:
                        # print(f"CHECK DETECTED: {piece} at ({r},{c}) attacks King at {king_pos}") # Debugging
                        return True
        return False

    def does_move_result_in_check(self, start_pos, end_pos, player_color):
         """Checks if making a move would put the player's own king in check."""
         r_start, c_start = start_pos
         r_end, c_end = end_pos
         piece = self.board[r_start][c_start]
         captured = self.board[r_end][c_end]

         # Simulate the move
         self.board[r_end][c_end] = piece
         self.board[r_start][c_start] = EMPTY

         in_check = self.is_in_check(player_color) # Check if the current player is now in check

         # Undo the move
         self.board[r_start][c_start] = piece
         self.board[r_end][c_end] = captured

         return in_check

    def kings_are_exposed(self, current_board=None):
        """Checks if the two kings are facing each other on the same file with no pieces between."""
        board_to_check = current_board if current_board else self.board
        red_k_pos = get_king_pos(board_to_check, 'red')
        black_k_pos = get_king_pos(board_to_check, 'black')

        if not red_k_pos or not black_k_pos: return False # One king missing (shouldn't happen)

        r1, c1 = red_k_pos
        r2, c2 = black_k_pos

        # Must be on the same file
        if c1 != c2: return False

        # Check for blocking pieces between the kings
        for r in range(min(r1, r2) + 1, max(r1, r2)):
            if board_to_check[r][c1] is not None:
                return False # A piece is blocking

        # If on same file and no pieces between, they are exposed
        return True

    def get_valid_moves_for_piece(self, r_start, c_start):
        """Gets all *legal* moves for a piece, considering checks and king exposure."""
        piece = self.board[r_start][c_start]
        if piece is None: return []

        player_color = get_piece_color(piece)
        raw_moves = self._get_raw_valid_moves(r_start, c_start, self.board)
        legal_moves = []

        for r_end, c_end in raw_moves:
            # Simulate the move to check for legality
            original_piece_at_target = self.board[r_end][c_end]
            self.board[r_end][c_end] = piece
            self.board[r_start][c_start] = EMPTY

            # Check 1: Does the move put the player's own king in check?
            is_self_check = self.is_in_check(player_color)

            # Check 2: Does the move result in the kings facing each other?
            is_king_exposed = self.kings_are_exposed()

            # Undo the simulation
            self.board[r_start][c_start] = piece
            self.board[r_end][c_end] = original_piece_at_target

            # If the move is legal (doesn't cause self-check and doesn't expose kings)
            if not is_self_check and not is_king_exposed:
                legal_moves.append((r_end, c_end))

        return legal_moves

    def _add_raw_move(self, moves_list, r, c, current_board, own_color):
        """Helper to add a potential move to a list if the target square is valid and not occupied by own piece."""
        if is_valid_coord(r, c):
            target_piece = current_board[r][c]
            if target_piece is None:
                moves_list.append((r, c)); return True # Added empty square move, can continue path
            elif get_piece_color(target_piece) != own_color:
                moves_list.append((r, c)); return False # Added capture move, path blocked
            else:
                return False # Own piece blocks path
        return False # Invalid coordinate blocks path

    def _get_raw_valid_moves(self, r_start, c_start, current_board):
        """Generates potential moves based only on piece movement rules, ignoring checks."""
        moves = []
        piece = current_board[r_start][c_start]
        if piece is None: return []
        color = get_piece_color(piece)
        piece_type = piece.lower()

        if piece_type == 'k': # 將/帥 (King)
            pr_min, pr_max = get_palace_limits(color)
            for dr, dc in [(0,1),(0,-1),(1,0),(-1,0)]:
                re, ce = r_start+dr, c_start+dc
                if pr_min <= re <= pr_max and 3 <= ce <= 5: # Stay within palace bounds
                    self._add_raw_move(moves, re, ce, current_board, color)
        elif piece_type == 'a': # 士/仕 (Advisor)
            pr_min, pr_max = get_palace_limits(color)
            for dr, dc in [(1,1),(1,-1),(-1,1),(-1,-1)]: # Diagonal moves only
                re, ce = r_start+dr, c_start+dc
                if pr_min <= re <= pr_max and 3 <= ce <= 5: # Stay within palace bounds
                    self._add_raw_move(moves, re, ce, current_board, color)
        elif piece_type == 'e': # 象/相 (Elephant) - CORRECTED
            for dr, dc in [(2,2),(2,-2),(-2,2),(-2,-2)]: # 走 "田" 字
                re, ce = r_start+dr, c_start+dc
                if not is_valid_coord(re, ce): continue # Target off board
                # River Crossing Check
                if (color == 'red' and re <= 4) or (color == 'black' and re >= 5):
                    continue # Cannot cross river
                # Blocking Check (Elephant eye)
                rb, cb = r_start + dr // 2, c_start + dc // 2
                if is_valid_coord(rb, cb) and current_board[rb][cb] is None:
                    self._add_raw_move(moves, re, ce, current_board, color)
        elif piece_type == 'h': # 馬 (Horse)
            for dr, dc, br, bc in [(-2,-1,-1,0),(-2,1,-1,0),(2,-1,1,0),(2,1,1,0), # Vertical L
                                   (-1,-2,0,-1),(1,-2,0,-1),(-1,2,0,1),(1,2,0,1)]: # Horizontal L
                re, ce = r_start+dr, c_start+dc
                rb, cb = r_start+br, c_start+bc # Blocking position
                if is_valid_coord(rb, cb) and current_board[rb][cb] is None: # Check blocker is valid and empty
                    self._add_raw_move(moves, re, ce, current_board, color)
        elif piece_type == 'r': # 車 (Rook)
            for dr, dc in [(0,1),(0,-1),(1,0),(-1,0)]: # Directions
                rt, ct = r_start, c_start
                while True:
                    rt, ct = rt + dr, ct + dc
                    if not self._add_raw_move(moves, rt, ct, current_board, color):
                        break # Stop if move wasn't added (blocked or off-board)
        elif piece_type == 'c': # 炮/砲 (Cannon)
            for dr, dc in [(0,1),(0,-1),(1,0),(-1,0)]: # Directions
                rt, ct = r_start, c_start
                jumped = False # Have we jumped over the 'screen'?
                while True:
                    rt, ct = rt + dr, ct + dc
                    if not is_valid_coord(rt, ct): break # Off board
                    target = current_board[rt][ct]
                    if not jumped:
                        if target is None:
                            moves.append((rt, ct)) # Move freely to empty square
                        else:
                            jumped = True # Found the screen, now look for capture
                    else: # After jumping screen
                        if target is not None: # Found a piece after the screen
                            if get_piece_color(target) != color: # Is it opponent?
                                moves.append((rt, ct)) # Capture
                            break # Path blocked (either by capture or own piece)
                        # else: Keep going if square after screen is empty
        elif piece_type == 'p': # 兵/卒 (Pawn)
            dr_fwd = -1 if color == 'red' else 1 # Forward direction
            # Forward move
            self._add_raw_move(moves, r_start + dr_fwd, c_start, current_board, color)
            # Sideways moves (only after crossing the river)
            if is_across_river(r_start, color):
                self._add_raw_move(moves, r_start, c_start + 1, current_board, color)
                self._add_raw_move(moves, r_start, c_start - 1, current_board, color)
        return moves

    def get_all_valid_moves(self, player_color):
        """Gets all legal moves for all pieces of a given color."""
        all_moves = []
        for r in range(BOARD_HEIGHT):
            for c in range(BOARD_WIDTH):
                piece = self.board[r][c]
                if piece is not None and get_piece_color(piece) == player_color:
                    valid_piece_moves = self.get_valid_moves_for_piece(r, c) # Gets only LEGAL moves
                    if valid_piece_moves:
                        all_moves.extend([((r, c), move) for move in valid_piece_moves])
        return all_moves

    def is_checkmate(self, player_color):
        """Checks if the player is in checkmate."""
        return self.is_in_check(player_color) and not self.get_all_valid_moves(player_color)

    def is_stalemate(self, player_color):
        """Checks if the player is in stalemate."""
        return not self.is_in_check(player_color) and not self.get_all_valid_moves(player_color)

    def update_timers(self):
        if self.game_state == GameState.PLAYING:
            now = time.time()
            time_elapsed = now - self.last_move_time
            self.last_move_time = now
            player_timer = self.timers[self.current_player]
            player_timer -= time_elapsed
            self.timers[self.current_player] = max(0, player_timer)
            if self.timers[self.current_player] <= 0:
                self.game_state = GameState.CHECKMATE
                opponent = 'black' if self.current_player == 'red' else 'red'
                opponent_name = "黑方" if opponent == 'black' else "紅方"
                self.status_message = f"超時! {opponent_name} 勝!"

    def save_game(self, filename="xiangqi_save.json"):
        try:
            # Only save necessary data for reconstruction
            save_data = { "move_log": self.move_log }
            with open(filename, 'w', encoding='utf-8') as f: json.dump(save_data, f, indent=4, ensure_ascii=False)
            print(f"棋譜已儲存至 {filename}")
            self.status_message = f"棋譜已儲存至 {filename}"
        except IOError as e: print(f"儲存遊戲時發生 IO 錯誤: {e}"); self.status_message = f"儲存錯誤: {e}"
        except Exception as e: print(f"儲存遊戲時發生未預期錯誤: {e}"); self.status_message = "儲存遊戲時發生錯誤."

    def load_game(self, filename="xiangqi_save.json"):
        try:
            if not os.path.exists(filename): self.status_message = f"找不到檔案: {filename}"; return False
            with open(filename, 'r', encoding='utf-8') as f: save_data = json.load(f)

            self.__init__() # Reset game state completely

            # Load the move log
            loaded_log = save_data.get("move_log", [])
            if not loaded_log:
                 print("警告: 載入的棋譜為空.")
                 self.status_message = "載入的棋譜為空"
                 # Stay in playing state? Or switch to analysis? Let's switch.
                 self.game_state = GameState.ANALYSIS
                 self.analysis_current_step = -1
                 self.analysis_board_state = [row[:] for row in INITIAL_BOARD_SETUP]
                 self.status_message = self._get_analysis_status()
                 return True # Loaded successfully, even if empty

            self.move_log = loaded_log

            # Transition to Analysis state
            self.game_state = GameState.ANALYSIS
            self.analysis_current_step = -1 # Start at the beginning
            self.analysis_board_state = [row[:] for row in INITIAL_BOARD_SETUP] # Start with initial board
            self.status_message = self._get_analysis_status() # Update status for step -1
            print(f"從 {filename} 載入遊戲. 進入分析模式.")
            return True
        except FileNotFoundError: print(f"錯誤: 找不到存檔文件 '{filename}'"); self.status_message = f"找不到檔案: {filename}"; return False
        except json.JSONDecodeError as e: print(f"錯誤: 解析存檔文件 '{filename}' 失敗: {e}"); self.status_message = "載入失敗: 文件格式錯誤"; return False
        except IOError as e: print(f"載入遊戲時發生 IO 錯誤: {e}"); self.status_message = f"載入錯誤: {e}"; return False
        except Exception as e: print(f"載入遊戲時發生未預期錯誤: {e}"); self.status_message = "載入遊戲時發生錯誤."; self.__init__(); return False # Reset on other errors


    def analysis_navigate(self, direction):
        if self.game_state != GameState.ANALYSIS: return
        current_total_moves = len(self.move_log)
        if current_total_moves == 0: return # No moves to navigate

        target_step = self.analysis_current_step
        if direction == 'next': target_step = min(self.analysis_current_step + 1, current_total_moves - 1)
        elif direction == 'prev': target_step = max(self.analysis_current_step - 1, -1)
        elif direction == 'first': target_step = -1
        elif direction == 'last': target_step = current_total_moves - 1

        if target_step != self.analysis_current_step:
             self._reconstruct_board_to_step(target_step)
             self.status_message = self._get_analysis_status() # Update status message after navigation

    def _reconstruct_board_to_step(self, target_step_index):
        """Rebuilds the analysis_board_state up to the given move index."""
        self.analysis_board_state = [row[:] for row in INITIAL_BOARD_SETUP] # Start from scratch
        current_internal_step = -1 # Tracks the last successfully applied step index

        for i in range(target_step_index + 1): # Iterate up to and including the target index
            if i < len(self.move_log):
                 move_data = self.move_log[i]
                 # Basic validation of move data structure
                 if "start" not in move_data or "end" not in move_data or "piece" not in move_data:
                      print(f"警告: 第 {i+1} 步棋譜數據不完整，跳過。 Move data: {move_data}")
                      continue # Skip this corrupted move data

                 r_start, c_start = move_data["start"]
                 r_end, c_end = move_data["end"]
                 piece_moved = move_data["piece"] # The piece that the log says moved

                 # Validate coordinates
                 if not (is_valid_coord(r_start, c_start) and is_valid_coord(r_end, c_end)):
                      print(f"警告: 第 {i+1} 步棋譜座標無效 ({r_start},{c_start})->({r_end},{c_end})，停止重建。")
                      self.analysis_current_step = current_internal_step # Roll back to last valid step
                      return

                 # Validate piece match before applying
                 piece_on_board = self.analysis_board_state[r_start][c_start]
                 if piece_on_board != piece_moved:
                      print(f"警告: 在重建棋譜第 {i+1} 步時發現棋子不一致. "
                            f"位置 ({r_start},{c_start}). 棋譜記錄移動 '{piece_moved}', "
                            f"但棋盤上是 '{piece_on_board}'. 停止重建。")
                      self.analysis_current_step = current_internal_step # Roll back to last valid step
                      return

                 # If valid, apply the move to the analysis board
                 self.analysis_board_state[r_end][c_end] = piece_moved
                 self.analysis_board_state[r_start][c_start] = EMPTY
                 current_internal_step = i # Mark this step as successfully applied

            else:
                # This case should ideally not be reached if target_step_index is correct
                print(f"警告: 嘗試重建棋步 {i+1}, 但棋譜只有 {len(self.move_log)} 步.")
                break # Stop if index goes out of bounds

        # Update the official analysis step index after successful reconstruction
        self.analysis_current_step = current_internal_step

    def _get_analysis_status(self): # Generates the status string for display
        if self.game_state != GameState.ANALYSIS: return ""
        total_moves = len(self.move_log)
        current_move_num = self.analysis_current_step + 1 # 1-based index for display

        if self.analysis_current_step == -1: # Before the first move
            return f"分析: 初始局面\n(0/{total_moves} 步)"
        elif 0 <= self.analysis_current_step < total_moves:
            move_data = self.move_log[self.analysis_current_step]
            notation = move_data.get("notation", "無記錄") # Use the generated algebraic notation
            time_taken_str = f"{move_data.get('time', '?')}s" # Add 's' for seconds
            player = "紅方" if move_data.get("player") == 'red' else "黑方"
            return f"分析: 第 {current_move_num}/{total_moves} 步 ({player})\n{notation}\n(思考: {time_taken_str})"
        # elif self.analysis_current_step >= total_moves - 1 and total_moves > 0: # At the last move
             # Handled by the previous case now, as analysis_current_step won't exceed total_moves - 1
             # move_data = self.move_log[total_moves - 1]
             # notation = move_data.get("notation", "無記錄")
             # player = "紅方" if move_data.get("player") == 'red' else "黑方"
             # final_status = "(終局)" # Simplistic end status
             # return f"分析: 第 {total_moves}/{total_moves} 步 ({player}) {final_status}\n{notation}"
        else: # Error state or empty log
             return f"分析: 無棋步記錄\n(0/0 步)"

# --- Drawing Functions ---

# Simple text wrapping function
def draw_text_wrapped(surface, text, rect, font, color):
    lines = text.splitlines()
    y = rect.top
    line_spacing = font.get_linesize() + 2 # Add a little extra spacing

    for line in lines:
        # Handle potential None value for font if loading failed
        if font is None:
            print("Error: Font not available for draw_text_wrapped.")
            return y # Return current y position

        words = line.split(' ')
        current_line = ''
        while words:
            test_word = words[0]
            # Add space only if current_line is not empty
            test_line = current_line + (' ' if current_line else '') + test_word

            # Check if the test line fits horizontally
            try:
                line_width = font.size(test_line)[0]
            except AttributeError: # Handle case where font might be None briefly
                 print("Error: Font object invalid during size check.")
                 return y # Exit drawing for this call
            except Exception as e:
                 print(f"Error checking font size: {e}")
                 return y

            if line_width < rect.width:
                current_line = test_line
                words.pop(0)
            else:
                # Word doesn't fit, render the current line (if any)
                if current_line:
                    try:
                        image = font.render(current_line.strip(), True, color)
                        surface.blit(image, (rect.left, y))
                        y += line_spacing
                    except Exception as e:
                         print(f"Error rendering wrapped text line '{current_line.strip()}': {e}")
                    current_line = '' # Reset for the next part of the line

                # If the single word itself is too long, render what fits (or just the word)
                try:
                    word_width = font.size(test_word)[0]
                except Exception as e:
                    print(f"Error checking word size '{test_word}': {e}")
                    word_width = rect.width # Assume it's too long

                if word_width >= rect.width:
                    # Render the long word on its own line (truncation is harder)
                    try:
                        # Basic truncation: Fit as many characters as possible
                        temp_word = test_word
                        while font.size(temp_word)[0] >= rect.width and len(temp_word) > 1:
                            temp_word = temp_word[:-1]
                        if temp_word:
                           image = font.render(temp_word, True, color)
                           surface.blit(image, (rect.left, y))
                           y += line_spacing
                    except Exception as e:
                        print(f"Error rendering truncated long word '{test_word}': {e}")

                    words.pop(0) # Move past the long word
                    current_line = '' # Ensure reset
                else:
                    # The word should fit on a new line by itself
                    current_line = test_word # Start the new line with this word
                    words.pop(0)


        # Render the last part of the line (or the whole line if it fit)
        if current_line:
             try:
                 image = font.render(current_line.strip(), True, color)
                 surface.blit(image, (rect.left, y))
                 y += line_spacing
             except Exception as e:
                 print(f"Error rendering final wrapped text line '{current_line.strip()}': {e}")
    return y # Return the Y coordinate after the last line


# draw_board
def draw_board(screen, river_font):
    screen.fill(BOARD_COLOR_BG, (0, 0, BOARD_AREA_WIDTH, BOARD_AREA_HEIGHT)) # Fill just the board area
    board_rect = pygame.Rect(0, 0, BOARD_AREA_WIDTH, BOARD_AREA_HEIGHT)
    half_sq = SQUARE_SIZE // 2
    RIVER_TOP_ROW = 4; RIVER_BOTTOM_ROW = 5

    # Vertical Lines (Draw in two parts to skip the river visually)
    for c in range(BOARD_WIDTH):
        x = c * SQUARE_SIZE + half_sq
        pygame.draw.line(screen, LINE_COLOR_DARK, (x, half_sq), (x, RIVER_TOP_ROW * SQUARE_SIZE + half_sq), LINE_THICKNESS_NORMAL)
        pygame.draw.line(screen, LINE_COLOR_DARK, (x, RIVER_BOTTOM_ROW * SQUARE_SIZE + half_sq), (x, (BOARD_HEIGHT - 1) * SQUARE_SIZE + half_sq), LINE_THICKNESS_NORMAL)

    # Horizontal Lines (Draw all the way across)
    for r in range(BOARD_HEIGHT):
        y = r * SQUARE_SIZE + half_sq; start_x = half_sq; end_x = (BOARD_WIDTH - 1) * SQUARE_SIZE + half_sq
        pygame.draw.line(screen, LINE_COLOR_DARK, (start_x, y), (end_x, y), LINE_THICKNESS_NORMAL)

    # Outer Border
    pygame.draw.rect(screen, LINE_COLOR_DARK, (half_sq, half_sq, (BOARD_WIDTH - 1) * SQUARE_SIZE, (BOARD_HEIGHT - 1) * SQUARE_SIZE), LINE_THICKNESS_OUTER)

    # Palaces (Diagonal lines)
    pygame.draw.line(screen, LINE_COLOR_DARK, (3*SQUARE_SIZE+half_sq, half_sq), (5*SQUARE_SIZE+half_sq, 2*SQUARE_SIZE+half_sq), LINE_THICKNESS_NORMAL)
    pygame.draw.line(screen, LINE_COLOR_DARK, (5*SQUARE_SIZE+half_sq, half_sq), (3*SQUARE_SIZE+half_sq, 2*SQUARE_SIZE+half_sq), LINE_THICKNESS_NORMAL)
    pygame.draw.line(screen, LINE_COLOR_DARK, (3*SQUARE_SIZE+half_sq, 7*SQUARE_SIZE+half_sq), (5*SQUARE_SIZE+half_sq, 9*SQUARE_SIZE+half_sq), LINE_THICKNESS_NORMAL)
    pygame.draw.line(screen, LINE_COLOR_DARK, (5*SQUARE_SIZE+half_sq, 7*SQUARE_SIZE+half_sq), (3*SQUARE_SIZE+half_sq, 9*SQUARE_SIZE+half_sq), LINE_THICKNESS_NORMAL)

    # River Text
    if river_font:
        texts = [("楚", 1.5), ("河", 2.5), ("漢", 5.5), ("界", 6.5)]
        river_y = RIVER_TOP_ROW * SQUARE_SIZE + SQUARE_SIZE # Center Y in river gap
        for text, col_pos in texts:
             try:
                 surf = river_font.render(text, True, RIVER_TEXT_COLOR)
                 text_x = (col_pos + 0.5) * SQUARE_SIZE # Center X in "column"
                 screen.blit(surf, surf.get_rect(center=(int(text_x), int(river_y))))
             except Exception as e: print(f"Error rendering river text '{text}': {e}")

    # Cannon/Pawn Markers
    pawn_marks_c, pawn_marks_r = [0, 2, 4, 6, 8], [3, 6]
    cannon_marks_c, cannon_marks_r = [1, 7], [2, 7]
    mark_len, mark_offset = SQUARE_SIZE // 9, SQUARE_SIZE // 12
    all_marks_coords = set()
    for r in pawn_marks_r:
        for c in pawn_marks_c: all_marks_coords.add((c, r))
    for r in cannon_marks_r:
        for c in cannon_marks_c: all_marks_coords.add((c, r))

    for c, r in all_marks_coords:
         x, y = c * SQUARE_SIZE + half_sq, r * SQUARE_SIZE + half_sq # Intersection center
         corner_markers = {
             (-1, -1): [(-mark_len, 0), (0, -mark_len)], ( 1, -1): [( mark_len, 0), (0, -mark_len)],
             (-1,  1): [(-mark_len, 0), (0,  mark_len)], ( 1,  1): [( mark_len, 0), (0,  mark_len)]
         }
         for (cdx, cdy), lines in corner_markers.items():
             if (c == 0 and cdx < 0) or \
                (c == BOARD_WIDTH - 1 and cdx > 0) or \
                (r == 0 and cdy < 0) or \
                (r == BOARD_HEIGHT - 1 and cdy > 0): continue # Skip markers pointing off board

             corner_x = x + cdx * mark_offset
             corner_y = y + cdy * mark_offset
             for (ldx, ldy) in lines:
                 end_x, end_y = corner_x + ldx, corner_y + ldy
                 pygame.draw.line(screen, LINE_COLOR_DARK, (corner_x, corner_y), (end_x, end_y), LINE_THICKNESS_NORMAL)

# draw_pieces
def draw_pieces(screen, board, piece_font):
    if not piece_font: return
    radius = SQUARE_SIZE // 2 - 6 # Piece radius
    for r in range(BOARD_HEIGHT):
        for c in range(BOARD_WIDTH):
            piece = board[r][c]
            if piece is not None:
                char = PIECE_CHARS.get(piece, "?")
                color = RED_COLOR if get_piece_color(piece) == 'red' else BLACK_COLOR
                center_x = c * SQUARE_SIZE + SQUARE_SIZE // 2
                center_y = r * SQUARE_SIZE + SQUARE_SIZE // 2
                try:
                    # Draw circle background and border
                    pygame.draw.circle(screen, PIECE_BG_COLOR, (center_x, center_y), radius)
                    pygame.draw.circle(screen, color, (center_x, center_y), radius, PIECE_BORDER_WIDTH) # Border color matches piece
                    # Draw text
                    text_surf = piece_font.render(char, True, color)
                    screen.blit(text_surf, text_surf.get_rect(center=(center_x, center_y)))
                except Exception as e: print(f"Error drawing piece {piece} at ({r},{c}): {e}")

# draw_highlights
def draw_highlights(screen, selected_pos, valid_moves, selected_surf, move_surf, marker_radius):
     # Highlight selected piece
     if selected_pos:
        r, c = selected_pos
        center_x = c * SQUARE_SIZE + SQUARE_SIZE // 2
        center_y = r * SQUARE_SIZE + SQUARE_SIZE // 2
        screen.blit(selected_surf, selected_surf.get_rect(center=(center_x, center_y)))
     # Highlight valid moves
     for r, c in valid_moves:
        center_x = c * SQUARE_SIZE + SQUARE_SIZE // 2
        center_y = r * SQUARE_SIZE + SQUARE_SIZE // 2
        screen.blit(move_surf, move_surf.get_rect(center=(center_x, center_y)))

# draw_info_panel (Below board)
def draw_info_panel(screen, game, font_small, font_large):
    save_btn_rect, load_btn_rect = None, None
    panel_rect = pygame.Rect(0, BOARD_AREA_HEIGHT, BOARD_AREA_WIDTH, INFO_PANEL_HEIGHT)
    pygame.draw.rect(screen, INFO_BG_COLOR, panel_rect) # Draw panel background

    # Only show timers/status/buttons if NOT in analysis mode
    if game.game_state != GameState.ANALYSIS:
        if not font_small or not font_large: return save_btn_rect, load_btn_rect

        # Draw Timers
        try:
            rm, rs = divmod(int(game.timers['red']), 60)
            bm, bs = divmod(int(game.timers['black']), 60)
            t_red = font_small.render(f"紅方: {rm:02d}:{rs:02d}", True, RED_COLOR)
            t_black = font_small.render(f"黑方: {bm:02d}:{bs:02d}", True, BLACK_COLOR)
            screen.blit(t_red, (panel_rect.left + 20, panel_rect.top + 15))
            screen.blit(t_black, (panel_rect.right - t_black.get_width() - 20, panel_rect.top + 15))
        except Exception as e: print(f"Error rendering timers: {e}")

        # Draw Status Message
        try:
            status_surf = font_large.render(game.status_message, True, BLACK_COLOR)
            screen.blit(status_surf, status_surf.get_rect(center=(panel_rect.centerx, panel_rect.top + 55)))
        except Exception as e: print(f"Error rendering status message: {e}")

        # Draw Buttons (Save/Load)
        btn_h, btn_w, btn_padding = 35, 90, 15
        btn_y = panel_rect.bottom - btn_h - 10 # Position near bottom
        save_btn_rect = pygame.Rect(panel_rect.left + 20, btn_y, btn_w, btn_h)
        load_btn_rect = pygame.Rect(save_btn_rect.right + btn_padding, btn_y, btn_w, btn_h)
        try:
            # Save Button
            pygame.draw.rect(screen, BUTTON_COLOR, save_btn_rect, border_radius=6)
            save_txt = font_small.render("儲存棋譜", True, BUTTON_TEXT_COLOR)
            screen.blit(save_txt, save_txt.get_rect(center=save_btn_rect.center))
            # Load Button
            pygame.draw.rect(screen, BUTTON_COLOR, load_btn_rect, border_radius=6)
            load_txt = font_small.render("載入棋譜", True, BUTTON_TEXT_COLOR)
            screen.blit(load_txt, load_txt.get_rect(center=load_btn_rect.center))
        except Exception as e: print(f"Error rendering save/load buttons: {e}")

    return save_btn_rect, load_btn_rect # Return rects (might be None if in analysis)

# draw_right_panel (Analysis Panel)
def draw_right_panel(screen, game, font_small, font_large, analysis_font):
    buttons = {} # Dictionary to store button rects keyed by function ('first', 'prev', etc.)
    panel_rect = pygame.Rect(BOARD_AREA_WIDTH, 0, ANALYSIS_PANEL_WIDTH, SCREEN_HEIGHT)
    pygame.draw.rect(screen, INFO_BG_COLOR, panel_rect) # Draw panel background

    # Only draw content if in analysis mode
    if game.game_state == GameState.ANALYSIS:
        # Check if necessary fonts are loaded
        if not analysis_font or not font_small:
            if not hasattr(draw_right_panel, "font_warning_printed"): # Print warning only once
                print("警告: 分析面板所需字體未載入，無法顯示內容。")
                draw_right_panel.font_warning_printed = True
            return buttons

        # 1. Display Analysis Status Info (uses pre-formatted message from game object)
        status_text = game.status_message
        status_rect = pygame.Rect(panel_rect.left + 15, panel_rect.top + 20, panel_rect.width - 30, 100) # Area for status text
        try:
            # Use draw_text_wrapped to handle multi-line status
            last_y = draw_text_wrapped(screen, status_text, status_rect, font_small, BLACK_COLOR)
        except Exception as e:
             print(f"Error rendering analysis status text: {e}")
             last_y = status_rect.top + status_rect.height # Estimate end position on error

        # 2. Draw Navigation Buttons
        button_texts = {"first":"<< 首步", "prev":"< 上一步", "next":"下一步 >", "last":"末步 >>"}
        btn_w, btn_h, v_space = 150, 40, 15 # Button dimensions and spacing
        start_y = last_y + 25 # Start buttons below the text area, with some padding
        current_y = start_y

        try:
            for key, txt in button_texts.items():
                btn_x = panel_rect.centerx - btn_w // 2 # Center buttons horizontally
                rect = pygame.Rect(btn_x, current_y, btn_w, btn_h)

                # Check if button fits within the panel height
                if rect.bottom > panel_rect.bottom - 10:
                    if not hasattr(draw_right_panel, "button_space_warning_printed"):
                        print("警告: 分析面板空間不足，無法繪製所有按鈕。")
                        draw_right_panel.button_space_warning_printed = True
                    break # Stop drawing buttons

                # Draw button background and text
                pygame.draw.rect(screen, BUTTON_COLOR, rect, border_radius=6)
                surf = analysis_font.render(txt, True, BUTTON_TEXT_COLOR)
                screen.blit(surf, surf.get_rect(center=rect.center))
                buttons[key] = rect # Store rect for click detection
                current_y += btn_h + v_space # Move down for the next button
        except Exception as e: print(f"Error rendering analysis buttons: {e}")
    else:
        # Optional: Draw something else when not in analysis mode (e.g., logo)
        if font_large: # Check if font exists
             try:
                 title_surf = font_large.render("象棋", True, BUTTON_COLOR)
                 screen.blit(title_surf, title_surf.get_rect(center=panel_rect.center))
             except Exception as e: print(f"Error rendering title in right panel: {e}")

    return buttons # Return the dictionary of button rects

# get_clicked_square
def get_clicked_square(pos):
    x, y = pos
    if not (0 <= x < BOARD_AREA_WIDTH and 0 <= y < BOARD_AREA_HEIGHT): return None # Click outside board area
    col = int(x // SQUARE_SIZE)
    row = int(y // SQUARE_SIZE)
    center_x = col * SQUARE_SIZE + SQUARE_SIZE // 2
    center_y = row * SQUARE_SIZE + SQUARE_SIZE // 2
    # Check distance from click to intersection center
    dist_sq = (x - center_x)**2 + (y - center_y)**2
    margin_sq = (SQUARE_SIZE * CLICK_MARGIN_RATIO)**2
    if dist_sq < margin_sq:
        return row, col
    else:
        return None # Clicked too far from intersection

# --- Main Game Loop ---
def main():
    pygame.init()

    # --- Initialize Fonts ---
    piece_font_size = int(SQUARE_SIZE * 0.55)
    info_font_size_small = int(SQUARE_SIZE * 0.30)
    info_font_size_large = int(SQUARE_SIZE * 0.40)
    river_font_size = int(SQUARE_SIZE * 0.35)
    analysis_font_size = info_font_size_small # Use small size for analysis text/buttons

    # Load fonts safely
    piece_font = load_font(FONT_FILE_PATH, piece_font_size, FALLBACK_FONTS)
    info_font_small = load_font(FONT_FILE_PATH, info_font_size_small, FALLBACK_FONTS)
    info_font_large = load_font(FONT_FILE_PATH, info_font_size_large, FALLBACK_FONTS)
    river_font = load_font(FONT_FILE_PATH, river_font_size, FALLBACK_FONTS)
    analysis_font = load_font(FONT_FILE_PATH, analysis_font_size, FALLBACK_FONTS)

    # Critical Font Check
    if not piece_font: print("錯誤: 主要棋子字體無法載入，程式無法繼續。"); pygame.quit(); sys.exit()
    # Warnings for non-critical fonts (allow program to run with visual glitches)
    if not info_font_small: print("警告: 小信息字體無法載入。")
    if not info_font_large: print("警告: 大信息字體無法載入。")
    if not river_font: print("警告: 河流字體無法載入。")
    if not analysis_font: print("警告: 分析字體無法載入。")
    # ---

    # --- Pre-render Highlight Surfaces (for efficiency) ---
    selected_highlight_surf = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
    pygame.draw.circle(selected_highlight_surf, SELECTED_COLOR, (SQUARE_SIZE // 2, SQUARE_SIZE // 2), SQUARE_SIZE // 2 - 4, 3) # Draw as a thicker ring

    move_marker_radius = SQUARE_SIZE // 7 # Make move marker slightly larger
    move_highlight_surf = pygame.Surface((move_marker_radius * 2, move_marker_radius * 2), pygame.SRCALPHA)
    pygame.draw.circle(move_highlight_surf, HIGHLIGHT_COLOR, (move_marker_radius, move_marker_radius), move_marker_radius)
    # ---

    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Python Xiangqi - 象棋")
    clock = pygame.time.Clock()
    game = XiangqiGame()

    running = True
    save_btn_rect, load_btn_rect = None, None # Button rects for info panel
    analysis_buttons = {}                   # Button rects for analysis panel

    while running:
        # === Event Handling ===
        mouse_pos = pygame.mouse.get_pos() # Get mouse position once per frame

        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False

            # --- Mouse Button Down ---
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1: # Left click
                clicked_ui_element = False

                # 1. Check UI Buttons (priority over board)
                if game.game_state == GameState.ANALYSIS:
                    # Check Analysis Panel Buttons (Right)
                    for key, rect in analysis_buttons.items():
                        if rect and rect.collidepoint(mouse_pos):
                            game.analysis_navigate(key)
                            clicked_ui_element = True; break
                else: # Playing, Checkmate, Stalemate states
                    # Check Info Panel Buttons (Bottom)
                    if save_btn_rect and save_btn_rect.collidepoint(mouse_pos):
                        game.save_game()
                        clicked_ui_element = True
                    elif load_btn_rect and load_btn_rect.collidepoint(mouse_pos):
                        if game.load_game(): # Switches state if successful
                           pass # Button rects will be updated on redraw
                        clicked_ui_element = True

                # 2. Check Board Click (If playing and no UI clicked)
                if not clicked_ui_element and game.game_state == GameState.PLAYING:
                    coords = get_clicked_square(mouse_pos)
                    if coords:
                        r, c = coords
                        if game.selected_piece_pos == (r, c): # Clicked selected piece again
                             game.selected_piece_pos = None # Deselect
                             game.valid_moves = []
                        elif game.selected_piece_pos is not None: # Piece already selected
                            if (r, c) in game.valid_moves: # Clicked a valid move
                                game.make_move(r, c)
                            else: # Clicked somewhere else
                                # Try selecting if it's own piece, otherwise deselect
                                piece_at_click = game.board[r][c]
                                if piece_at_click is not None and get_piece_color(piece_at_click) == game.current_player:
                                     game.select_piece(r, c) # Select the new piece
                                else:
                                     game.selected_piece_pos = None # Deselect
                                     game.valid_moves = []
                        else: # No piece selected, try selecting
                            game.select_piece(r, c)
                    else: # Clicked on board but not near intersection
                        game.selected_piece_pos = None
                        game.valid_moves = []

            # --- Key Down ---
            if event.type == pygame.KEYDOWN:
                 # Analysis Navigation Hotkeys
                 if game.game_state == GameState.ANALYSIS:
                     if event.key == pygame.K_RIGHT: game.analysis_navigate('next')
                     elif event.key == pygame.K_LEFT: game.analysis_navigate('prev')
                     elif event.key in [pygame.K_UP, pygame.K_HOME]: game.analysis_navigate('first')
                     elif event.key in [pygame.K_DOWN, pygame.K_END]: game.analysis_navigate('last')
                 # Add other potential hotkeys here (e.g., save/load?)

        # === Game Logic Update ===
        if game.game_state == GameState.PLAYING: game.update_timers()

        # === Drawing ===
        screen.fill(INFO_BG_COLOR) # Fill entire background (covers previous frame)

        # Determine which board state to draw
        board_to_draw = game.analysis_board_state if game.game_state == GameState.ANALYSIS else game.board

        # --- Draw Board Area (Left Side) ---
        draw_board(screen, river_font)
        if board_to_draw: draw_pieces(screen, board_to_draw, piece_font)
        # Draw highlights only during active play
        if game.game_state == GameState.PLAYING:
            draw_highlights(screen, game.selected_piece_pos, game.valid_moves,
                            selected_highlight_surf, move_highlight_surf, move_marker_radius)

        # --- Draw Info Panel (Bottom) ---
        # Returns button rects (or None) - needed for click detection
        save_btn_rect, load_btn_rect = draw_info_panel(screen, game, info_font_small, info_font_large)

        # --- Draw Analysis Panel (Right Side) ---
        # Returns analysis button rects (or empty dict) - needed for click detection
        analysis_buttons = draw_right_panel(screen, game, info_font_small, info_font_large, analysis_font)

        # Update the full display surface
        pygame.display.flip()
        clock.tick(30) # Cap FPS

    pygame.quit()
    sys.exit()

# --- Execution Start ---
if __name__ == "__main__":
    # Font file check before starting Pygame
    if not os.path.exists(FONT_FILE_PATH) and not any(pygame.font.match_font(f) for f in FALLBACK_FONTS if f):
         print(f"錯誤: 指定字體文件 '{FONT_FILE_PATH}' 未找到，且系統中找不到任何有效的備選字體 {FALLBACK_FONTS}。")
         print("請確保字體文件存在或安裝至少一個備選字體。")
         # Optionally add a way to exit if no fonts are possible
         # sys.exit("Font loading error.")
    elif not os.path.exists(FONT_FILE_PATH):
         print(f"警告: 指定字體文件 '{FONT_FILE_PATH}' 未找到。將嘗試使用系統備選字體。")

    main()