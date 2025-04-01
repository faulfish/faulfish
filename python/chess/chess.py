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
MOVE_LIST_HIGHLIGHT_COLOR = (255, 10, 10) # Bright red for current move in list

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
_NUM_CHARS = {1: '一', 2: '二', 3: '三', 4: '四', 5: '五', 6: '六', 7: '七', 8: '八', 9: '九'}
_RED_FILES = {0: '九', 1: '八', 2: '七', 3: '六', 4: '五', 5: '四', 6: '三', 7: '二', 8: '一'}
_BLACK_FILES = {0: '1', 1: '2', 2: '3', 3: '4', 4: '5', 5: '6', 6: '7', 7: '8', 8: '9'}

def get_file_notation(col, color):
    if color == 'red':
        return _RED_FILES.get(col, '?')
    else: # black
        return _BLACK_FILES.get(col, '?')

def get_step_notation(num, color):
    abs_num = abs(num)
    if color == 'red':
        return _NUM_CHARS.get(abs_num, str(abs_num))
    else: # black
        return str(abs_num)
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
    return (0 <= r <= 2) or (7 <= r <= 9)

def get_palace_limits(color):
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
        """Initializes or resets the game state."""
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

        # Reset analysis specific variables
        self.analysis_board_state = None # No need for separate board when starting fresh
        self.analysis_current_step = -1

    def new_game(self):
        """Resets the game to the initial state for a new match."""
        self.__init__() # Call the initializer to reset everything
        print("新局開始!") # Optional console feedback

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

    def _find_ambiguous_pieces(self, board, r_end, c_end, piece_to_move, start_pos_moving, color):
        """Finds if other pieces of the same type could also legally move to the target square."""
        r_start_moving, c_start_moving = start_pos_moving
        piece_char_lower = piece_to_move.lower()
        ambiguous_movers = []
        original_selected = self.selected_piece_pos # Backup state
        original_valid = self.valid_moves

        # Use the *live* board state (self.board) for checking potential moves of *other* pieces
        # because get_valid_moves_for_piece relies on the current self.board for its checks.
        live_board = self.board

        for r in range(BOARD_HEIGHT):
            for c in range(BOARD_WIDTH):
                piece = live_board[r][c] # Check piece on the live board
                # Check same type, same color, BUT DIFFERENT starting position
                if piece is not None and piece.lower() == piece_char_lower and get_piece_color(piece) == color and (r,c) != (r_start_moving, c_start_moving):
                     # Temporarily select this other piece to check its *legal* moves on the live board
                     self.selected_piece_pos = (r,c)
                     potential_moves = self.get_valid_moves_for_piece(r, c) # Checks self.board
                     if (r_end, c_end) in potential_moves:
                         ambiguous_movers.append((r, c))

        self.selected_piece_pos = original_selected # Restore state
        self.valid_moves = original_valid
        return ambiguous_movers


    def get_algebraic_notation(self, board_before_move, start_pos, end_pos, player_color):
        """Generates standard Chinese algebraic notation for a move."""
        r_start, c_start = start_pos
        r_end, c_end = end_pos
        piece = board_before_move[r_start][c_start] # Use the board state *before* the move

        if piece is None: return "錯誤"

        piece_char_display = PIECE_CHARS.get(piece, '?')
        piece_type = piece.lower()
        dr = r_end - r_start
        dc = c_end - c_start

        # Determine Direction
        direction = ''
        if dc == 0: direction = '進' if (player_color == 'red' and dr < 0) or (player_color == 'black' and dr > 0) else '退'
        elif dr == 0: direction = '平'
        else: direction = '進' if (player_color == 'red' and dr < 0) or (player_color == 'black' and dr > 0) else '退'

        # Determine Target Value
        target_val = ''
        if direction == '平': target_val = get_file_notation(c_end, player_color)
        else:
            if piece_type in ['k', 'a', 'e', 'h']: target_val = get_file_notation(c_end, player_color)
            elif piece_type in ['r', 'c', 'p']: target_val = get_step_notation(dr, player_color)

        # Handle Ambiguity and Pawns
        first_part = piece_char_display
        needs_start_file = False

        if piece_type == 'p':
            needs_start_file = True
        else:
            # Pass the start pos of the piece actually moving to the checker
            potential_movers = self._find_ambiguous_pieces(board_before_move, r_end, c_end, piece, start_pos, player_color)

            if potential_movers:
                all_ambiguous_files = {pos[1] for pos in potential_movers}
                all_ambiguous_files.add(c_start)

                if len(all_ambiguous_files) > 1:
                    needs_start_file = True
                elif piece_type in ['r', 'h', 'c']:
                    needs_start_file = True

        if needs_start_file:
            first_part = piece_char_display + get_file_notation(c_start, player_color)

        return f"{first_part}{direction}{target_val}"


    def make_move(self, r_end, c_end):
        if not self.selected_piece_pos or (r_end, c_end) not in self.valid_moves:
            self.selected_piece_pos = None
            self.valid_moves = []
            return False

        r_start, c_start = self.selected_piece_pos
        piece_to_move = self.board[r_start][c_start]
        captured_piece = self.board[r_end][c_end]
        time_taken = time.time() - self.current_move_start_time

        # Generate notation BEFORE board update using the state BEFORE move
        board_state_before_move = [row[:] for row in self.board]
        notation = self.get_algebraic_notation(board_state_before_move, (r_start, c_start), (r_end, c_end), self.current_player)

        # Update Log
        self.move_log.append({
            "start": (r_start, c_start), "end": (r_end, c_end), "piece": piece_to_move,
            "captured": captured_piece, "notation": notation,
            "time": round(time_taken, 1), # Store time with 1 decimal place maybe? Or keep 2? Let's keep 2 for data, format later.
            "time": round(time_taken, 2),
            "player": self.current_player
        })

        # Update Board
        self.board[r_end][c_end] = piece_to_move
        self.board[r_start][c_start] = EMPTY
        self.selected_piece_pos = None
        self.valid_moves = []
        self.last_move_time = time.time()

        # Check End Conditions
        opponent_color = 'black' if self.current_player == 'red' else 'red'
        winner_name = "紅方" if self.current_player == 'red' else "黑方"
        if self.is_checkmate(opponent_color):
            self.game_state = GameState.CHECKMATE
            self.status_message = f"將死! {winner_name} 勝!"
        elif self.is_stalemate(opponent_color):
            self.game_state = GameState.STALEMATE
            self.status_message = "欠行! 和棋!"
        else:
            self.switch_player()
            if self.is_in_check(self.current_player):
                 player_name = "紅方" if self.current_player == 'red' else "黑方"
                 self.status_message = f"{player_name} 回合 (將軍!)"
        return True

    def is_in_check(self, player_color, current_board=None):
        board_to_check = current_board if current_board else self.board
        king_pos = get_king_pos(board_to_check, player_color)
        if not king_pos: return False
        opponent_color = 'black' if player_color == 'red' else 'red'
        for r in range(BOARD_HEIGHT):
            for c in range(BOARD_WIDTH):
                piece = board_to_check[r][c]
                if piece is not None and get_piece_color(piece) == opponent_color:
                    raw_moves = self._get_raw_valid_moves(r, c, board_to_check)
                    if king_pos in raw_moves: return True
        return False

    def does_move_result_in_check(self, start_pos, end_pos, player_color):
         r_start, c_start = start_pos
         r_end, c_end = end_pos
         piece = self.board[r_start][c_start]
         captured = self.board[r_end][c_end]
         self.board[r_end][c_end] = piece
         self.board[r_start][c_start] = EMPTY
         in_check = self.is_in_check(player_color)
         self.board[r_start][c_start] = piece
         self.board[r_end][c_end] = captured
         return in_check

    def kings_are_exposed(self, current_board=None):
        board_to_check = current_board if current_board else self.board
        red_k_pos = get_king_pos(board_to_check, 'red')
        black_k_pos = get_king_pos(board_to_check, 'black')
        if not red_k_pos or not black_k_pos: return False
        r1, c1 = red_k_pos; r2, c2 = black_k_pos
        if c1 != c2: return False
        for r in range(min(r1, r2) + 1, max(r1, r2)):
            if board_to_check[r][c1] is not None: return False
        return True

    def get_valid_moves_for_piece(self, r_start, c_start):
        piece = self.board[r_start][c_start]
        if piece is None: return []
        player_color = get_piece_color(piece)
        raw_moves = self._get_raw_valid_moves(r_start, c_start, self.board)
        legal_moves = []
        for r_end, c_end in raw_moves:
            original_target = self.board[r_end][c_end]
            self.board[r_end][c_end] = piece
            self.board[r_start][c_start] = EMPTY
            is_self_check = self.is_in_check(player_color)
            is_king_exposed = self.kings_are_exposed()
            self.board[r_start][c_start] = piece
            self.board[r_end][c_end] = original_target
            if not is_self_check and not is_king_exposed:
                legal_moves.append((r_end, c_end))
        return legal_moves

    def _add_raw_move(self, moves_list, r, c, current_board, own_color):
        if is_valid_coord(r, c):
            target_piece = current_board[r][c]
            if target_piece is None:
                moves_list.append((r, c)); return True
            elif get_piece_color(target_piece) != own_color:
                moves_list.append((r, c)); return False
            else: return False
        return False

    def _get_raw_valid_moves(self, r_start, c_start, current_board):
        moves = []
        piece = current_board[r_start][c_start]
        if piece is None: return []
        color = get_piece_color(piece)
        piece_type = piece.lower()

        if piece_type == 'k':
            pr_min, pr_max = get_palace_limits(color)
            for dr, dc in [(0,1),(0,-1),(1,0),(-1,0)]:
                re, ce = r_start+dr, c_start+dc
                if pr_min <= re <= pr_max and 3 <= ce <= 5: self._add_raw_move(moves, re, ce, current_board, color)
        elif piece_type == 'a':
            pr_min, pr_max = get_palace_limits(color)
            for dr, dc in [(1,1),(1,-1),(-1,1),(-1,-1)]:
                re, ce = r_start+dr, c_start+dc
                if pr_min <= re <= pr_max and 3 <= ce <= 5: self._add_raw_move(moves, re, ce, current_board, color)
        elif piece_type == 'e': # CORRECTED
            for dr, dc in [(2,2),(2,-2),(-2,2),(-2,-2)]:
                re, ce = r_start+dr, c_start+dc
                if not is_valid_coord(re, ce): continue
                if (color == 'red' and re <= 4) or (color == 'black' and re >= 5): continue
                rb, cb = r_start + dr // 2, c_start + dc // 2
                if is_valid_coord(rb, cb) and current_board[rb][cb] is None:
                    self._add_raw_move(moves, re, ce, current_board, color)
        elif piece_type == 'h':
            for dr, dc, br, bc in [(-2,-1,-1,0),(-2,1,-1,0),(2,-1,1,0),(2,1,1,0),
                                   (-1,-2,0,-1),(1,-2,0,-1),(-1,2,0,1),(1,2,0,1)]:
                re, ce = r_start+dr, c_start+dc
                rb, cb = r_start+br, c_start+bc
                if is_valid_coord(rb, cb) and current_board[rb][cb] is None:
                    self._add_raw_move(moves, re, ce, current_board, color)
        elif piece_type == 'r':
            for dr, dc in [(0,1),(0,-1),(1,0),(-1,0)]:
                rt, ct = r_start, c_start
                while True:
                    rt, ct = rt + dr, ct + dc
                    if not self._add_raw_move(moves, rt, ct, current_board, color): break
        elif piece_type == 'c':
            for dr, dc in [(0,1),(0,-1),(1,0),(-1,0)]:
                rt, ct = r_start, c_start
                jumped = False
                while True:
                    rt, ct = rt + dr, ct + dc
                    if not is_valid_coord(rt, ct): break
                    target = current_board[rt][ct]
                    if not jumped:
                        if target is None: moves.append((rt, ct))
                        else: jumped = True
                    else:
                        if target is not None:
                            if get_piece_color(target) != color: moves.append((rt, ct))
                            break
        elif piece_type == 'p':
            dr_fwd = -1 if color == 'red' else 1
            self._add_raw_move(moves, r_start + dr_fwd, c_start, current_board, color)
            if is_across_river(r_start, color):
                self._add_raw_move(moves, r_start, c_start + 1, current_board, color)
                self._add_raw_move(moves, r_start, c_start - 1, current_board, color)
        return moves

    def get_all_valid_moves(self, player_color):
        all_moves = []
        for r in range(BOARD_HEIGHT):
            for c in range(BOARD_WIDTH):
                piece = self.board[r][c]
                if piece is not None and get_piece_color(piece) == player_color:
                    valid_piece_moves = self.get_valid_moves_for_piece(r, c)
                    if valid_piece_moves: all_moves.extend([((r, c), move) for move in valid_piece_moves])
        return all_moves

    def is_checkmate(self, player_color):
        return self.is_in_check(player_color) and not self.get_all_valid_moves(player_color)

    def is_stalemate(self, player_color):
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
            save_data = { "move_log": self.move_log }
            with open(filename, 'w', encoding='utf-8') as f: json.dump(save_data, f, indent=4, ensure_ascii=False)
            print(f"棋譜已儲存至 {filename}")
            self.status_message = f"棋譜已儲存至 {filename}"
        except Exception as e: print(f"儲存遊戲時發生錯誤: {e}"); self.status_message = "儲存錯誤"

    def load_game(self, filename="xiangqi_save.json"):
        try:
            if not os.path.exists(filename): self.status_message = f"找不到檔案: {filename}"; return False
            with open(filename, 'r', encoding='utf-8') as f: save_data = json.load(f)
            self.__init__() # Reset before loading
            self.move_log = save_data.get("move_log", [])
            if not self.move_log: self.status_message = "載入的棋譜為空" # Set status but proceed
            self.game_state = GameState.ANALYSIS
            self.analysis_current_step = -1
            self.analysis_board_state = [row[:] for row in INITIAL_BOARD_SETUP]
            print(f"從 {filename} 載入遊戲. 進入分析模式.")
            return True
        except Exception as e: print(f"載入遊戲時發生錯誤: {e}"); self.status_message = "載入錯誤"; self.__init__(); return False

    def analysis_navigate(self, direction):
        if self.game_state != GameState.ANALYSIS: return
        current_total_moves = len(self.move_log)
        if current_total_moves == 0: return
        target_step = self.analysis_current_step
        if direction == 'next': target_step = min(self.analysis_current_step + 1, current_total_moves - 1)
        elif direction == 'prev': target_step = max(self.analysis_current_step - 1, -1)
        elif direction == 'first': target_step = -1
        elif direction == 'last': target_step = current_total_moves - 1
        if target_step != self.analysis_current_step:
             self._reconstruct_board_to_step(target_step)

    def _reconstruct_board_to_step(self, target_step_index):
        self.analysis_board_state = [row[:] for row in INITIAL_BOARD_SETUP]
        current_internal_step = -1
        for i in range(target_step_index + 1):
            if i < len(self.move_log):
                 move_data = self.move_log[i]
                 if not all(k in move_data for k in ["start", "end", "piece"]):
                      print(f"警告: 第 {i+1} 步棋譜數據不完整，跳過。")
                      continue
                 r_start, c_start = move_data["start"]; r_end, c_end = move_data["end"]; piece_moved = move_data["piece"]
                 if not (is_valid_coord(r_start, c_start) and is_valid_coord(r_end, c_end)):
                      print(f"警告: 第 {i+1} 步座標無效，停止重建。")
                      self.analysis_current_step = current_internal_step; return
                 piece_on_board = self.analysis_board_state[r_start][c_start]
                 if piece_on_board != piece_moved:
                      print(f"警告: 第 {i+1} 步棋子不一致 ({piece_on_board} vs {piece_moved})，停止重建。")
                      self.analysis_current_step = current_internal_step; return
                 self.analysis_board_state[r_end][c_end] = piece_moved
                 self.analysis_board_state[r_start][c_start] = EMPTY
                 current_internal_step = i
            else: break
        self.analysis_current_step = current_internal_step

# --- Drawing Functions ---
def draw_text_wrapped(surface, text, rect, font, color):
    # Simplified version for move list (assumes single line per move)
    if font is None: return rect.top
    lines = text.splitlines()
    y = rect.top
    line_spacing = font.get_linesize() + 1
    for line in lines:
         if y + line_spacing > rect.bottom: break # Stop if exceeding rect
         try:
             image = font.render(line, True, color)
             surface.blit(image, (rect.left, y))
             y += line_spacing
         except Exception as e: print(f"Render Error: {e}")
    return y

def draw_board(screen, river_font):
    screen.fill(BOARD_COLOR_BG, (0, 0, BOARD_AREA_WIDTH, BOARD_AREA_HEIGHT))
    half_sq = SQUARE_SIZE // 2; RIVER_TOP_ROW = 4; RIVER_BOTTOM_ROW = 5
    # Vert Lines
    for c in range(BOARD_WIDTH):
        x = c * SQUARE_SIZE + half_sq
        pygame.draw.line(screen, LINE_COLOR_DARK, (x, half_sq), (x, RIVER_TOP_ROW * SQUARE_SIZE + half_sq), LINE_THICKNESS_NORMAL)
        pygame.draw.line(screen, LINE_COLOR_DARK, (x, RIVER_BOTTOM_ROW * SQUARE_SIZE + half_sq), (x, (BOARD_HEIGHT - 1) * SQUARE_SIZE + half_sq), LINE_THICKNESS_NORMAL)
    # Horiz Lines
    for r in range(BOARD_HEIGHT):
        y = r * SQUARE_SIZE + half_sq
        pygame.draw.line(screen, LINE_COLOR_DARK, (half_sq, y), ((BOARD_WIDTH - 1) * SQUARE_SIZE + half_sq, y), LINE_THICKNESS_NORMAL)
    # Border
    pygame.draw.rect(screen, LINE_COLOR_DARK, (half_sq, half_sq, (BOARD_WIDTH - 1) * SQUARE_SIZE, (BOARD_HEIGHT - 1) * SQUARE_SIZE), LINE_THICKNESS_OUTER)
    # Palaces
    pygame.draw.line(screen, LINE_COLOR_DARK, (3*SQUARE_SIZE+half_sq, half_sq), (5*SQUARE_SIZE+half_sq, 2*SQUARE_SIZE+half_sq), LINE_THICKNESS_NORMAL)
    pygame.draw.line(screen, LINE_COLOR_DARK, (5*SQUARE_SIZE+half_sq, half_sq), (3*SQUARE_SIZE+half_sq, 2*SQUARE_SIZE+half_sq), LINE_THICKNESS_NORMAL)
    pygame.draw.line(screen, LINE_COLOR_DARK, (3*SQUARE_SIZE+half_sq, 7*SQUARE_SIZE+half_sq), (5*SQUARE_SIZE+half_sq, 9*SQUARE_SIZE+half_sq), LINE_THICKNESS_NORMAL)
    pygame.draw.line(screen, LINE_COLOR_DARK, (5*SQUARE_SIZE+half_sq, 7*SQUARE_SIZE+half_sq), (3*SQUARE_SIZE+half_sq, 9*SQUARE_SIZE+half_sq), LINE_THICKNESS_NORMAL)
    # River Text
    if river_font:
        texts = [("楚", 1.5), ("河", 2.5), ("漢", 5.5), ("界", 6.5)]
        river_y = RIVER_TOP_ROW * SQUARE_SIZE + SQUARE_SIZE
        for text, col_pos in texts:
             try:
                 surf = river_font.render(text, True, RIVER_TEXT_COLOR)
                 text_x = (col_pos + 0.5) * SQUARE_SIZE
                 screen.blit(surf, surf.get_rect(center=(int(text_x), int(river_y))))
             except Exception as e: print(f"Render Error: River Text '{text}' - {e}")
    # Markers
    p_marks_c, p_marks_r = [0, 2, 4, 6, 8], [3, 6]
    c_marks_c, c_marks_r = [1, 7], [2, 7]
    mark_len, mark_off = SQUARE_SIZE // 9, SQUARE_SIZE // 12
    marks_coords = set((c, r) for r in p_marks_r for c in p_marks_c) | set((c, r) for r in c_marks_r for c in c_marks_c)
    for c, r in marks_coords:
         x, y = c*SQUARE_SIZE+half_sq, r*SQUARE_SIZE+half_sq
         corners = {(-1,-1):[(-mark_len,0),(0,-mark_len)],(1,-1):[(mark_len,0),(0,-mark_len)],
                    (-1, 1):[(-mark_len,0),(0, mark_len)],(1, 1):[(mark_len,0),(0, mark_len)]}
         for (cdx, cdy), lines in corners.items():
             if (c==0 and cdx<0) or (c==BOARD_WIDTH-1 and cdx>0) or \
                (r==0 and cdy<0) or (r==BOARD_HEIGHT-1 and cdy>0): continue
             cx, cy = x + cdx*mark_off, y + cdy*mark_off
             for (ldx, ldy) in lines:
                 try:
                      pygame.draw.line(screen, LINE_COLOR_DARK, (cx, cy), (cx+ldx, cy+ldy), LINE_THICKNESS_NORMAL)
                 except Exception as e: print(f"Render Error: Marker Line at ({c},{r}) - {e}")


def draw_pieces(screen, board, piece_font):
    if not piece_font: return
    radius = SQUARE_SIZE // 2 - 6
    for r in range(BOARD_HEIGHT):
        for c in range(BOARD_WIDTH):
            piece = board[r][c]
            if piece:
                char = PIECE_CHARS.get(piece, "?")
                color = RED_COLOR if get_piece_color(piece) == 'red' else BLACK_COLOR
                cx, cy = c*SQUARE_SIZE+SQUARE_SIZE//2, r*SQUARE_SIZE+SQUARE_SIZE//2
                try:
                    pygame.draw.circle(screen, PIECE_BG_COLOR, (cx, cy), radius)
                    pygame.draw.circle(screen, color, (cx, cy), radius, PIECE_BORDER_WIDTH)
                    surf = piece_font.render(char, True, color)
                    screen.blit(surf, surf.get_rect(center=(cx, cy)))
                except Exception as e: print(f"Render Error: Piece '{piece}' at ({r},{c}) - {e}")

def draw_highlights(screen, selected_pos, valid_moves, selected_surf, move_surf, marker_radius):
     try:
         if selected_pos:
            r, c = selected_pos; cx, cy = c*SQUARE_SIZE+SQUARE_SIZE//2, r*SQUARE_SIZE+SQUARE_SIZE//2
            screen.blit(selected_surf, selected_surf.get_rect(center=(cx, cy)))
         for r, c in valid_moves:
            cx, cy = c*SQUARE_SIZE+SQUARE_SIZE//2, r*SQUARE_SIZE+SQUARE_SIZE//2
            screen.blit(move_surf, move_surf.get_rect(center=(cx, cy)))
     except Exception as e: print(f"Render Error: Highlights - {e}")

# --- REVISED draw_info_panel ---
def draw_info_panel(screen, game, font_small, font_large):
    save_btn_rect, load_btn_rect, new_game_btn_rect = None, None, None
    panel_rect = pygame.Rect(0, BOARD_AREA_HEIGHT, BOARD_AREA_WIDTH, INFO_PANEL_HEIGHT)

    # 1. Draw Panel Background (Always)
    try:
        pygame.draw.rect(screen, INFO_BG_COLOR, panel_rect)
    except Exception as e: print(f"Render Error: Info Panel BG - {e}"); return None, None, None

    # 2. Draw Timers and Status Message (Only when NOT analyzing)
    if game.game_state != GameState.ANALYSIS:
        if font_small and font_large: # Check if fonts are available
            try: # Timers
                rm, rs = divmod(int(game.timers['red']), 60)
                bm, bs = divmod(int(game.timers['black']), 60)
                t_red = font_small.render(f"紅方: {rm:02d}:{rs:02d}", True, RED_COLOR)
                t_black = font_small.render(f"黑方: {bm:02d}:{bs:02d}", True, BLACK_COLOR)
                screen.blit(t_red, (panel_rect.left + 20, panel_rect.top + 15))
                screen.blit(t_black, (panel_rect.right - t_black.get_width() - 20, panel_rect.top + 15))
            except Exception as e: print(f"Render Error: Timers - {e}")

            try: # Status Message
                status_surf = font_large.render(game.status_message, True, BLACK_COLOR)
                screen.blit(status_surf, status_surf.get_rect(center=(panel_rect.centerx, panel_rect.top + 55))) # Adjusted Y pos
            except Exception as e: print(f"Render Error: Status Message - {e}")

    # 3. Draw Buttons (Always, if font_small exists)
    if font_small:
        btn_h, btn_w, btn_padding = 30, 85, 10
        btn_y = panel_rect.bottom - btn_h - 10 # Position buttons near bottom

        # Calculate starting X to roughly center the 3 buttons
        total_button_width = btn_w * 3 + btn_padding * 2
        start_x = panel_rect.centerx - total_button_width // 2

        # Button 1: Save
        save_btn_rect = pygame.Rect(start_x, btn_y, btn_w, btn_h)
        try:
            pygame.draw.rect(screen, BUTTON_COLOR, save_btn_rect, border_radius=6)
            save_txt = font_small.render("儲存棋譜", True, BUTTON_TEXT_COLOR)
            screen.blit(save_txt, save_txt.get_rect(center=save_btn_rect.center))
        except Exception as e: print(f"Render Error: Save Button - {e}")

        # Button 2: Load
        load_btn_rect = pygame.Rect(save_btn_rect.right + btn_padding, btn_y, btn_w, btn_h)
        try:
            pygame.draw.rect(screen, BUTTON_COLOR, load_btn_rect, border_radius=6)
            load_txt = font_small.render("載入棋譜", True, BUTTON_TEXT_COLOR)
            screen.blit(load_txt, load_txt.get_rect(center=load_btn_rect.center))
        except Exception as e: print(f"Render Error: Load Button - {e}")

        # Button 3: New Game
        new_game_btn_rect = pygame.Rect(load_btn_rect.right + btn_padding, btn_y, btn_w, btn_h)
        try:
            pygame.draw.rect(screen, BUTTON_COLOR, new_game_btn_rect, border_radius=6)
            new_game_txt = font_small.render("新對局", True, BUTTON_TEXT_COLOR)
            screen.blit(new_game_txt, new_game_txt.get_rect(center=new_game_btn_rect.center))
        except Exception as e: print(f"Render Error: New Game Button - {e}")

    return save_btn_rect, load_btn_rect, new_game_btn_rect
# --- END REVISED draw_info_panel ---


# --- REVISED draw_right_panel ---
def draw_right_panel(screen, game, font_small, font_large, analysis_font):
    buttons = {}
    panel_rect = pygame.Rect(BOARD_AREA_WIDTH, 0, ANALYSIS_PANEL_WIDTH, SCREEN_HEIGHT)
    try:
        pygame.draw.rect(screen, INFO_BG_COLOR, panel_rect)
    except Exception as e: print(f"Render Error: Right Panel BG - {e}"); return {}

    # Define areas
    top_padding = 15; button_area_height = 80 # Adjusted for 2 rows
    move_list_top_padding = 10
    button_area_rect = pygame.Rect(panel_rect.left, panel_rect.top + top_padding, panel_rect.width, button_area_height)
    move_list_area_rect = pygame.Rect( panel_rect.left, button_area_rect.bottom + move_list_top_padding, panel_rect.width, panel_rect.height - button_area_rect.bottom - move_list_top_padding - 10 )

    # --- Draw Buttons at the Top (Only in Analysis) ---
    if game.game_state == GameState.ANALYSIS:
        if not analysis_font: return buttons

        btn_w, btn_h, h_space, v_space = 90, 30, 15, 10
        start_x = panel_rect.centerx - (btn_w * 2 + h_space) // 2
        current_y = button_area_rect.top

        # Row 1: First, Prev
        try:
            rect_first = pygame.Rect(start_x, current_y, btn_w, btn_h); buttons['first'] = rect_first
            pygame.draw.rect(screen, BUTTON_COLOR, rect_first, border_radius=6)
            surf_first = analysis_font.render("<< 首步", True, BUTTON_TEXT_COLOR)
            screen.blit(surf_first, surf_first.get_rect(center=rect_first.center))

            rect_prev = pygame.Rect(rect_first.right + h_space, current_y, btn_w, btn_h); buttons['prev'] = rect_prev
            pygame.draw.rect(screen, BUTTON_COLOR, rect_prev, border_radius=6)
            surf_prev = analysis_font.render("< 上一步", True, BUTTON_TEXT_COLOR)
            screen.blit(surf_prev, surf_prev.get_rect(center=rect_prev.center))
        except Exception as e: print(f"Render Error: Analysis Buttons Row 1 - {e}")

        current_y += btn_h + v_space

        # Row 2: Next, Last
        try:
            rect_next = pygame.Rect(start_x, current_y, btn_w, btn_h); buttons['next'] = rect_next
            pygame.draw.rect(screen, BUTTON_COLOR, rect_next, border_radius=6)
            surf_next = analysis_font.render("下一步 >", True, BUTTON_TEXT_COLOR)
            screen.blit(surf_next, surf_next.get_rect(center=rect_next.center))

            rect_last = pygame.Rect(rect_next.right + h_space, current_y, btn_w, btn_h); buttons['last'] = rect_last
            pygame.draw.rect(screen, BUTTON_COLOR, rect_last, border_radius=6)
            surf_last = analysis_font.render("末步 >>", True, BUTTON_TEXT_COLOR)
            screen.blit(surf_last, surf_last.get_rect(center=rect_last.center))
        except Exception as e: print(f"Render Error: Analysis Buttons Row 2 - {e}")

        # --- Draw Move List Below Buttons ---
        if not font_small: return buttons

        list_x_padding = 10
        list_render_area = move_list_area_rect.inflate(-list_x_padding * 2, -10)

        try:
            line_height = font_small.get_linesize() + 1
            if line_height <= 0: raise ValueError("Font error")
            max_visible_lines = list_render_area.height // line_height

            if max_visible_lines > 0 and game.move_log:
                total_moves = len(game.move_log)
                current_step = game.analysis_current_step

                # Calculate display window start index
                display_start_index = 0
                if total_moves > max_visible_lines:
                    target_center_line = max(0, current_step)
                    display_start_index = max(0, target_center_line - max_visible_lines // 2)
                    display_start_index = min(display_start_index, total_moves - max_visible_lines)

                # Iterate and draw visible moves
                for i in range(max_visible_lines):
                    move_index = display_start_index + i
                    if move_index >= total_moves: break

                    move_data = game.move_log[move_index]
                    notation = move_data.get("notation", "???")
                    player_char = "紅" if move_data.get("player") == 'red' else "黑"
                    move_time = move_data.get("time", None)

                    time_str = ""
                    if move_time is not None:
                        try: time_str = f" ({move_time:.1f}s)" # Format time
                        except (TypeError, ValueError): time_str = " (?s)"

                    move_text = f"{move_index + 1}. ({player_char}) {notation}{time_str}" # Add time

                    is_current = (move_index == current_step)
                    text_color = MOVE_LIST_HIGHLIGHT_COLOR if is_current else BLACK_COLOR

                    surf = font_small.render(move_text, True, text_color)
                    render_y = list_render_area.top + i * line_height

                    # Basic text truncation if too wide
                    max_width = list_render_area.width
                    if surf.get_width() > max_width:
                         try:
                             original_len = len(move_text)
                             # Estimate chars to keep, minus a bit for ellipsis
                             keep_chars = max(1, int(original_len * max_width / surf.get_width()) - 2)
                             surf = font_small.render(move_text[:keep_chars] + "..", True, text_color)
                         except Exception as e: print(f"Render Error: Truncating Text - {e}") # Fallback if error

                    screen.blit(surf, (list_render_area.left, render_y))

            elif not game.move_log:
                 empty_text = font_small.render("棋譜為空", True, BLACK_COLOR)
                 screen.blit(empty_text, empty_text.get_rect(center=list_render_area.center))

        except Exception as e: print(f"Error rendering move list: {e}")

    else: # Not in analysis mode - Draw Title
        if font_large:
            try:
                title_surf = font_large.render("象棋", True, BUTTON_COLOR)
                screen.blit(title_surf, title_surf.get_rect(center=panel_rect.center))
            except Exception as e: print(f"Render Error: Title - {e}")

    return buttons
# --- END REVISED draw_right_panel ---


def get_clicked_square(pos):
    x, y = pos
    if not (0 <= x < BOARD_AREA_WIDTH and 0 <= y < BOARD_AREA_HEIGHT): return None
    col, row = int(x // SQUARE_SIZE), int(y // SQUARE_SIZE)
    cx, cy = col*SQUARE_SIZE+SQUARE_SIZE//2, row*SQUARE_SIZE+SQUARE_SIZE//2
    if (x - cx)**2 + (y - cy)**2 < (SQUARE_SIZE * CLICK_MARGIN_RATIO)**2:
        return row, col
    return None

# --- Main Game Loop ---
def main():
    pygame.init()
    # --- Font Loading ---
    pfs = int(SQUARE_SIZE*0.55); ifs_s = int(SQUARE_SIZE*0.30); ifs_l = int(SQUARE_SIZE*0.40)
    rfs = int(SQUARE_SIZE*0.35); afs = int(SQUARE_SIZE*0.30)
    pf = load_font(FONT_FILE_PATH, pfs, FALLBACK_FONTS); ifs = load_font(FONT_FILE_PATH, ifs_s, FALLBACK_FONTS)
    ifl = load_font(FONT_FILE_PATH, ifs_l, FALLBACK_FONTS); rf = load_font(FONT_FILE_PATH, rfs, FALLBACK_FONTS)
    af = load_font(FONT_FILE_PATH, afs, FALLBACK_FONTS)
    if not pf: print("CRITICAL FONT ERROR"); pygame.quit(); sys.exit()

    # --- Highlight Surfaces ---
    sel_surf = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
    pygame.draw.circle(sel_surf, SELECTED_COLOR, (SQUARE_SIZE//2, SQUARE_SIZE//2), SQUARE_SIZE//2 - 4, 3)
    mr = SQUARE_SIZE // 7; mov_surf = pygame.Surface((mr*2, mr*2), pygame.SRCALPHA)
    pygame.draw.circle(mov_surf, HIGHLIGHT_COLOR, (mr, mr), mr)

    # --- Setup ---
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Python Xiangqi - 象棋")
    clock = pygame.time.Clock()
    game = XiangqiGame()
    running = True
    # Button rects from info panel (initially None)
    save_btn_rect, load_btn_rect, new_game_btn_rect = None, None, None
    # Button rects from analysis panel (initially empty)
    analysis_buttons = {}

    while running:
        # === Event Handling ===
        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False

            # --- Mouse Click ---
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_pos = event.pos
                clicked_ui = False

                # 1. Check Bottom Panel Buttons (Always check these first)
                if save_btn_rect and save_btn_rect.collidepoint(mouse_pos):
                    game.save_game(); clicked_ui = True
                elif load_btn_rect and load_btn_rect.collidepoint(mouse_pos):
                    game.load_game(); clicked_ui = True # load_game changes state
                elif new_game_btn_rect and new_game_btn_rect.collidepoint(mouse_pos):
                    game.new_game(); clicked_ui = True # new_game resets state

                # 2. Check Right Panel Analysis Buttons (Only if Analysis and no bottom button clicked)
                if not clicked_ui and game.game_state == GameState.ANALYSIS:
                    for key, rect in analysis_buttons.items():
                        if rect and rect.collidepoint(mouse_pos):
                            game.analysis_navigate(key) # Handles 'first', 'prev', etc.
                            clicked_ui = True; break

                # 3. Check Board Click (Only if Playing and no UI clicked)
                if not clicked_ui and game.game_state == GameState.PLAYING:
                    coords = get_clicked_square(mouse_pos)
                    if coords:
                        r, c = coords
                        if game.selected_piece_pos == (r, c): game.selected_piece_pos = None; game.valid_moves = []
                        elif game.selected_piece_pos:
                            if (r, c) in game.valid_moves: game.make_move(r, c)
                            else: game.select_piece(r, c)
                        else: game.select_piece(r, c)
                    else: game.selected_piece_pos = None; game.valid_moves = []

            # --- Keyboard ---
            if event.type == pygame.KEYDOWN:
                if game.game_state == GameState.ANALYSIS:
                     if event.key == pygame.K_RIGHT: game.analysis_navigate('next')
                     elif event.key == pygame.K_LEFT: game.analysis_navigate('prev')
                     elif event.key in [pygame.K_UP, pygame.K_HOME]: game.analysis_navigate('first')
                     elif event.key in [pygame.K_DOWN, pygame.K_END]: game.analysis_navigate('last')

        # === Game Logic Update ===
        if game.game_state == GameState.PLAYING: game.update_timers()

        # === Drawing ===
        screen.fill(INFO_BG_COLOR)
        board_to_draw = game.analysis_board_state if game.game_state == GameState.ANALYSIS else game.board

        # --- Draw Board Area ---
        draw_board(screen, rf)
        if board_to_draw: draw_pieces(screen, board_to_draw, pf)
        if game.game_state == GameState.PLAYING: draw_highlights(screen, game.selected_piece_pos, game.valid_moves, sel_surf, mov_surf, mr)

        # --- Draw Bottom Panel (returns its button rects) ---
        save_btn_rect, load_btn_rect, new_game_btn_rect = draw_info_panel(screen, game, ifs, ifl)

        # --- Draw Right Panel (returns analysis button rects) ---
        analysis_buttons = draw_right_panel(screen, game, ifs, ifl, af)

        # --- Update Display ---
        pygame.display.flip()
        clock.tick(30)

    pygame.quit()
    sys.exit()

# --- Execution Start ---
if __name__ == "__main__":
    if not os.path.exists(FONT_FILE_PATH) and not any(pygame.font.match_font(f) for f in FALLBACK_FONTS if f):
         print(f"錯誤: 字體文件 '{FONT_FILE_PATH}' 未找到，且無備選字體。")
    elif not os.path.exists(FONT_FILE_PATH):
         print(f"警告: 字體文件 '{FONT_FILE_PATH}' 未找到，嘗試備選字體。")
    main()