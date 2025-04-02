# -*- coding: utf-8 -*-
import time
import json
import os
import random
from config import (GameState, BOARD_SIZE, EMPTY, BLACK, WHITE, EDGE,
                    DIRECTIONS, DEFAULT_TIME_LIMIT)
from utils import is_on_board
import ast # For safely evaluating tuple strings from JSON

# --- 開局庫文件路徑 ---
OPENING_BOOK_FILE = "opening_book.json"

# --- 加載開局庫函數 ---
def load_opening_book():
    """從 JSON 文件加載開局庫數據。"""
    default_book = { "((7, 7),)": [[7, 8], [6, 7], [6, 8]], }
    if os.path.exists(OPENING_BOOK_FILE):
        try:
            with open(OPENING_BOOK_FILE, 'r', encoding='utf-8') as f: data = json.load(f)
            book = {}
            for k_str, v_list_of_lists in data.items():
                try:
                    key_tuple = ast.literal_eval(k_str)
                    if isinstance(key_tuple, tuple) and \
                       all(isinstance(m, tuple) and len(m)==2 for m in key_tuple) and \
                       isinstance(v_list_of_lists, list) and \
                       all(isinstance(move, list) and len(move)==2 for move in v_list_of_lists):
                        book[key_tuple] = [tuple(move) for move in v_list_of_lists]
                    else: print(f"Warn: Invalid format in book. Key: {k_str}, Val: {v_list_of_lists}")
                except Exception as e: print(f"Warn: Error parsing key '{k_str}': {e}")
            print(f"Loaded {len(book)} entries (with move lists) from {OPENING_BOOK_FILE}")
            mem_default={ast.literal_eval(k):[tuple(m) for m in v] for k,v in default_book.items()}
            return book if book else mem_default
        except Exception as e:
            print(f"Error loading book: {e}. Using default.")
            mem_default={}
            for k,v in default_book.items(): mem_default[ast.literal_eval(k)]=[tuple(m) for m in v]
            return mem_default
    else:
        print(f"Book file '{OPENING_BOOK_FILE}' not found. Using default.");
        mem_default={}
        for k,v in default_book.items(): mem_default[ast.literal_eval(k)]=[tuple(m) for m in v]
        return mem_default

# --- 保存開局庫函數 ---
def save_opening_book_to_file(book_data):
     """將開局庫數據保存到 JSON 文件。"""
     try:
         serializable_book = {str(k): [list(move) for move in v_list] for k, v_list in book_data.items()}
         with open(OPENING_BOOK_FILE, 'w', encoding='utf-8') as f:
             json.dump(serializable_book, f, indent=4, ensure_ascii=False, sort_keys=True)
         print(f"Opening book saved to {OPENING_BOOK_FILE}")
     except Exception as e: print(f"Error saving opening book: {e}")

# --- 在模塊加載時加載開局庫 ---
OPENING_BOOK = load_opening_book()


class RenjuGame:
    """處理 Renju 遊戲的核心邏輯、狀態和規則，支援多種模式和簡單 AI。"""

    def __init__(self, black_player_type="human", white_player_type="ai"):
        """初始化遊戲。"""
        global OPENING_BOOK
        self.board = [[EMPTY for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
        self.current_player = BLACK; self.game_state = GameState.PLAYING
        self.last_move = None; self.move_count = 0; self.move_log = []
        self.timers = {BLACK: DEFAULT_TIME_LIMIT, WHITE: DEFAULT_TIME_LIMIT}
        self.last_update_time = time.time(); self.current_move_start_time = self.last_update_time
        self.pause_start_time = None; self.accumulated_pause_time = 0.0
        self.analysis_step = -1; self.analysis_board = [[EMPTY for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
        self.player_types = {BLACK: black_player_type, WHITE: white_player_type}; self.ai_thinking = False
        p1 = "(H)" if self.player_types[BLACK]=="human" else "(AI)"
        p2 = "(H)" if self.player_types[WHITE]=="human" else "(AI)"
        p_name = "黑方" if self.current_player==BLACK else "白方"
        p_type = p1 if self.current_player==BLACK else p2
        if self.move_count==0 and self.current_player==BLACK: self.status_message = f"{p_name}{p_type} 回合 (請下天元)"
        else: self.status_message = f"{p_name}{p_type} 回合"

    def restart_game(self): p_black=self.player_types[BLACK]; p_white=self.player_types[WHITE]; self.__init__(black_player_type=p_black, white_player_type=p_white)
    def pause_game(self):
        if self.game_state == GameState.PLAYING:
            self.game_state = GameState.PAUSED; self.pause_start_time = time.time()
            elapsed = self.pause_start_time - self.last_update_time; self.timers[self.current_player] = max(0, self.timers[self.current_player] - elapsed)
            p_name="黑方" if self.current_player==BLACK else "白方"; p_type="(H)" if self.player_types[self.current_player]=="human" else "(AI)"
            self.status_message = f"{p_name}{p_type} 暫停 (按鈕恢復)"; print("Game Paused")
    def resume_game(self):
        if self.game_state == GameState.PAUSED and self.pause_start_time is not None:
            paused = time.time() - self.pause_start_time; self.accumulated_pause_time += paused; self.last_update_time = time.time()
            self.game_state = GameState.PLAYING; self.pause_start_time = None; p_name="黑方" if self.current_player==BLACK else "白方"
            p_type="(H)" if self.player_types[self.current_player]=="human" else "(AI)"; self.status_message = f"{p_name}{p_type} 回合"; print(f"Resumed (Paused {paused:.1f}s)")
        elif self.game_state == GameState.PAUSED:
            self.game_state = GameState.PLAYING; self.last_update_time = time.time(); p_name="黑方" if self.current_player==BLACK else "白方"
            p_type="(H)" if self.player_types[self.current_player]=="human" else "(AI)"; self.status_message = f"{p_name}{p_type} 回合"; print("Warn: Resuming inconsistent pause.")
    def update_timers(self):
        if self.game_state != GameState.PLAYING: return
        now=time.time(); elapsed=now-self.last_update_time; self.last_update_time=now; self.timers[self.current_player]=max(0,self.timers[self.current_player]-elapsed)
        if self.timers[self.current_player]<=0:
            loser=self.current_player; winner=WHITE if loser==BLACK else BLACK; self.game_state=GameState.BLACK_WINS if winner==BLACK else GameState.WHITE_WINS
            w_name="黑方" if winner==BLACK else "白方"; w_type="(H)" if self.player_types[winner]=="human" else "(AI)"; l_type="(H)" if self.player_types[loser]=="human" else "(AI)"
            self.status_message = f"超時! {w_name}{w_type} 勝!"; print(f"Timeout! Player {loser} ({l_type}) lost.")
            if self.player_types[loser]=="ai": print(f"AI {loser} lost by timeout. Learning..."); self.learn_from_loss(self.move_log)
    def _is_valid_move(self, r, c, player):
        if not is_on_board(r, c) or self.board[r][c] != EMPTY: return False, "Occupied or Off-board"
        if player == BLACK:
            if self.move_count == 0: return (True, None) if (r,c) == (7,7) else (False, "First move must be Tengen (7,7)")
            else: self.board[r][c]=player; win=self.check_win_condition(r,c,player); reason=None if win else self.check_forbidden_move(r,c); self.board[r][c]=EMPTY; return (False, reason) if reason else (True, None)
        else: return True, None
    def make_move(self, r, c):
        if self.game_state != GameState.PLAYING: self.status_message = "遊戲已結束或暫停"; return False
        player=self.current_player; ptype="(H)" if self.player_types[player]=="human" else "(AI)"; pname="黑方" if player==BLACK else "白方"
        valid, reason = self._is_valid_move(r, c, player)
        if not valid:
             if reason=="First move must be Tengen (7,7)": self.status_message=f"{pname}{ptype} 請下天元 (7, 7)"
             elif reason=="Occupied or Off-board": self.status_message=f"{pname}{ptype} 無效位置!"
             else: self.status_message=f"{pname}{ptype} 禁手: {reason}! 請選他處."
             print(f"Invalid move by {pname}{ptype} at ({r},{c}): {reason}"); return False
        self.board[r][c]=player; self.last_move=(r,c); self.move_count+=1
        log={"player": player, "row": r, "col": c, "time": round(time.time()-self.current_move_start_time,1), "pause": round(self.accumulated_pause_time,1)}
        self.move_log.append(log); self.accumulated_pause_time = 0.0
        if self.check_win_condition(r, c, player):
            self.game_state=GameState.BLACK_WINS if player==BLACK else GameState.WHITE_WINS; loser=WHITE if player==BLACK else BLACK
            self.status_message = f"{pname}{ptype} 連珠五子勝!"; print(f"Win for {pname}{ptype} at ({r},{c})")
            if self.player_types[loser]=="ai": print(f"AI {loser} lost. Learning..."); self.learn_from_loss(self.move_log)
            return True
        if self.move_count == BOARD_SIZE*BOARD_SIZE: self.game_state=GameState.DRAW; self.status_message="平局!"; print("Draw game."); return True
        self.switch_player(); return True
    def switch_player(self):
        self.current_player = WHITE if self.current_player==BLACK else BLACK; p_name="黑方" if self.current_player==BLACK else "白方"; p_type="(H)" if self.player_types[self.current_player]=="human" else "(AI)"
        if self.move_count==1 and self.current_player==WHITE: self.status_message = f"{p_name}{p_type} 回合"
        elif self.move_count==0 and self.current_player==BLACK: self.status_message = f"{p_name}{p_type} 回合 (請下天元)"
        else: self.status_message = f"{p_name}{p_type} 回合"
        now=time.time(); self.last_update_time=now; self.current_move_start_time=now
    def count_line(self, r, c, player, dr_dc):
        dr,dc=dr_dc; count=1; open_ends=0; cr,cc=r+dr,c+dc
        while is_on_board(cr,cc) and self.board[cr][cc]==player: count+=1; cr+=dr; cc+=dc
        if is_on_board(cr,cc) and self.board[cr][cc]==EMPTY: open_ends+=1
        cr,cc=r-dr,c-dc
        while is_on_board(cr,cc) and self.board[cr][cc]==player: count+=1; cr-=dr; cc-=dc
        if is_on_board(cr,cc) and self.board[cr][cc]==EMPTY: open_ends+=1
        return count, open_ends
    def check_win_condition(self, r, c, player):
        for dr_dc in DIRECTIONS: count,_=self.count_line(r,c,player,dr_dc); C=count; P=player; B=BLACK; W=WHITE;
        if (P==B and C==5) or (P==W and C>=5): return True
        return False
    def check_forbidden_move(self, r, c):
        player=BLACK;
        for dr_dc in DIRECTIONS: count,_=self.count_line(r,c,player,dr_dc); C=count;
        if C>=6: return "長連"
        threes, fours = 0, 0
        for dr_dc in DIRECTIONS:
            four,_=self.check_specific_line(r,c,player,dr_dc,4); count4,_=self.count_line(r,c,player,dr_dc)
            if four and count4==4: fours+=1
            three,open3=self.check_specific_line(r,c,player,dr_dc,3); count3,_=self.count_line(r,c,player,dr_dc)
            if open3 and count3==3: threes+=1
        if fours>=2: return "四四"
        if threes>=2 and fours<2: return "三三"
        return None
    def check_specific_line(self, r, c, player, dr_dc, target):
        dr,dc=dr_dc; line=[]; idx=-1; T=target
        for i in range(T+1,0,-1): cr,cc=r-i*dr,c-i*dc; line.append(self.board[cr][cc] if is_on_board(cr,cc) else EDGE)
        line.append(player); idx=len(line)-1
        for i in range(1,T+2): cr,cc=r+i*dr,c+i*dc; line.append(self.board[cr][cc] if is_on_board(cr,cc) else EDGE)
        found=False; open3=False
        for i in range(len(line)-T+1):
            sub=line[i:i+T]
            if all(s==player for s in sub) and i<=idx<i+T:
                 left=line[i-1] if i>0 else EDGE; right=line[i+T] if (i+T)<len(line) else EDGE; longer=(left==player or right==player)
                 if not longer:
                    found=True
                    if T==3 and left==EMPTY and right==EMPTY:
                        open3=True; break
        if T==3: return found, open3
        else: return found, False
    def save_game(self, filename="renju_save.json"):
        save_data = {"move_log": self.move_log, "player_black": self.player_types[BLACK], "player_white": self.player_types[WHITE]}
        try:
            with open(filename, 'w', encoding='utf-8') as f: json.dump(save_data, f, indent=4, ensure_ascii=False, sort_keys=True)
            self.status_message = f"棋譜已存檔至 {filename}"; print(f"Saved to {filename}")
        except Exception as e: self.status_message = "存檔失敗!"; print(f"Error saving game to {filename}: {e}")
    def load_game(self, filename="renju_save.json"):
        global OPENING_BOOK; OPENING_BOOK = load_opening_book()
        try:
            if not os.path.exists(filename): self.status_message=f"找不到檔案"; return False
            with open(filename, 'r', encoding='utf-8') as f: save_data = json.load(f)
            p_black=save_data.get("player_black","human"); p_white=save_data.get("player_white","human")
            self.__init__(black_player_type=p_black, white_player_type=p_white)
            self.move_log = save_data.get("move_log", [])
            p1="(H)" if self.player_types[BLACK]=="human" else "(AI)"; p2="(H)" if self.player_types[WHITE]=="human" else "(AI)"
            mode=f"{p1} vs {p2}"; msg=f"載入空棋譜 ({mode})" if not self.move_log else f"棋譜載入 ({mode})"
            self.status_message=f"{msg} - 分析模式"; print(f"Loaded {filename} ({mode}). Analysis.")
            self.game_state=GameState.ANALYSIS; self.analysis_step=-1; self._reconstruct_board_to_step(self.analysis_step); return True
        except Exception as e: self.restart_game(); self.status_message="載入失敗!"; print(f"Error loading: {e}"); return False
    def analysis_navigate(self, direction):
        if self.game_state!=GameState.ANALYSIS or not self.move_log: return
        target=self.analysis_step; total=len(self.move_log); T=target; TT=total; S=self.analysis_step
        if direction=='next': T=min(S+1, TT-1)
        elif direction=='prev': T=max(S-1, -1)
        elif direction=='first': T=-1
        elif direction=='last': T=TT-1
        if T!=S:
            self.analysis_step=T; self._reconstruct_board_to_step(T); P1T=self.player_types[BLACK]; P2T=self.player_types[WHITE]
            p1="(H)" if P1T=="human" else "(AI)"; p2="(H)" if P2T=="human" else "(AI)"
            if T==-1: self.status_message=f"分析 ({p1} vs {p2}): 初始"
            else: m=self.move_log[T]; p=m.get('player'); mn=T+1; pn="黑" if p==BLACK else "白" if p==WHITE else "?"; pt="(H)" if self.player_types.get(p)=="human" else "(AI)" if self.player_types.get(p)=="ai" else ""; self.status_message=f"分析: {mn}手 ({pn}{pt})"
    def _reconstruct_board_to_step(self, target_idx):
        board=[[EMPTY for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]; self.last_move=None
        for i in range(target_idx+1):
            if i<len(self.move_log): data=self.move_log[i]; r,c,p=data.get('row',-1),data.get('col',-1),data.get('player',0)
            if is_on_board(r,c):
                if board[r][c]==EMPTY: board[r][c]=p; self.last_move=(r,c) if i==target_idx else None
                else: print(f"W:Rec Overwrite {i+1}"); self.last_move=None; break
            else: print(f"W:Rec Invalid {i+1}"); self.last_move=None; break
        self.analysis_board = board

    # --- find_best_move with corrected syntax and logic ---
    def find_best_move(self, return_book_usage=False):
        if self.game_state != GameState.PLAYING: return None, False

        ai_player = self.current_player; opponent_player = WHITE if ai_player == BLACK else BLACK
        used_book_flag = False
        try:
            # Strategy -1: AI Black First Move
            if self.move_count == 0 and ai_player == BLACK:
                valid,_ = self._is_valid_move(7,7,ai_player); move=(7,7) if valid else None
                if move: print(f"AI ({ai_player}) mandatory Tengen"); return move, False

            # Strategy 0: Opening Book
            if self.move_count > 0:
                global OPENING_BOOK; seq = tuple(tuple(m[k] for k in ['row','col']) for m in self.move_log)
                if seq in OPENING_BOOK:
                    possible = OPENING_BOOK[seq]; valid_moves = []
                    if isinstance(possible, list): valid_moves=[m for m in possible if self._is_valid_move(m[0],m[1],ai_player)[0]]
                    if valid_moves: move=random.choice(valid_moves); print(f"AI ({ai_player}) using book {move} from {len(valid_moves)}"); return move, True
                    else: print(f"AI ({ai_player}) book seq found but no valid moves. Fallback.")

            # Strategies 1, 2, 2.25, 2.5, 3
            empty = []; occupied = set();
            for r in range(BOARD_SIZE):
                for c in range(BOARD_SIZE): (empty.append((r,c)) if self.board[r][c]==EMPTY else occupied.add((r,c)))
            if not empty: print(f"AI ({ai_player}) no empty spots."); return None, False

            # 1. Win
            for r,c in empty: valid,_=self._is_valid_move(r,c,ai_player);
            if valid: self.board[r][c]=ai_player; win=self.check_win_condition(r,c,ai_player); self.board[r][c]=EMPTY;
            if valid and win: print(f"AI ({ai_player}) found win at ({r},{c})"); return (r,c), False

            # 2. Block Win
            for r,c in empty: self.board[r][c]=opponent_player; opp_wins=self.check_win_condition(r,c,opponent_player); self.board[r][c]=EMPTY;
            if opp_wins: block_ok,_=self._is_valid_move(r,c,ai_player);
            if opp_wins and block_ok: print(f"AI ({ai_player}) blocking win at ({r},{c})"); return (r,c), False

            # 2.25: Block Threatening Four
            four_blocks = []
            for r, c in empty:
                 self.board[r][c] = opponent_player
                 forms_threatening_four = False
                 # --- Corrected Loop ---
                 for dr_dc in DIRECTIONS:
                     count, ends = self.count_line(r, c, opponent_player, dr_dc)
                     if count == 4 and ends >= 1:
                         forms_threatening_four = True
                         break # Exit inner loop once found
                 # --- End Corrected Loop ---
                 self.board[r][c] = EMPTY
                 if forms_threatening_four:
                      can_block_here, _ = self._is_valid_move(r, c, ai_player)
                      if can_block_here: four_blocks.append((r, c))
            if four_blocks: move=random.choice(four_blocks); print(f"AI ({ai_player}) blocking four at {move}"); return move, False

            # 2.5: Block Open Three
            three_blocks = []
            for r, c in empty:
                 self.board[r][c] = opponent_player
                 forms_open_three = False
                 # --- Corrected Loop ---
                 for dr_dc in DIRECTIONS:
                     is_three, is_open = self.check_specific_line(r, c, opponent_player, dr_dc, 3)
                     if is_open:
                         count_overall, _ = self.count_line(r, c, opponent_player, dr_dc)
                         if count_overall == 3:
                             forms_open_three = True
                             break
                 # --- End Corrected Loop ---
                 self.board[r][c] = EMPTY
                 if forms_open_three:
                     can_block_here, _ = self._is_valid_move(r, c, ai_player)
                     if can_block_here: three_blocks.append((r, c))
            if three_blocks: move=random.choice(three_blocks); print(f"AI ({ai_player}) blocking open three at {move}"); return move, False

            # 3. Adjacent/Random
            candidates=[]; adjacent=set(); offsets=[(dr,dc) for dr in [-1,0,1] for dc in [-1,0,1] if not (dr==0 and dc==0)]
            if ai_player==WHITE and self.move_count==1 and self.board[7][7]==BLACK:
                for dr,dc in offsets: nr,nc=7+dr,7+dc; adjacent.add((nr,nc)) if is_on_board(nr,nc) and self.board[nr][nc]==EMPTY else None
            else:
                 for r_o,c_o in occupied:
                     for dr,dc in offsets: nr,nc=r_o+dr,c_o+dc; adjacent.add((nr,nc)) if is_on_board(nr,nc) and self.board[nr][nc]==EMPTY else None
            for r_a,c_a in adjacent: valid,_=self._is_valid_move(r_a,c_a,ai_player); candidates.append((r_a,c_a)) if valid else None

            if candidates: move=random.choice(candidates); print(f"AI ({ai_player}) chose adjacent {move}..."); return move, False
            else:
                all_valid = [m for m in empty if self._is_valid_move(m[0], m[1], ai_player)[0]]
                if all_valid: move=random.choice(all_valid); print(f"AI ({ai_player}) chose random {move}..."); return move, False
                else: print(f"AI ({ai_player}) no valid moves!"); return None, False

            print(f"Error: AI ({ai_player}) failed to determine move."); return None, False
        finally:
            # No need to set self.ai_thinking = False here
            pass

    # --- learn_from_loss with corrected loser logic and list handling ---
    def learn_from_loss(self, final_move_log):
        print("--- Entering learn_from_loss ---")
        global OPENING_BOOK
        if not final_move_log or len(final_move_log)<2: print("Learn: Log too short."); print("--- Exit learn ---"); return
        winner=final_move_log[-1].get('player'); loser=WHITE if winner==BLACK else BLACK
        if self.player_types.get(loser)!="ai": print(f"Learn: Loser {loser} not AI."); print("--- Exit learn ---"); return

        ai_last_idx = -1
        for i in range(len(final_move_log)-2, -1, -1):
             if final_move_log[i].get('player') == loser: ai_last_idx=i; break
        if ai_last_idx == -1: print(f"Learn: AI {loser} move not found before loss."); print("--- Exit learn ---"); return

        ai_losing_data=final_move_log[ai_last_idx]; losing_move=tuple(ai_losing_data[k] for k in ['row','col'])
        seq_before=final_move_log[:ai_last_idx]; key_seq=tuple(tuple(m[k] for k in ['row','col']) for m in seq_before)
        print(f"Learn: AI {loser} lost. Last AI move {losing_move} at index {ai_last_idx}"); print(f"Learn: Sequence key {key_seq}")

        # Reconstruct board state before AI's losing move
        print("Learn: Reconstructing board state...")
        temp_board = [[EMPTY for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]; ok = True
        for i, move_data in enumerate(seq_before):
            r, c, p = move_data.get('row',-1), move_data.get('col',-1), move_data.get('player',0)
            # --- Corrected Block ---
            if is_on_board(r, c) and temp_board[r][c] == EMPTY:
                temp_board[r][c] = p
            else:
                print(f"Learn Err: Recon failed at step {i+1} ({r},{c}). Invalid coord or overwrite.")
                ok = False
                break # Break the loop if reconstruction fails
            # --- End Corrected Block ---
        if not ok:
            print("--- Exiting learn_from_loss (Reconstruction Failed) ---") # Debug Exit
            return # Exit if reconstruction failed
        print("Learn: Board state reconstructed.")

        orig_board=self.board; orig_count=self.move_count; self.board=temp_board; self.move_count=len(seq_before)
        valid_moves=[(r,c) for r in range(BOARD_SIZE) for c in range(BOARD_SIZE) if self.board[r][c]==EMPTY and self._is_valid_move(r,c,loser)[0]]
        self.board=orig_board; self.move_count=orig_count
        print(f"Learn: Found {len(valid_moves)} valid moves then: {valid_moves}")
        alternatives=[m for m in valid_moves if m!=losing_move]
        print(f"Learn: Losing move {losing_move}. Found {len(alternatives)} alternatives: {alternatives}")

        book_entry = OPENING_BOOK.get(key_seq)
        updated = False
        if isinstance(book_entry, list):
             if losing_move in book_entry:
                 book_entry.remove(losing_move); print(f"Learn: Removed {losing_move} from book list for {key_seq}.")
                 if not book_entry: del OPENING_BOOK[key_seq]; print(f"Learn: Removed key {key_seq} as list empty.")
                 updated = True
             else: print(f"Learn: Losing move {losing_move} not in book list {book_entry}. No update.")
        elif book_entry == losing_move: # Handle potential old format
             if alternatives:
                 new_move = random.choice(alternatives); OPENING_BOOK[key_seq] = [new_move]
                 print(f"Learn: Replaced single losing {losing_move} with [{new_move}] for {key_seq}.")
                 updated = True
             else: del OPENING_BOOK[key_seq]; print(f"Learn: Removed single losing {key_seq} no alternatives.") ; updated = True
        elif book_entry is None and alternatives: # Sequence not in book
             new_move = random.choice(alternatives); OPENING_BOOK[key_seq] = [new_move]
             print(f"Learn: Added new seq {key_seq} to book with [{new_move}]."); updated = True
        else: print(f"Learn: No update needed/possible. Entry: {book_entry}, Alts: {len(alternatives)}")

        if updated: print("Learn: Saving updated book..."); save_opening_book_to_file(OPENING_BOOK); print("Learn: Save called.")
        else: print("Learn: No changes to opening book.")
        print("--- Exiting learn_from_loss ---")