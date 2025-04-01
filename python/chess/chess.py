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
        # print(f"成功載入字體: {font_path} (size {size})") # Optional: reduce console output
        return font
    except pygame.error as e:
        print(f"警告: 無法載入指定字體 '{font_path}': {e}")
        try:
            # Filter out None from fallback list if present
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

    def make_move(self, r_end, c_end):
        if not self.selected_piece_pos or (r_end, c_end) not in self.valid_moves:
            self.selected_piece_pos = None
            self.valid_moves = []
            return False
        r_start, c_start = self.selected_piece_pos
        piece = self.board[r_start][c_start]
        captured_piece = self.board[r_end][c_end]
        time_taken = time.time() - self.current_move_start_time
        notation = f"{PIECE_CHARS.get(piece, '?')}({r_start},{c_start})-({r_end},{c_end})"
        if captured_piece: notation += f"x{PIECE_CHARS.get(captured_piece, '?')}"
        self.move_log.append({
            "start": (r_start, c_start), "end": (r_end, c_end), "piece": piece,
            "captured": captured_piece, "notation": notation,
            "time": round(time_taken, 2), "player": self.current_player
        })
        self.board[r_end][c_end] = piece
        self.board[r_start][c_start] = EMPTY
        self.selected_piece_pos = None
        self.valid_moves = []
        self.last_move_time = time.time()
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
        r1, c1 = red_k_pos
        r2, c2 = black_k_pos
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
            original_piece_at_target = self.board[r_end][c_end]
            self.board[r_end][c_end] = piece
            self.board[r_start][c_start] = EMPTY
            is_self_check = self.is_in_check(player_color)
            is_king_exposed = self.kings_are_exposed()
            self.board[r_start][c_start] = piece
            self.board[r_end][c_end] = original_piece_at_target
            if not is_self_check and not is_king_exposed:
                legal_moves.append((r_end, c_end))
        return legal_moves

    def _add_raw_move(self, moves_list, r, c, current_board, own_color):
        """Helper to add a move if valid. Returns True if square is empty, False otherwise."""
        if is_valid_coord(r, c):
            target_piece = current_board[r][c]
            if target_piece is None:
                moves_list.append((r, c)); return True
            elif get_piece_color(target_piece) != own_color:
                moves_list.append((r, c)); return False # Capture block
            else: return False # Own piece block
        return False # Invalid coord block

    # Make sure indentation is correct here (aligned with other methods)
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
        elif piece_type == 'e':
            river_row = 4 if color == 'red' else 5
            for dr, dc in [(2,2),(2,-2),(-2,2),(-2,-2)]:
                re, ce = r_start+dr, c_start+dc
                if (color == 'red' and re > river_row) or (color == 'black' and re < river_row): continue
                rb, cb = r_start+dr//2, c_start+dc//2
                if is_valid_coord(rb, cb) and current_board[rb][cb] is None: self._add_raw_move(moves, re, ce, current_board, color)
        elif piece_type == 'h':
            for dr, dc, br, bc in [(-2,-1,-1,0),(-2,1,-1,0),(2,-1,1,0),(2,1,1,0), (-1,-2,0,-1),(1,-2,0,-1),(-1,2,0,1),(1,2,0,1)]:
                re, ce = r_start+dr, c_start+dc
                rb, cb = r_start+br, c_start+bc
                if is_valid_coord(rb, cb) and current_board[rb][cb] is None: self._add_raw_move(moves, re, ce, current_board, color)
        elif piece_type == 'r': # Rook - Corrected multi-line version
            for dr, dc in [(0,1),(0,-1),(1,0),(-1,0)]:
                rt, ct = r_start, c_start
                while True:
                    rt, ct = rt + dr, ct + dc
                    if not self._add_raw_move(moves, rt, ct, current_board, color):
                        break
        elif piece_type == 'c': # Cannon
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
                    else: # Have jumped
                        if target is not None:
                            if get_piece_color(target) != color: moves.append((rt, ct))
                            break # Stop after hitting second piece
                        # else: continue if empty after jump
        elif piece_type == 'p': # Pawn
            dr_fwd = -1 if color == 'red' else 1
            self._add_raw_move(moves, r_start+dr_fwd, c_start, current_board, color)
            if is_across_river(r_start, color):
                self._add_raw_move(moves, r_start, c_start+1, current_board, color)
                self._add_raw_move(moves, r_start, c_start-1, current_board, color)
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
            save_data = { "move_log": self.move_log, "initial_timers": {'red': DEFAULT_TIME, 'black': DEFAULT_TIME} }
            with open(filename, 'w', encoding='utf-8') as f: json.dump(save_data, f, indent=4, ensure_ascii=False)
            print(f"棋譜已儲存至 {filename}")
            self.status_message = f"棋譜已儲存至 {filename}"
        except IOError as e: print(f"儲存遊戲時發生 IO 錯誤: {e}"); self.status_message = f"儲存錯誤: {e}"
        except Exception as e: print(f"儲存遊戲時發生未預期錯誤: {e}"); self.status_message = "儲存遊戲時發生錯誤."

    def load_game(self, filename="xiangqi_save.json"):
        try:
            if not os.path.exists(filename): self.status_message = f"找不到檔案: {filename}"; return False
            with open(filename, 'r', encoding='utf-8') as f: save_data = json.load(f)
            self.__init__() # Reset game state
            self.move_log = save_data.get("move_log", [])
            if not self.move_log: print("警告: 載入的棋譜為空."); self.status_message = "載入的棋譜為空"
            # Transition to Analysis state
            self.game_state = GameState.ANALYSIS
            self.analysis_current_step = -1 # Start at beginning
            self.analysis_board_state = [row[:] for row in INITIAL_BOARD_SETUP] # Start with initial board
            # Set initial status message for analysis mode
            self.status_message = self._get_analysis_status() # Update status based on step -1
            print(f"從 {filename} 載入遊戲. 進入分析模式.")
            return True
        except FileNotFoundError: print(f"錯誤: 找不到存檔文件 '{filename}'"); self.status_message = f"找不到檔案: {filename}"; return False
        except json.JSONDecodeError as e: print(f"錯誤: 解析存檔文件 '{filename}' 失敗: {e}"); self.status_message = "載入失敗: 文件格式錯誤"; return False
        except IOError as e: print(f"載入遊戲時發生 IO 錯誤: {e}"); self.status_message = f"載入錯誤: {e}"; return False
        except Exception as e: print(f"載入遊戲時發生未預期錯誤: {e}"); self.status_message = "載入遊戲時發生錯誤."; self.__init__(); return False

    def analysis_navigate(self, direction):
        if self.game_state != GameState.ANALYSIS: return
        current_total_moves = len(self.move_log)
        target_step = self.analysis_current_step
        if direction == 'next': target_step = min(self.analysis_current_step + 1, current_total_moves - 1)
        elif direction == 'prev': target_step = max(self.analysis_current_step - 1, -1)
        elif direction == 'first': target_step = -1
        elif direction == 'last': target_step = current_total_moves - 1
        if target_step != self.analysis_current_step:
             self._reconstruct_board_to_step(target_step)
             self.status_message = self._get_analysis_status() # Update status after navigation

    def _reconstruct_board_to_step(self, target_step_index):
        self.analysis_board_state = [row[:] for row in INITIAL_BOARD_SETUP]
        current_internal_step = -1
        for i in range(target_step_index + 1):
            if i < len(self.move_log):
                 move_data = self.move_log[i]
                 # Make sure start/end keys exist before accessing
                 if "start" not in move_data or "end" not in move_data or "piece" not in move_data:
                      print(f"警告: 第 {i+1} 步棋譜數據不完整，跳過。")
                      continue
                 r_start, c_start = move_data["start"]; r_end, c_end = move_data["end"]; piece = move_data["piece"]
                 # Validate coordinates and piece match before applying
                 if is_valid_coord(r_start, c_start) and is_valid_coord(r_end, c_end) and \
                    self.analysis_board_state[r_start][c_start] == piece:
                     self.analysis_board_state[r_end][c_end] = piece
                     self.analysis_board_state[r_start][c_start] = EMPTY
                     current_internal_step = i
                 else:
                      print(f"警告: 在重建棋譜第 {i+1} 步時發現不一致 ({r_start},{c_start})={self.analysis_board_state[r_start][c_start]} vs {piece}。")
                      self.analysis_current_step = current_internal_step # Stop at last valid step
                      return # Stop reconstruction
            else:
                # This should not happen if target_step_index is calculated correctly
                print(f"警告: 嘗試重建棋步 {i+1}, 但棋譜只有 {len(self.move_log)} 步.")
                break
        self.analysis_current_step = current_internal_step # Update step after successful reconstruction

    def _get_analysis_status(self): # Generates the status string for display
        if self.game_state != GameState.ANALYSIS: return ""
        total_moves = len(self.move_log)
        current_move_num = self.analysis_current_step + 1
        if self.analysis_current_step == -1:
            return f"分析: 初始局面\n(0/{total_moves} 步)"
        elif 0 <= self.analysis_current_step < total_moves:
            move_data = self.move_log[self.analysis_current_step]
            notation = move_data.get("notation", "無記錄")
            time_taken = move_data.get("time", "?")
            player = "紅方" if move_data.get("player") == 'red' else "黑方"
            return f"分析: 第 {current_move_num}/{total_moves} 步 ({player})\n{notation}\n(思考: {time_taken}s)"
        elif self.analysis_current_step >= total_moves - 1 and total_moves > 0: # At the end
             move_data = self.move_log[total_moves - 1]
             notation = move_data.get("notation", "無記錄")
             player = "紅方" if move_data.get("player") == 'red' else "黑方"
             return f"分析: 第 {total_moves}/{total_moves} 步 ({player}) (終局)\n{notation}"
        else: # Error state or empty log
             return f"分析: 無棋步記錄\n(0/0 步)"

# --- Drawing Functions ---

# Simple text wrapping function
def draw_text_wrapped(surface, text, rect, font, color):
    lines = text.splitlines()
    y = rect.top
    line_spacing = font.get_linesize() + 2

    for line in lines:
        words = line.split(' ')
        current_line = ''
        line_rendered = False
        while words:
            test_word = words[0]
            test_line = current_line + test_word + ' '
            # Check if the test line fits
            if font.size(test_line)[0] < rect.width:
                current_line = test_line
                words.pop(0)
            else:
                # Word doesn't fit, render the current line (if any)
                if current_line:
                    image = font.render(current_line.strip(), True, color)
                    surface.blit(image, (rect.left, y))
                    y += line_spacing
                    current_line = ''
                    line_rendered = True
                # If the single word itself is too long, render it truncated or handle differently
                elif font.size(test_word)[0] >= rect.width:
                    # Render what fits of the long word
                    # This part needs refinement for better truncation
                    temp_word = test_word
                    while font.size(temp_word)[0] >= rect.width and len(temp_word)>0:
                        temp_word = temp_word[:-1]
                    if temp_word:
                         image = font.render(temp_word, True, color)
                         surface.blit(image, (rect.left, y))
                         y += line_spacing
                         line_rendered = True
                    words.pop(0) # Move past the long word
                    current_line = '' # Ensure reset
                else: # current_line is empty, but the word should fit
                     current_line = test_word + ' '
                     words.pop(0)

        # Render the last part of the line
        if current_line:
            image = font.render(current_line.strip(), True, color)
            surface.blit(image, (rect.left, y))
            y += line_spacing


# draw_board
def draw_board(screen, river_font):
    # Fill only the board background area on the left
    screen.fill(BOARD_COLOR_BG, (0, 0, BOARD_AREA_WIDTH, SCREEN_HEIGHT))
    board_rect = pygame.Rect(0, 0, BOARD_AREA_WIDTH, BOARD_AREA_HEIGHT)
    half_sq = SQUARE_SIZE // 2
    RIVER_TOP_ROW = 4; RIVER_BOTTOM_ROW = 5

    # Vertical Lines (Corrected for River)
    for c in range(BOARD_WIDTH):
        x = c * SQUARE_SIZE + half_sq
        pygame.draw.line(screen, LINE_COLOR_DARK, (x, half_sq), (x, RIVER_TOP_ROW * SQUARE_SIZE + half_sq), LINE_THICKNESS_NORMAL)
        pygame.draw.line(screen, LINE_COLOR_DARK, (x, RIVER_BOTTOM_ROW * SQUARE_SIZE + half_sq), (x, (BOARD_HEIGHT - 1) * SQUARE_SIZE + half_sq), LINE_THICKNESS_NORMAL)

    # Horizontal Lines
    for r in range(BOARD_HEIGHT):
        y = r * SQUARE_SIZE + half_sq; start_x = half_sq; end_x = (BOARD_WIDTH - 1) * SQUARE_SIZE + half_sq
        pygame.draw.line(screen, LINE_COLOR_DARK, (start_x, y), (end_x, y), LINE_THICKNESS_NORMAL)

    # Outer Border
    pygame.draw.rect(screen, LINE_COLOR_DARK, (half_sq, half_sq, (BOARD_WIDTH - 1) * SQUARE_SIZE, (BOARD_HEIGHT - 1) * SQUARE_SIZE), LINE_THICKNESS_OUTER)

    # Palaces
    palace_coords = [ ((3*SQUARE_SIZE+half_sq, half_sq), (5*SQUARE_SIZE+half_sq, 2*SQUARE_SIZE+half_sq)), ((5*SQUARE_SIZE+half_sq, half_sq), (3*SQUARE_SIZE+half_sq, 2*SQUARE_SIZE+half_sq)), ((3*SQUARE_SIZE+half_sq, 7*SQUARE_SIZE+half_sq), (5*SQUARE_SIZE+half_sq, 9*SQUARE_SIZE+half_sq)), ((5*SQUARE_SIZE+half_sq, 7*SQUARE_SIZE+half_sq), (3*SQUARE_SIZE+half_sq, 9*SQUARE_SIZE+half_sq)), ]
    for start, end in palace_coords: pygame.draw.line(screen, LINE_COLOR_DARK, start, end, LINE_THICKNESS_NORMAL)

    # River Text
    if river_font:
        texts = [("楚", 1.5), ("河", 2.5), ("漢", 5.5), ("界", 6.5)]
        river_y = RIVER_TOP_ROW * SQUARE_SIZE + half_sq + (SQUARE_SIZE / 2)
        for text, col_pos in texts:
             try:
                 surf = river_font.render(text, True, RIVER_TEXT_COLOR)
                 text_x = col_pos * SQUARE_SIZE + half_sq
                 screen.blit(surf, surf.get_rect(center=(text_x, river_y)))
             except Exception as e: print(f"Error rendering river text '{text}': {e}") # Catch font render errors

    # Cannon/Pawn Markers
    pawn_marks_c, pawn_marks_r = [0, 2, 4, 6, 8], [3, 6]
    cannon_marks_c, cannon_marks_r = [1, 7], [2, 7]
    mark_len, mark_offset = SQUARE_SIZE // 9, SQUARE_SIZE // 12
    all_marks_coords = set()
    [(all_marks_coords.add((c, r))) for r in pawn_marks_r for c in pawn_marks_c]
    [(all_marks_coords.add((c, r))) for r in cannon_marks_r for c in cannon_marks_c]
    for c, r in all_marks_coords:
         x, y = c * SQUARE_SIZE + half_sq, r * SQUARE_SIZE + half_sq
         corner_markers = { (-1, -1): [(-mark_len, 0), (0, -mark_len)], ( 1, -1): [( mark_len, 0), (0, -mark_len)], (-1,  1): [(-mark_len, 0), (0,  mark_len)], ( 1,  1): [( mark_len, 0), (0,  mark_len)] }
         for (cdx, cdy), lines in corner_markers.items():
             if c == 0 and cdx < 0: continue
             if c == BOARD_WIDTH - 1 and cdx > 0: continue
             corner_x = x + cdx * mark_offset; corner_y = y + cdy * mark_offset
             for (ldx, ldy) in lines:
                 end_x = corner_x + ldx; end_y = corner_y + ldy
                 pygame.draw.line(screen, LINE_COLOR_DARK, (corner_x, corner_y), (end_x, end_y), LINE_THICKNESS_NORMAL)

# draw_pieces
def draw_pieces(screen, board, piece_font):
    if not piece_font: return
    radius = SQUARE_SIZE // 2 - 6
    for r in range(BOARD_HEIGHT):
        for c in range(BOARD_WIDTH):
            piece = board[r][c]
            if piece is not None:
                char = PIECE_CHARS.get(piece, "?")
                color = RED_COLOR if get_piece_color(piece) == 'red' else BLACK_COLOR
                center_x = c * SQUARE_SIZE + SQUARE_SIZE // 2
                center_y = r * SQUARE_SIZE + SQUARE_SIZE // 2
                try:
                    pygame.draw.circle(screen, PIECE_BG_COLOR, (center_x, center_y), radius)
                    pygame.draw.circle(screen, LINE_COLOR_DARK, (center_x, center_y), radius, PIECE_BORDER_WIDTH)
                    text_surf = piece_font.render(char, True, color)
                    screen.blit(text_surf, text_surf.get_rect(center=(center_x, center_y)))
                except Exception as e: print(f"Error drawing piece {piece} at ({r},{c}): {e}") # Catch drawing errors


# draw_highlights
def draw_highlights(screen, selected_pos, valid_moves, selected_surf, move_surf, marker_radius):
     if selected_pos:
        r, c = selected_pos
        center_x = c * SQUARE_SIZE + SQUARE_SIZE // 2
        center_y = r * SQUARE_SIZE + SQUARE_SIZE // 2
        screen.blit(selected_surf, (center_x - selected_surf.get_width() // 2, center_y - selected_surf.get_height() // 2))
     for r, c in valid_moves:
        center_x = c * SQUARE_SIZE + SQUARE_SIZE // 2
        center_y = r * SQUARE_SIZE + SQUARE_SIZE // 2
        screen.blit(move_surf, (center_x - marker_radius, center_y - marker_radius))

# draw_info_panel (Below board)
def draw_info_panel(screen, game, font_small, font_large):
    save_btn_rect, load_btn_rect = None, None
    if game.game_state != GameState.ANALYSIS:
        panel_rect = pygame.Rect(0, BOARD_AREA_HEIGHT, BOARD_AREA_WIDTH, INFO_PANEL_HEIGHT)
        pygame.draw.rect(screen, INFO_BG_COLOR, panel_rect)
        if not font_small or not font_large: return save_btn_rect, load_btn_rect
        try: # Timers
            rm, rs = divmod(int(game.timers['red']), 60)
            bm, bs = divmod(int(game.timers['black']), 60)
            t_red = font_small.render(f"紅方: {rm:02d}:{rs:02d}", True, RED_COLOR)
            t_black = font_small.render(f"黑方: {bm:02d}:{bs:02d}", True, BLACK_COLOR)
            screen.blit(t_red, (panel_rect.left + 20, panel_rect.top + 15))
            screen.blit(t_black, (panel_rect.right - t_black.get_width() - 20, panel_rect.top + 15))
        except Exception as e: print(f"Error rendering timers: {e}")
        try: # Status Message
            status_surf = font_large.render(game.status_message, True, BLACK_COLOR)
            screen.blit(status_surf, status_surf.get_rect(center=(panel_rect.centerx, panel_rect.top + 55)))
        except Exception as e: print(f"Error rendering status message: {e}")
        # Buttons
        btn_h, btn_w, btn_padding = 35, 90, 15
        btn_y = panel_rect.bottom - btn_h - 10
        save_btn_rect = pygame.Rect(panel_rect.left + 20, btn_y, btn_w, btn_h)
        load_btn_rect = pygame.Rect(save_btn_rect.right + btn_padding, btn_y, btn_w, btn_h)
        try:
            pygame.draw.rect(screen, BUTTON_COLOR, save_btn_rect, border_radius=6)
            save_txt = font_small.render("儲存棋譜", True, BUTTON_TEXT_COLOR)
            screen.blit(save_txt, save_txt.get_rect(center=save_btn_rect.center))
            pygame.draw.rect(screen, BUTTON_COLOR, load_btn_rect, border_radius=6)
            load_txt = font_small.render("載入棋譜", True, BUTTON_TEXT_COLOR)
            screen.blit(load_txt, load_txt.get_rect(center=load_btn_rect.center))
        except Exception as e: print(f"Error rendering buttons: {e}")
    return save_btn_rect, load_btn_rect

# draw_right_panel
def draw_right_panel(screen, game, font_small, font_large, analysis_font):
    buttons = {}
    panel_rect = pygame.Rect(BOARD_AREA_WIDTH, 0, ANALYSIS_PANEL_WIDTH, SCREEN_HEIGHT)
    pygame.draw.rect(screen, INFO_BG_COLOR, panel_rect) # Background

    if game.game_state == GameState.ANALYSIS:
        if not analysis_font or not font_small: return buttons

        # Display Analysis Status Info (using status message from game object)
        status_text = game.status_message # Use the message updated by navigation
        status_rect = pygame.Rect(panel_rect.left + 15, panel_rect.top + 20, panel_rect.width - 30, 150)
        try:
            draw_text_wrapped(screen, status_text, status_rect, font_small, BLACK_COLOR)
        except Exception as e: print(f"Error rendering analysis status: {e}")

        # Draw Navigation Buttons (Vertically)
        button_texts = {"first":"<< 首步", "prev":"< 上一步", "next":"下一步 >", "last":"末步 >>"}
        btn_w, btn_h, v_space = 150, 40, 15
        # Adjust starting Y based on where text wrapping ended, or fixed position
        start_y = status_rect.bottom + 30 # Start buttons below text area
        current_y = start_y
        try:
            for key, txt in button_texts.items():
                btn_x = panel_rect.centerx - btn_w // 2
                rect = pygame.Rect(btn_x, current_y, btn_w, btn_h)
                # Add bounds check
                if rect.bottom > panel_rect.bottom - 10: # Check if button goes off panel
                    print("Warning: Not enough space for all analysis buttons.")
                    break # Stop drawing buttons if out of space
                pygame.draw.rect(screen, BUTTON_COLOR, rect, border_radius=6)
                surf = analysis_font.render(txt, True, BUTTON_TEXT_COLOR)
                screen.blit(surf, surf.get_rect(center=rect.center))
                buttons[key] = rect
                current_y += btn_h + v_space
        except Exception as e: print(f"Error rendering analysis buttons: {e}")
    return buttons

# get_clicked_square
def get_clicked_square(pos):
    x, y = pos
    if not (0 <= x < BOARD_AREA_WIDTH and 0 <= y < BOARD_AREA_HEIGHT): return None
    margin = SQUARE_SIZE * CLICK_MARGIN_RATIO
    col = int(x // SQUARE_SIZE)
    row = int(y // SQUARE_SIZE)
    center_x = col * SQUARE_SIZE + SQUARE_SIZE // 2
    center_y = row * SQUARE_SIZE + SQUARE_SIZE // 2
    if abs(x - center_x) < margin and abs(y - center_y) < margin: return row, col
    else: return None

# --- Main Game Loop ---
def main():
    pygame.init()

    # --- Initialize Fonts ---
    piece_font_size = int(SQUARE_SIZE * 0.55)
    info_font_size_small = int(SQUARE_SIZE * 0.30)
    info_font_size_large = int(SQUARE_SIZE * 0.40)
    river_font_size = int(SQUARE_SIZE * 0.35)
    analysis_font_size = info_font_size_small

    # Load fonts safely
    piece_font = load_font(FONT_FILE_PATH, piece_font_size, FALLBACK_FONTS)
    info_font_small = load_font(FONT_FILE_PATH, info_font_size_small, FALLBACK_FONTS)
    info_font_large = load_font(FONT_FILE_PATH, info_font_size_large, FALLBACK_FONTS)
    river_font = load_font(FONT_FILE_PATH, river_font_size, FALLBACK_FONTS)
    analysis_font = load_font(FONT_FILE_PATH, analysis_font_size, FALLBACK_FONTS)

    # Critical Font Check
    if not piece_font: print("錯誤: 主要棋子字體無法載入，程式無法繼續。"); pygame.quit(); sys.exit()
    # Warnings for non-critical fonts
    if not info_font_small: print("警告: 小信息字體無法載入。")
    if not info_font_large: print("警告: 大信息字體無法載入。")
    if not river_font: print("警告: 河流字體無法載入。")
    if not analysis_font: print("警告: 分析字體無法載入。")
    # ---

    # --- Pre-render Highlight Surfaces ---
    selected_highlight_surf = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
    pygame.draw.circle(selected_highlight_surf, SELECTED_COLOR, (SQUARE_SIZE // 2, SQUARE_SIZE // 2), SQUARE_SIZE // 2 - 3)
    move_marker_radius = SQUARE_SIZE // 8
    move_highlight_surf = pygame.Surface((move_marker_radius * 2, move_marker_radius * 2), pygame.SRCALPHA)
    pygame.draw.circle(move_highlight_surf, HIGHLIGHT_COLOR, (move_marker_radius, move_marker_radius), move_marker_radius)
    # ---

    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Python Xiangqi - 象棋 (右側面板)")
    clock = pygame.time.Clock()
    game = XiangqiGame()

    running = True
    save_btn_rect, load_btn_rect = None, None
    analysis_buttons = {}

    while running:
        # === Event Handling ===
        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False

            # --- Mouse Click Handling ---
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                pos = pygame.mouse.get_pos()
                clicked_ui_element = False

                # 1. Check UI Buttons based on state
                if game.game_state == GameState.ANALYSIS:
                    # Check RIGHT PANEL buttons
                    for key, rect in analysis_buttons.items():
                        if rect and rect.collidepoint(pos): # Check if rect exists
                            game.analysis_navigate(key)
                            clicked_ui_element = True; break
                else: # PLAYING, CHECKMATE, STALEMATE
                    # Check BOTTOM PANEL buttons
                    if save_btn_rect and save_btn_rect.collidepoint(pos):
                        game.save_game(); clicked_ui_element = True
                    elif load_btn_rect and load_btn_rect.collidepoint(pos):
                        if game.load_game(): # Load switches state to ANALYSIS
                            analysis_buttons = {} # Reset analysis buttons
                            save_btn_rect, load_btn_rect = None, None # Clear bottom buttons
                        clicked_ui_element = True

                # 2. Check Board Click (Only if playing and no UI clicked)
                if not clicked_ui_element and game.game_state == GameState.PLAYING:
                    coords = get_clicked_square(pos)
                    if coords:
                        r, c = coords
                        if game.selected_piece_pos is None: game.select_piece(r, c)
                        else:
                            if (r, c) in game.valid_moves: game.make_move(r, c)
                            elif game.board[r][c] is not None and get_piece_color(game.board[r][c]) == game.current_player:
                                game.select_piece(r, c)
                            else: game.selected_piece_pos = None; game.valid_moves = []
                    else: game.selected_piece_pos = None; game.valid_moves = []

            # --- Keyboard Handling (Analysis Mode Navigation) ---
            if event.type == pygame.KEYDOWN and game.game_state == GameState.ANALYSIS:
                 if event.key == pygame.K_RIGHT: game.analysis_navigate('next')
                 elif event.key == pygame.K_LEFT: game.analysis_navigate('prev')
                 elif event.key in [pygame.K_UP, pygame.K_HOME]: game.analysis_navigate('first')
                 elif event.key in [pygame.K_DOWN, pygame.K_END]: game.analysis_navigate('last')

        # === Game Logic Update ===
        if game.game_state == GameState.PLAYING: game.update_timers()

        # === Drawing ===
        screen.fill(INFO_BG_COLOR) # Fill entire background with panel color first

        # Determine board state to draw
        board_to_draw = game.analysis_board_state if game.game_state == GameState.ANALYSIS else game.board

        # Draw Left Side (Board Area)
        draw_board(screen, river_font) # draw_board now fills its own BG
        if board_to_draw: draw_pieces(screen, board_to_draw, piece_font)
        if game.game_state == GameState.PLAYING:
            draw_highlights(screen, game.selected_piece_pos, game.valid_moves,
                            selected_highlight_surf, move_highlight_surf, move_marker_radius)

        # Draw Bottom Panel (Below Board - content only drawn if not analysis)
        save_btn_rect, load_btn_rect = draw_info_panel(screen, game, info_font_small, info_font_large)

        # Draw Right Panel (Background always, content only if analysis)
        analysis_buttons = draw_right_panel(screen, game, info_font_small, info_font_large, analysis_font)

        # Update the display
        pygame.display.flip()
        clock.tick(30) # Limit FPS

    pygame.quit()
    sys.exit()

# --- Execution Start ---
if __name__ == "__main__":
    # Check for font file before starting Pygame
    if not os.path.exists(FONT_FILE_PATH):
        print(f"錯誤: 主要字體文件未找到於 '{FONT_FILE_PATH}'")
        print("請確認 'Noto Sans SC' 資料夾 (包含 NotoSansSC-VariableFont_wght.ttf 文件)")
        print("位於此 Python 腳本所在的相同目錄中，或者修改 FONT_FILE_PATH 常量。")
    else:
        # Ensure fonts are loaded before Pygame display initialization if needed elsewhere
        # Or handle font loading errors more gracefully inside main()
        main()