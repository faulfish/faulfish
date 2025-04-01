# -*- coding: utf-8 -*-
import pygame
import sys
import time
import json
import os
from enum import Enum, auto

# --- Enums ---
class GameState(Enum):
    PLAYING = auto()
    PAUSED = auto()
    BLACK_WINS = auto()
    WHITE_WINS = auto()
    DRAW = auto()
    ANALYSIS = auto()

# --- Constants ---
BOARD_SIZE = 15
SQUARE_SIZE = 40
MARGIN = 30
GRID_WIDTH = (BOARD_SIZE - 1) * SQUARE_SIZE
GRID_HEIGHT = (BOARD_SIZE - 1) * SQUARE_SIZE
INFO_HEIGHT = 80
ANALYSIS_WIDTH = 180
BOARD_AREA_WIDTH = GRID_WIDTH + 2 * MARGIN
BOARD_AREA_HEIGHT = GRID_HEIGHT + 2 * MARGIN
WIDTH = BOARD_AREA_WIDTH + ANALYSIS_WIDTH
HEIGHT = BOARD_AREA_HEIGHT + INFO_HEIGHT

# Colors
BOARD_COLOR = (210, 180, 140)
LINE_COLOR = (50, 50, 50)
BLACK_STONE = (10, 10, 10)
WHITE_STONE = (245, 245, 245)
INFO_BG_COLOR = (200, 200, 200)
ANALYSIS_BG_COLOR = (215, 215, 215)
INFO_TEXT_COLOR = (0, 0, 0)
HIGHLIGHT_COLOR = (255, 0, 0)
HOVER_BLACK_COLOR = (10, 10, 10, 120)
HOVER_WHITE_COLOR = (245, 245, 245, 120)
BUTTON_COLOR = (100, 100, 180)
BUTTON_TEXT_COLOR = (255, 255, 255)
MOVE_LIST_HIGHLIGHT_COLOR = (0, 0, 200)

# Players & Game Elements
EMPTY = 0
BLACK = 1
WHITE = 2
EDGE = -1

# Directions
DIRECTIONS = [(0, 1), (1, 0), (1, 1), (1, -1)]

# Game Settings
DEFAULT_TIME_LIMIT = 10 * 60

# --- Helper Functions ---
def is_on_board(r, c):
    return 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE

def get_board_coords(screen_x, screen_y):
    if not (MARGIN // 2 < screen_x < BOARD_AREA_WIDTH - MARGIN // 2 and
            MARGIN // 2 < screen_y < BOARD_AREA_HEIGHT - MARGIN // 2):
        return None
    col = round((screen_x - MARGIN) / SQUARE_SIZE)
    row = round((screen_y - MARGIN) / SQUARE_SIZE)
    center_x = MARGIN + col * SQUARE_SIZE
    center_y = MARGIN + row * SQUARE_SIZE
    click_radius_sq = (SQUARE_SIZE * 0.45) ** 2
    if (screen_x - center_x)**2 + (screen_y - center_y)**2 <= click_radius_sq:
        if 0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE:
            return row, col
    return None

def format_time(seconds):
    if seconds < 0: seconds = 0
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes:02d}:{secs:02d}"

def load_best_font(size, prefer_cjk=True):
     preferred = ["SimHei", "Microsoft YaHei", "PingFang SC", "sans-serif"]
     try:
         font_name = None
         if prefer_cjk:
             font_name = pygame.font.match_font(preferred)
         if font_name: return pygame.font.Font(font_name, size)
         else: return pygame.font.Font(None, size)
     except Exception as e:
         print(f"Font loading error: {e}. Using default Pygame font.")
         try: return pygame.font.Font(None, size)
         except Exception as final_e: print(f"FATAL: Could not load even default font: {final_e}"); return None

# --- Game Logic Class ---
class RenjuGame:
    def __init__(self):
        self.board = [[EMPTY for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
        self.current_player = BLACK
        self.game_state = GameState.PLAYING
        self.last_move = None
        self.move_count = 0
        self.status_message = "黑方回合"
        self.move_log = []
        self.timers = {BLACK: DEFAULT_TIME_LIMIT, WHITE: DEFAULT_TIME_LIMIT}
        self.last_update_time = time.time()
        self.current_move_start_time = self.last_update_time
        self.pause_start_time = None
        self.accumulated_pause_time = 0.0
        self.analysis_step = -1
        self.analysis_board = [[EMPTY for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]

    def restart_game(self): self.__init__()
    def pause_game(self):
        if self.game_state == GameState.PLAYING:
            self.game_state = GameState.PAUSED; self.pause_start_time = time.time()
            elapsed = self.pause_start_time - self.last_update_time
            self.timers[self.current_player] = max(0, self.timers[self.current_player] - elapsed)
            self.status_message = "遊戲暫停 (按鈕恢復)"; print("Game Paused")
    def resume_game(self):
        if self.game_state == GameState.PAUSED and self.pause_start_time is not None:
            pause_duration = time.time() - self.pause_start_time
            self.accumulated_pause_time += pause_duration; self.last_update_time = time.time()
            self.game_state = GameState.PLAYING; self.pause_start_time = None
            player_name = "黑方" if self.current_player == BLACK else "白方"
            self.status_message = f"{player_name} 回合"; print(f"Game Resumed (Paused for {pause_duration:.1f}s)")
        elif self.game_state == GameState.PAUSED:
            self.game_state = GameState.PLAYING; self.last_update_time = time.time(); print("Warning: Resuming game with inconsistent pause state.")
    def update_timers(self):
        if self.game_state != GameState.PLAYING: return
        now = time.time(); elapsed = now - self.last_update_time; self.last_update_time = now
        self.timers[self.current_player] = max(0, self.timers[self.current_player] - elapsed)
        if self.timers[self.current_player] <= 0:
            loser = self.current_player; winner = WHITE if loser == BLACK else BLACK
            self.game_state = GameState.BLACK_WINS if winner == BLACK else GameState.WHITE_WINS
            winner_name = "黑方" if winner == BLACK else "白方"; self.status_message = f"超時! {winner_name} 勝!"; print("Timeout!")
    def make_move(self, r, c):
        if self.game_state != GameState.PLAYING: self.status_message = "遊戲已結束或暫停"; return False
        if not is_on_board(r, c) or self.board[r][c] != EMPTY: self.status_message = "無效位置!"; return False
        player = self.current_player
        if player == BLACK: # Check forbidden first
            self.board[r][c] = player # Place temp
            is_win = self.check_win_condition(r, c, player)
            forbidden = None if is_win else self.check_forbidden_move(r, c)
            self.board[r][c] = EMPTY # Remove temp
            if forbidden: self.status_message = f"禁手: {forbidden}! 請選他處."; print(f"Forbidden attempt: {forbidden} at ({r},{c})"); return False
        self.board[r][c] = player; self.last_move = (r, c); self.move_count += 1
        thinking_time = time.time() - self.current_move_start_time
        self.move_log.append({"player": player, "row": r, "col": c, "time": round(thinking_time, 1), "pause": round(self.accumulated_pause_time, 1)})
        self.accumulated_pause_time = 0.0
        if self.check_win_condition(r, c, player):
            self.game_state = GameState.BLACK_WINS if player == BLACK else GameState.WHITE_WINS
            winner = "黑方" if player == BLACK else "白方"; self.status_message = f"{winner} 連珠五子勝!"; print(f"Win for {winner}"); return True
        if self.move_count == BOARD_SIZE * BOARD_SIZE: self.game_state = GameState.DRAW; self.status_message = "平局!"; print("Draw game"); return True
        self.switch_player(); return True
    def switch_player(self):
        self.current_player = WHITE if self.current_player == BLACK else BLACK
        player_name = "黑方" if self.current_player == BLACK else "白方"; self.status_message = f"{player_name} 回合"
        now = time.time(); self.last_update_time = now; self.current_move_start_time = now
    def count_line(self, r, c, player, dr_dc):
        dr, dc = dr_dc; count = 1; open_ends = 0
        cr, cc = r + dr, c + dc
        while is_on_board(cr, cc) and self.board[cr][cc] == player: count += 1; cr += dr; cc += dc
        if is_on_board(cr, cc) and self.board[cr][cc] == EMPTY: open_ends += 1
        cr, cc = r - dr, c - dc
        while is_on_board(cr, cc) and self.board[cr][cc] == player: count += 1; cr -= dr; cc -= dc
        if is_on_board(cr, cc) and self.board[cr][cc] == EMPTY: open_ends += 1
        return count, open_ends
    def check_win_condition(self, r, c, player):
        for dr_dc in DIRECTIONS:
            count, _ = self.count_line(r, c, player, dr_dc)
            if player == BLACK and count == 5: return True
            if player == WHITE and count >= 5: return True
        return False
    def check_forbidden_move(self, r, c):
        player = BLACK
        for dr_dc in DIRECTIONS: # Check Overline
            count, _ = self.count_line(r, c, player, dr_dc);
            if count >= 6: return "長連"
        open_threes, fours = 0, 0
        for dr_dc in DIRECTIONS:
            is_three, is_open_three = self.check_specific_line(r, c, player, dr_dc, 3)
            if is_open_three: open_threes += 1
            is_four, _ = self.check_specific_line(r, c, player, dr_dc, 4)
            if is_four: fours += 1
        if open_threes >= 2: return "三三"
        if fours >= 2: return "四四"
        return None

    # --- CORRECTED check_specific_line ---
    def check_specific_line(self, r, c, player, dr_dc, target_count):
        """Helper for forbidden checks. Assumes stone at (r,c) is placed."""
        dr, dc = dr_dc
        seq_fwd, seq_bwd = [player], [player] # Start with the placed stone

        # Scan forward direction
        for i in range(1, target_count + 2):
            cr, cc = r + i * dr, c + i * dc
            stone = self.board[cr][cc] if is_on_board(cr, cc) else EDGE
            seq_fwd.append(stone)
            # Optimization: stop scanning early if blocked, edge, or too long
            if stone == EDGE or stone != player or len(seq_fwd) > target_count + 1:
                 break # Correctly indented break

        # Scan backward direction
        for i in range(1, target_count + 2):
            cr, cc = r - i * dr, c - i * dc
            stone = self.board[cr][cc] if is_on_board(cr, cc) else EDGE
            seq_bwd.insert(0, stone) # Insert at beginning
            # Optimization
            if stone == EDGE or stone != player or len(seq_bwd) > target_count + 1:
                 break # Correctly indented break

        full_seq = seq_bwd[:-1] + seq_fwd # Combine sequences around the placed stone
        new_stone_idx = len(seq_bwd) - 1 # Index of the just-placed stone in full_seq

        count_found = False
        is_open_line = False
        # Check all possible sub-sequences of target_count length
        for i in range(len(full_seq) - target_count + 1):
            sub_seq = full_seq[i : i + target_count]
            if all(s == player for s in sub_seq): # Found a line of target_count
                # Ensure the newly placed stone is part of this specific line segment
                if i <= new_stone_idx < i + target_count:
                    count_found = True
                    if target_count == 3: # Check for Open Three specifically
                        # Check left end (_OOO)
                        left_open = i > 0 and full_seq[i - 1] == EMPTY
                        # Check right end (OOO_)
                        right_open = (i + target_count) < len(full_seq) and full_seq[i + target_count] == EMPTY
                        if left_open and right_open:
                            is_open_line = True
                            break # Found an open three, no need to check further patterns in this direction
        return count_found, is_open_line
    # --- END CORRECTED check_specific_line ---

    def save_game(self, filename="renju_save.json"):
        try: save_data={"move_log": self.move_log}; f=open(filename,'w',encoding='utf-8'); json.dump(save_data,f,indent=2); f.close(); self.status_message=f"棋譜已存檔"; print(f"Saved to {filename}")
        except Exception as e: self.status_message="存檔失敗!"; print(f"Error saving: {e}")
    def load_game(self, filename="renju_save.json"):
        try:
            if not os.path.exists(filename): self.status_message=f"找不到檔案"; return False
            f=open(filename,'r',encoding='utf-8'); save_data=json.load(f); f.close()
            self.restart_game(); self.move_log=save_data.get("move_log",[])
            self.status_message="棋譜載入-分析模式" if self.move_log else "載入空棋譜"
            self.game_state=GameState.ANALYSIS; self.analysis_step=-1; self._reconstruct_board_to_step(self.analysis_step)
            print(f"Loaded from {filename}. Analysis mode."); return True
        except Exception as e: self.restart_game(); self.status_message="載入失敗!"; print(f"Error loading: {e}"); return False
    def analysis_navigate(self, direction):
        if self.game_state!=GameState.ANALYSIS or not self.move_log: return
        target=self.analysis_step; total=len(self.move_log)
        if direction=='next': target=min(self.analysis_step+1, total-1)
        elif direction=='prev': target=max(self.analysis_step-1, -1)
        elif direction=='first': target=-1
        elif direction=='last': target=total-1
        if target!=self.analysis_step: self.analysis_step=target; self._reconstruct_board_to_step(self.analysis_step)
    def _reconstruct_board_to_step(self, target_idx):
        self.analysis_board = [[EMPTY for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]; self.last_move = None
        for i in range(target_idx + 1):
             if i<len(self.move_log):
                 data=self.move_log[i]
                 try: r,c,p=data['row'],data['col'],data['player'];
                 except KeyError: print(f"Warn: Bad data step {i+1}"); break
                 if is_on_board(r,c): self.analysis_board[r][c] = p;
                 else: print(f"Warn: Invalid coord step {i+1}"); break
                 if i==target_idx: self.last_move=(r,c)

# --- Drawing Functions ---
def draw_grid(screen):
    try:
        screen.fill(BOARD_COLOR)
        for i in range(BOARD_SIZE): # Lines
            pygame.draw.line(screen,LINE_COLOR,(MARGIN+i*SQUARE_SIZE,MARGIN),(MARGIN+i*SQUARE_SIZE,MARGIN+GRID_HEIGHT))
            pygame.draw.line(screen,LINE_COLOR,(MARGIN,MARGIN+i*SQUARE_SIZE),(MARGIN+GRID_WIDTH,MARGIN+i*SQUARE_SIZE))
        stars=[(3,3),(3,11),(11,3),(11,11),(7,7)]; r=5 # Star points
        for y,x in stars: pygame.draw.circle(screen,LINE_COLOR,(MARGIN+x*SQUARE_SIZE,MARGIN+y*SQUARE_SIZE),r)
    except Exception as e: print(f"Error drawing grid: {e}")

def draw_stones(screen, board, last_move, game_state):
    if game_state == GameState.PAUSED: return
    try:
        rad = SQUARE_SIZE // 2 - 3
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                p = board[r][c]
                if p != EMPTY:
                    ctr=(MARGIN+c*SQUARE_SIZE,MARGIN+r*SQUARE_SIZE); clr=BLACK_STONE if p==BLACK else WHITE_STONE
                    pygame.draw.circle(screen, clr, ctr, rad)
        if last_move: r,c=last_move; ctr=(MARGIN+c*SQUARE_SIZE,MARGIN+r*SQUARE_SIZE); pygame.draw.circle(screen,HIGHLIGHT_COLOR,ctr,rad//3)
    except Exception as e: print(f"Error drawing stones: {e}")

def draw_hover_preview(screen, hover_pos, current_player, board):
    if hover_pos is None: return
    try:
        r,c = hover_pos
        if is_on_board(r,c) and board[r][c] == EMPTY:
            ctr=(MARGIN+c*SQUARE_SIZE,MARGIN+r*SQUARE_SIZE); rad=SQUARE_SIZE//2-3
            clr=HOVER_BLACK_COLOR if current_player==BLACK else HOVER_WHITE_COLOR
            tmp=pygame.Surface((rad*2,rad*2),pygame.SRCALPHA); pygame.draw.circle(tmp,clr,(rad,rad),rad)
            screen.blit(tmp, (ctr[0]-rad, ctr[1]-rad))
    except Exception as e: print(f"Error drawing hover preview: {e}")

# --- REVISED draw_info_panel ---
def draw_info_panel(screen, game, font_small, font_medium):
    restart_btn, pause_btn, save_btn, load_btn = None, None, None, None
    panel_rect = pygame.Rect(0, BOARD_AREA_HEIGHT, WIDTH - ANALYSIS_WIDTH, INFO_HEIGHT)
    try: pygame.draw.rect(screen, INFO_BG_COLOR, panel_rect)
    except Exception as e: print(f"Render Error: Info Panel BG - {e}"); return None, None, None, None

    left_pad=15; right_pad=WIDTH-ANALYSIS_WIDTH-15; timer_y=panel_rect.top+8
    btn_h, btn_w, pad = 28, 75, 8; btn_y = panel_rect.bottom - btn_h - 8
    button_top_y = btn_y - 4 # Estimate space above buttons
    status_y = timer_y # Default if no fonts

    if font_small and font_medium:
        timer_line_height = font_small.get_height() if font_small else 15
        status_line_height = font_medium.get_height() if font_medium else 20
        # Calculate Y pos for status message, trying to center it vertically
        status_y = timer_y + (button_top_y - timer_y) // 2 - status_line_height // 2
        status_y = max(status_y, timer_y + timer_line_height + 4) # Ensure below timers

        # Timers
        if game.game_state != GameState.ANALYSIS:
            try:
                b_time=format_time(game.timers[BLACK]); w_time=format_time(game.timers[WHITE])
                b_surf=font_small.render(f"黑: {b_time}",True,INFO_TEXT_COLOR)
                w_surf=font_small.render(f"白: {w_time}",True,INFO_TEXT_COLOR)
                screen.blit(b_surf, (left_pad, timer_y)); screen.blit(w_surf, (right_pad - w_surf.get_width(), timer_y))
            except Exception as e: print(f"Render Error: Timers - {e}")
        # Status
        try:
            status_surf=font_medium.render(game.status_message,True,INFO_TEXT_COLOR)
            screen.blit(status_surf, status_surf.get_rect(centerx=panel_rect.centerx, y=status_y))
        except Exception as e: print(f"Render Error: Status - {e}")

        # Buttons
        total_w=btn_w*4+pad*3; start_x=panel_rect.centerx-total_w//2
        restart_btn=pygame.Rect(start_x,btn_y,btn_w,btn_h); pause_btn=pygame.Rect(restart_btn.right+pad,btn_y,btn_w,btn_h)
        save_btn=pygame.Rect(pause_btn.right+pad,btn_y,btn_w,btn_h); load_btn=pygame.Rect(save_btn.right+pad,btn_y,btn_w,btn_h)
        try: pygame.draw.rect(screen,BUTTON_COLOR,restart_btn,border_radius=5); t=font_small.render("重新開始",True,BUTTON_TEXT_COLOR); screen.blit(t, t.get_rect(center=restart_btn.center))
        except: pass
        try: pause_txt="恢復" if game.game_state==GameState.PAUSED else "暫停"; active=game.game_state in [GameState.PLAYING,GameState.PAUSED]; bc=BUTTON_COLOR if active else (160,160,160); tc=BUTTON_TEXT_COLOR if active else (210,210,210); pygame.draw.rect(screen,bc,pause_btn,border_radius=5); t=font_small.render(pause_txt,True,tc); screen.blit(t, t.get_rect(center=pause_btn.center))
        except: pass
        try: pygame.draw.rect(screen,BUTTON_COLOR,save_btn,border_radius=5); t=font_small.render("儲存棋譜",True,BUTTON_TEXT_COLOR); screen.blit(t, t.get_rect(center=save_btn.center))
        except: pass
        try: pygame.draw.rect(screen,BUTTON_COLOR,load_btn,border_radius=5); t=font_small.render("載入棋譜",True,BUTTON_TEXT_COLOR); screen.blit(t, t.get_rect(center=load_btn.center))
        except: pass

    return restart_btn, pause_btn, save_btn, load_btn
# --- END REVISED draw_info_panel ---


# --- REVISED draw_analysis_panel ---
def draw_analysis_panel(screen, game, font_small, font_medium): # Use font_medium for title
    buttons = {}
    panel_rect = pygame.Rect(BOARD_AREA_WIDTH, 0, ANALYSIS_WIDTH, HEIGHT)
    try: pygame.draw.rect(screen, ANALYSIS_BG_COLOR, panel_rect)
    except Exception as e: print(f"Render Error: Analysis Panel BG - {e}"); return {}

    top_padding=15; button_area_height=80; move_list_top_padding=10
    button_area_rect = pygame.Rect(panel_rect.left, panel_rect.top + top_padding, panel_rect.width, button_area_height)
    move_list_area_rect = pygame.Rect( panel_rect.left, button_area_rect.bottom + move_list_top_padding, panel_rect.width, panel_rect.height - button_area_rect.bottom - move_list_top_padding - 10 )

    if game.game_state == GameState.ANALYSIS:
        analysis_font = font_small
        if not analysis_font: return buttons
        # --- Draw Nav Buttons ---
        btn_w, btn_h, h_space, v_space = 70, 30, 10, 10
        start_x = panel_rect.centerx - (btn_w * 2 + h_space) // 2
        current_y = button_area_rect.top
        try: # Row 1
            r1=pygame.Rect(start_x,current_y,btn_w,btn_h);buttons['first']=r1;pygame.draw.rect(screen,BUTTON_COLOR,r1,border_radius=5);s=analysis_font.render("<< 首步",True,BUTTON_TEXT_COLOR);screen.blit(s,s.get_rect(center=r1.center))
            r2=pygame.Rect(r1.right+h_space,current_y,btn_w,btn_h);buttons['prev']=r2;pygame.draw.rect(screen,BUTTON_COLOR,r2,border_radius=5);s=analysis_font.render("<上一步",True,BUTTON_TEXT_COLOR);screen.blit(s,s.get_rect(center=r2.center))
        except: pass
        current_y += btn_h + v_space
        try: # Row 2
            r3=pygame.Rect(start_x,current_y,btn_w,btn_h);buttons['next']=r3;pygame.draw.rect(screen,BUTTON_COLOR,r3,border_radius=5);s=analysis_font.render("下一步>",True,BUTTON_TEXT_COLOR);screen.blit(s,s.get_rect(center=r3.center))
            r4=pygame.Rect(r3.right+h_space,current_y,btn_w,btn_h);buttons['last']=r4;pygame.draw.rect(screen,BUTTON_COLOR,r4,border_radius=5);s=analysis_font.render("末步>>",True,BUTTON_TEXT_COLOR);screen.blit(s,s.get_rect(center=r4.center))
        except: pass

        # --- Draw Move List ---
        if not font_small: return buttons
        list_x_pad = 10; list_area = move_list_area_rect.inflate(-list_x_pad*2, -10)
        try:
            line_h = font_small.get_linesize() + 2; max_lines = list_area.height//line_h if line_h>0 else 0
            if max_lines>0 and game.move_log:
                total = len(game.move_log); current=game.analysis_step; start_idx=0
                if total>max_lines: start_idx=max(0,min(max(0,current)-max_lines//2,total-max_lines))
                for i in range(max_lines):
                    idx=start_idx+i;
                    if idx>=total:break
                    data=game.move_log[idx]; p=data.get('player'); r,c=data.get('row',-1),data.get('col',-1)
                    t=data.get('time'); pause=data.get('pause',0.0); pc="黑" if p==BLACK else "白" if p==WHITE else "?"
                    coord=f"({chr(ord('A')+c)}{BOARD_SIZE-r})" if 0<=r<BOARD_SIZE and 0<=c<BOARD_SIZE else "(?)"
                    ts=f"({t:.1f}s)" if t is not None else "(?)"; ps=f"[P:{pause:.1f}s]" if pause>0.05 else ""
                    txt=f"{idx+1}.{pc}{coord}{ts}{ps}"
                    is_curr=(idx==current); color=MOVE_LIST_HIGHLIGHT_COLOR if is_curr else INFO_TEXT_COLOR
                    surf=font_small.render(txt,True,color); y=list_area.top+i*line_h; max_w=list_area.width
                    if surf.get_width()>max_w: # Truncate
                        try: k=max(1,int(len(txt)*max_w/surf.get_width())-2); surf=font_small.render(txt[:k]+"..",True,color)
                        except: pass
                    screen.blit(surf, (list_area.left, y))
            elif not game.move_log:
                 txt=font_small.render("無棋譜記錄",True,INFO_TEXT_COLOR); screen.blit(txt, txt.get_rect(center=list_area.center))
        except Exception as e: print(f"Error rendering move list: {e}")

    # Removed the "else" block that drew the "Renju" title when not in analysis

    return buttons
# --- END REVISED draw_analysis_panel ---


# --- Main Game Loop ---
def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("五子棋 (日本規則)")
    clock = pygame.time.Clock()

    # --- Load Fonts ---
    font_s = load_best_font(16) # Small font
    font_m = load_best_font(20) # Medium font
    if not font_s or not font_m:
        print("FATAL: Could not load necessary fonts.")
        pygame.quit(); sys.exit()

    game = RenjuGame()
    running = True
    hover_coords = None
    restart_btn, pause_btn, save_btn, load_btn = None, None, None, None
    analysis_btns = {}

    while running:
        # === Event Handling ===
        mouse_pos = pygame.mouse.get_pos()
        hover_coords = get_board_coords(mouse_pos[0], mouse_pos[1]) if game.game_state == GameState.PLAYING else None

        try:
            for event in pygame.event.get():
                if event.type == pygame.QUIT: running = False
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    clicked_ui = False
                    # Check Bottom Buttons FIRST
                    if restart_btn and restart_btn.collidepoint(mouse_pos): game.restart_game(); clicked_ui = True
                    elif pause_btn and pause_btn.collidepoint(mouse_pos):
                        if game.game_state == GameState.PLAYING: game.pause_game()
                        elif game.game_state == GameState.PAUSED: game.resume_game()
                        clicked_ui = True
                    elif save_btn and save_btn.collidepoint(mouse_pos): game.save_game(); clicked_ui = True
                    elif load_btn and load_btn.collidepoint(mouse_pos): game.load_game(); clicked_ui = True
                    # Check Analysis Buttons
                    if not clicked_ui and game.game_state == GameState.ANALYSIS:
                        for key, rect in analysis_btns.items():
                            if rect and rect.collidepoint(mouse_pos): game.analysis_navigate(key); clicked_ui = True; break
                    # Check Board Click
                    if not clicked_ui and game.game_state == GameState.PLAYING:
                        click_coords = get_board_coords(mouse_pos[0], mouse_pos[1])
                        if click_coords: game.make_move(click_coords[0], click_coords[1])
                if event.type == pygame.KEYDOWN: # Keyboard shortcuts
                    if game.game_state == GameState.ANALYSIS:
                        if event.key == pygame.K_RIGHT: game.analysis_navigate('next')
                        elif event.key == pygame.K_LEFT: game.analysis_navigate('prev')
                        elif event.key in [pygame.K_UP, pygame.K_HOME]: game.analysis_navigate('first')
                        elif event.key in [pygame.K_DOWN, pygame.K_END]: game.analysis_navigate('last')
                    elif game.game_state == GameState.PLAYING and event.key == pygame.K_p: game.pause_game()
                    elif game.game_state == GameState.PAUSED and event.key == pygame.K_p: game.resume_game()
                    elif event.key == pygame.K_r: game.restart_game() # 'R' for restart shortcut
        except Exception as e: print(f"Event Handling Error: {e}")

        # === Game Logic Update ===
        try: game.update_timers()
        except Exception as e: print(f"Timer Update Error: {e}")

        # === Drawing ===
        try:
            board_to_draw = game.analysis_board if game.game_state == GameState.ANALYSIS else game.board
            last_move_to_draw = game.last_move
            if game.game_state == GameState.ANALYSIS :
                if game.analysis_step >= 0 and game.analysis_step < len(game.move_log):
                    m = game.move_log[game.analysis_step]; last_move_to_draw = (m['row'], m['col'])
                else: last_move_to_draw = None

            draw_grid(screen)
            draw_stones(screen, board_to_draw, last_move_to_draw, game.game_state)
            if game.game_state == GameState.PLAYING: draw_hover_preview(screen, hover_coords, game.current_player, board_to_draw)

            # Pass correct fonts to drawing functions
            restart_btn, pause_btn, save_btn, load_btn = draw_info_panel(screen, game, font_s, font_m)
            analysis_btns = draw_analysis_panel(screen, game, font_s, font_m)

            pygame.display.flip()
        except Exception as e: print(f"Drawing Error: {e}")

        clock.tick(30)

    pygame.quit()
    sys.exit()

# --- Execution Start ---
if __name__ == "__main__":
    main()