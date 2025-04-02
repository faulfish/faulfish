# -*- coding: utf-8 -*-
import time
import json
import os
import random
from config import (GameState, BOARD_SIZE, EMPTY, BLACK, WHITE, EDGE,
                    DIRECTIONS, DEFAULT_TIME_LIMIT) # 導入必要的配置和枚舉
from utils import is_on_board # 導入輔助函數

# --- 簡單開局庫 ---
OPENING_BOOK = {
    ((7, 7),): (7, 8),
    ((7, 7), (7, 8)): (6, 8),
    ((7, 7), (6, 7)): (6, 8),
    ((7, 7), (7, 8), (6, 8)): (6, 7),
    ((7, 7), (6, 7), (6, 8)): (7, 8),
    ((7, 7), (7, 8), (6, 8), (6, 7)): (5, 7),
}


class RenjuGame:
    """處理 Renju 遊戲的核心邏輯、狀態和規則，支援多種模式和簡單 AI。"""

    def __init__(self, black_player_type="human", white_player_type="ai"):
        """初始化遊戲。"""
        self.board = [[EMPTY for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
        self.current_player = BLACK
        self.game_state = GameState.PLAYING
        self.last_move = None
        self.move_count = 0
        self.move_log = []
        self.timers = {BLACK: DEFAULT_TIME_LIMIT, WHITE: DEFAULT_TIME_LIMIT}
        self.last_update_time = time.time()
        self.current_move_start_time = self.last_update_time
        self.pause_start_time = None
        self.accumulated_pause_time = 0.0
        self.analysis_step = -1
        self.analysis_board = [[EMPTY for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
        self.player_types = {BLACK: black_player_type, WHITE: white_player_type}
        self.ai_thinking = False
        p1_type_str = "(Human)" if self.player_types[BLACK] == "human" else "(AI)"
        p2_type_str = "(Human)" if self.player_types[WHITE] == "human" else "(AI)"
        player_name = "黑方" if self.current_player == BLACK else "白方"
        current_player_type_str = p1_type_str if self.current_player == BLACK else p2_type_str
        # 加入天元規則提示到初始狀態消息
        if self.move_count == 0 and self.current_player == BLACK:
             self.status_message = f"{player_name}{current_player_type_str} 回合 (請下天元)"
        else:
             self.status_message = f"{player_name}{current_player_type_str} 回合"


    def restart_game(self):
        """重置遊戲到初始狀態，保留玩家類型設置。"""
        p_black = self.player_types[BLACK]
        p_white = self.player_types[WHITE]
        self.__init__(black_player_type=p_black, white_player_type=p_white)


    def pause_game(self):
        """如果遊戲正在進行，則暫停遊戲。"""
        if self.game_state == GameState.PLAYING:
            self.game_state = GameState.PAUSED
            self.pause_start_time = time.time()
            elapsed_since_last_update = self.pause_start_time - self.last_update_time
            self.timers[self.current_player] = max(0, self.timers[self.current_player] - elapsed_since_last_update)
            player_name = "黑方" if self.current_player == BLACK else "白方"
            player_type_str = "(Human)" if self.player_types[self.current_player] == "human" else "(AI)"
            self.status_message = f"{player_name}{player_type_str} 暫停 (按鈕恢復)"
            print("Game Paused")


    def resume_game(self):
        """如果遊戲已暫停，則恢復遊戲。"""
        if self.game_state == GameState.PAUSED and self.pause_start_time is not None:
            pause_duration = time.time() - self.pause_start_time
            self.accumulated_pause_time += pause_duration
            self.last_update_time = time.time()
            self.game_state = GameState.PLAYING
            self.pause_start_time = None
            player_name = "黑方" if self.current_player == BLACK else "白方"
            player_type_str = "(Human)" if self.player_types[self.current_player] == "human" else "(AI)"
            self.status_message = f"{player_name}{player_type_str} 回合"
            print(f"Game Resumed (Paused for {pause_duration:.1f}s)")
        elif self.game_state == GameState.PAUSED:
            self.game_state = GameState.PLAYING
            self.last_update_time = time.time()
            player_name = "黑方" if self.current_player == BLACK else "白方"
            player_type_str = "(Human)" if self.player_types[self.current_player] == "human" else "(AI)"
            self.status_message = f"{player_name}{player_type_str} 回合"
            print("Warning: Resuming game potentially from an inconsistent pause state.")


    def update_timers(self):
        """如果遊戲正在進行，則更新玩家計時器。"""
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
            winner_type_str = "(Human)" if self.player_types[winner] == "human" else "(AI)"
            self.status_message = f"超時! {winner_name}{winner_type_str} 勝!"
            print(f"Timeout! Player {loser} ran out of time.")


    def _is_valid_move(self, r, c, player):
        """檢查 (r, c) 對指定 player 是否為有效且合法的落子點 (邊界, 佔用, 禁手)。"""
        if not is_on_board(r, c) or self.board[r][c] != EMPTY:
            return False, "Occupied or Off-board"

        if player == BLACK:
            # --- 天元規則檢查 (針對黑棋第一步) ---
            if self.move_count == 0 and (r, c) != (7, 7):
                 return False, "First move must be Tengen (7,7)"

            # --- 檢查禁手 (僅對黑棋非第一步) ---
            if self.move_count > 0:
                 self.board[r][c] = player
                 is_win = self.check_win_condition(r, c, player)
                 forbidden_reason = None
                 if not is_win: forbidden_reason = self.check_forbidden_move(r, c)
                 self.board[r][c] = EMPTY
                 if forbidden_reason:
                     return False, forbidden_reason

        # --- 如果前面的檢查都通過了，則是有效的 ---
        return True, None


    def make_move(self, r, c):
        """嘗試為當前玩家在 (r, c) 處落子，加入天元規則。"""
        if self.game_state != GameState.PLAYING:
            self.status_message = "遊戲已結束或暫停"
            return False

        player = self.current_player
        player_name = "黑方" if player == BLACK else "白方"
        player_type_str = "(Human)" if self.player_types[player] == "human" else "(AI)"

        # --- 驗證著法 (包括天元和禁手規則) ---
        is_valid, reason = self._is_valid_move(r, c, player)
        if not is_valid:
             if reason == "First move must be Tengen (7,7)":
                 self.status_message = f"{player_name}{player_type_str} 請下天元 (7, 7)"
                 print(f"Invalid first move attempt at ({r},{c}). Must be (7,7).")
             elif reason == "Occupied or Off-board":
                 self.status_message = f"{player_name}{player_type_str} 無效位置!"
             else: # 禁手情況
                 self.status_message = f"{player_name}{player_type_str} 禁手: {reason}! 請選他處."
                 print(f"Forbidden move attempt by {player_type_str} Black: {reason} at ({r},{c})")
             return False
        # --- 結束驗證 ---


        # --- 執行落子 ---
        self.board[r][c] = player
        self.last_move = (r, c)
        self.move_count += 1

        # --- 記錄和後續檢查 ---
        thinking_time = time.time() - self.current_move_start_time
        self.move_log.append({
            "player": player, "row": r, "col": c,
            "time": round(thinking_time, 1),
            "pause": round(self.accumulated_pause_time, 1)
        })
        self.accumulated_pause_time = 0.0

        if self.check_win_condition(r, c, player):
            self.game_state = GameState.BLACK_WINS if player == BLACK else GameState.WHITE_WINS
            winner = "黑方" if player == BLACK else "白方"
            winner_type = "(Human)" if self.player_types[player] == "human" else "(AI)"
            self.status_message = f"{winner}{winner_type} 連珠五子勝!"
            print(f"Win condition met for {winner}{winner_type} at ({r},{c})")
            return True

        if self.move_count == BOARD_SIZE * BOARD_SIZE:
            self.game_state = GameState.DRAW
            self.status_message = "平局!"
            print("Draw game: Board is full.")
            return True

        self.switch_player() # 交換玩家並更新狀態訊息
        return True


    def switch_player(self):
        """切換當前玩家並更新狀態。"""
        self.current_player = WHITE if self.current_player == BLACK else BLACK
        player_name = "黑方" if self.current_player == BLACK else "白方"
        player_type_str = "(Human)" if self.player_types[self.current_player] == "human" else "(AI)"
        self.status_message = f"{player_name}{player_type_str} 回合"
        # 天元提示由 __init__ 和 make_move 處理

        now = time.time()
        self.last_update_time = now
        self.current_move_start_time = now


    def count_line(self, r, c, player, dr_dc):
        """計算從 (r, c) 開始沿 dr_dc 方向的 'player' 連續棋子數量及開放端點數。"""
        dr, dc = dr_dc
        count = 1
        open_ends = 0
        cr, cc = r + dr, c + dc
        while is_on_board(cr, cc) and self.board[cr][cc] == player:
            count += 1
            cr += dr; cc += dc
        if is_on_board(cr, cc) and self.board[cr][cc] == EMPTY:
            open_ends += 1
        cr, cc = r - dr, c - dc
        while is_on_board(cr, cc) and self.board[cr][cc] == player:
            count += 1
            cr -= dr; cc -= dc
        if is_on_board(cr, cc) and self.board[cr][cc] == EMPTY:
            open_ends += 1
        return count, open_ends


    def check_win_condition(self, r, c, player):
        """檢查在 (r, c) 落子是否為 'player' 帶來勝利。"""
        for dr_dc in DIRECTIONS:
            count, _ = self.count_line(r, c, player, dr_dc)
            if player == BLACK and count == 5:
                return True
            if player == WHITE and count >= 5:
                return True
        return False


    def check_forbidden_move(self, r, c):
        """檢查在 (r, c) 處下黑子是否為禁手 (三三、四四、長連)。
           假設黑子已 *臨時* 放置在棋盤上進行檢查。"""
        player = BLACK
        for dr_dc in DIRECTIONS:
            count, _ = self.count_line(r, c, player, dr_dc);
            if count >= 6: return "長連"
        open_threes_count, fours_count = 0, 0
        for dr_dc in DIRECTIONS:
            is_four, _ = self.check_specific_line(r, c, player, dr_dc, 4)
            if is_four:
                 count_overall, _ = self.count_line(r, c, player, dr_dc)
                 if count_overall == 4: fours_count += 1
            is_three, is_open_three = self.check_specific_line(r, c, player, dr_dc, 3)
            if is_open_three:
                 count_overall, _ = self.count_line(r, c, player, dr_dc)
                 if count_overall == 3: open_threes_count += 1
        if fours_count >= 2: return "四四"
        if open_threes_count >= 2:
             if fours_count < 2: return "三三"
        return None


    def check_specific_line(self, r, c, player, dr_dc, target_count):
        """用於禁手檢查的輔助函數。"""
        dr, dc = dr_dc
        line = []
        new_stone_index = -1
        for i in range(target_count + 1, 0, -1):
            cr, cc = r - i * dr, c - i * dc
            line.append(self.board[cr][cc] if is_on_board(cr, cc) else EDGE)
        line.append(player)
        new_stone_index = len(line) - 1
        for i in range(1, target_count + 2):
            cr, cc = r + i * dr, c + i * dc
            line.append(self.board[cr][cc] if is_on_board(cr, cc) else EDGE)

        found_exact_target_count_line = False
        is_specifically_open_three = False
        for i in range(len(line) - target_count + 1):
            sub_seq = line[i : i + target_count]
            if all(s == player for s in sub_seq):
                if i <= new_stone_index < i + target_count:
                    left_end = line[i - 1] if i > 0 else EDGE
                    right_end = line[i + target_count] if (i + target_count) < len(line) else EDGE
                    is_part_of_longer = (left_end == player or right_end == player)
                    if not is_part_of_longer:
                        found_exact_target_count_line = True
                        if target_count == 3:
                            if left_end == EMPTY and right_end == EMPTY:
                                is_specifically_open_three = True
                                break # Found open three, break inner loop
        if target_count == 3:
            return found_exact_target_count_line, is_specifically_open_three
        else:
            return found_exact_target_count_line, False


    def save_game(self, filename="renju_save.json"):
        """將當前的著法記錄和玩家類型保存到 JSON 文件。"""
        save_data = {
            "move_log": self.move_log,
            "player_black": self.player_types[BLACK],
            "player_white": self.player_types[WHITE]
            }
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
        """從 JSON 文件載入著法記錄並進入分析模式。"""
        try:
            if not os.path.exists(filename):
                self.status_message = f"找不到檔案: {filename}"
                print(f"Load failed: File not found at {filename}")
                return False

            with open(filename, 'r', encoding='utf-8') as f:
                save_data = json.load(f)

            p_black = save_data.get("player_black", "human")
            p_white = save_data.get("player_white", "human")
            self.__init__(black_player_type=p_black, white_player_type=p_white)
            self.move_log = save_data.get("move_log", [])

            p1_type = "(Human)" if self.player_types[BLACK] == "human" else "(AI)"
            p2_type = "(Human)" if self.player_types[WHITE] == "human" else "(AI)"
            mode_str = f"{p1_type} vs {p2_type}"

            if not self.move_log:
                 self.status_message = f"載入空棋譜 ({mode_str}) - 分析模式"
                 print(f"Loaded an empty move log ({mode_str}). Entering Analysis mode.")
            else:
                 self.status_message = f"棋譜載入 ({mode_str}) - 分析模式"
                 print(f"Game loaded successfully from {filename} ({mode_str}). Entering Analysis mode.")

            self.game_state = GameState.ANALYSIS
            self.analysis_step = -1
            self._reconstruct_board_to_step(self.analysis_step)

            return True

        except json.JSONDecodeError as e:
            self.restart_game()
            self.status_message = "載入失敗: 檔案格式錯誤!"
            print(f"Error loading game from {filename}: Invalid JSON format. {e}")
            return False
        except IOError as e:
            self.restart_game()
            self.status_message = "載入失敗: 無法讀取檔案!"
            print(f"Error loading game from {filename}: {e}")
            return False
        except Exception as e:
            self.restart_game()
            self.status_message = "載入時發生未知錯誤!"
            print(f"An unexpected error occurred during loading: {e}")
            return False


    def analysis_navigate(self, direction):
        """在分析模式下導航著法。"""
        if self.game_state != GameState.ANALYSIS or not self.move_log:
            return

        target_step = self.analysis_step
        total_moves = len(self.move_log)

        if direction == 'next': target_step = min(self.analysis_step + 1, total_moves - 1)
        elif direction == 'prev': target_step = max(self.analysis_step - 1, -1)
        elif direction == 'first': target_step = -1
        elif direction == 'last': target_step = total_moves - 1

        if target_step != self.analysis_step:
            self.analysis_step = target_step
            self._reconstruct_board_to_step(self.analysis_step)
            if self.analysis_step == -1:
                 p1_type = "(Human)" if self.player_types[BLACK] == "human" else "(AI)"
                 p2_type = "(Human)" if self.player_types[WHITE] == "human" else "(AI)"
                 self.status_message = f"分析 ({p1_type} vs {p2_type}): 初始局面"
            else:
                 move_num = self.analysis_step + 1
                 player = self.move_log[self.analysis_step].get('player', '?')
                 p_name = "黑" if player == BLACK else "白" if player == WHITE else "?"
                 p_type = "(Human)" if self.player_types.get(player) == "human" else "(AI)" if self.player_types.get(player) == "ai" else ""
                 self.status_message = f"分析: 第 {move_num} 手 ({p_name}{p_type})"


    def _reconstruct_board_to_step(self, target_move_index):
        """內部輔助函數，將 analysis_board 狀態設置為特定著法索引之前的狀態。"""
        self.analysis_board = [[EMPTY for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
        self.last_move = None
        for i in range(target_move_index + 1):
            if i < len(self.move_log):
                move_data = self.move_log[i]
                try:
                    r, c, player = move_data['row'], move_data['col'], move_data['player']
                except KeyError:
                    print(f"警告：在步驟 {i+1} 處的著法數據損壞。停止重建。")
                    if i == target_move_index: self.last_move = None
                    break
                if is_on_board(r, c):
                    if self.analysis_board[r][c] == EMPTY:
                        self.analysis_board[r][c] = player
                        if i == target_move_index: self.last_move = (r, c)
                    else:
                         print(f"警告：在步驟 {i+1} ({r},{c}) 處發現重複落子。棋譜可能無效。")
                         if i == target_move_index: self.last_move = None
                else:
                    print(f"警告：在步驟 {i+1} ({r},{c}) 處發現無效座標。停止重建。")
                    if i == target_move_index: self.last_move = None
                    break


    # --- AI 決策方法 (再次修正 + 更多調試) ---
    def find_best_move(self):
        """AI 尋找最佳著法，加入開局庫、天元規則和啟發式隨機選擇。"""
        if self.game_state != GameState.PLAYING or self.ai_thinking:
            # print(f"Debug: find_best_move returning early. State: {self.game_state}, Thinking: {self.ai_thinking}") # Debug
            return None

        self.ai_thinking = True
        ai_player = self.current_player
        opponent_player = WHITE if ai_player == BLACK else BLACK
        move_to_return = None # 用一個變量存儲最終結果

        try:
            # print(f"\n--- AI ({ai_player}) Starting Turn. move_count={self.move_count} ---") # Debug

            # --- 策略 -1: AI Black First Move ---
            if self.move_count == 0 and ai_player == BLACK:
                is_valid, _ = self._is_valid_move(7, 7, ai_player)
                if is_valid:
                    print(f"AI ({ai_player}) playing mandatory first move at Tengen (7,7)")
                    move_to_return = (7, 7)
                else:
                     print("Error: AI is Black, first move, but Tengen (7,7) is not valid?")
                     move_to_return = None

            # --- 策略 0: Opening Book (Only if not handled above) ---
            if move_to_return is None and self.move_count > 0:
                current_move_sequence = tuple((move['row'], move['col']) for move in self.move_log)
                # print(f"Debug: Checking opening book. Key: {current_move_sequence}") # Debug
                if current_move_sequence in OPENING_BOOK:
                    book_move = OPENING_BOOK[current_move_sequence]
                    # print(f"Debug: Found key in book. Suggested move: {book_move}") # Debug
                    is_valid, reason = self._is_valid_move(book_move[0], book_move[1], ai_player)
                    # print(f"Debug: Book move validity: {is_valid}, Reason: {reason}") # Debug
                    if is_valid:
                        print(f"AI ({ai_player}) using opening book move at {book_move}")
                        move_to_return = book_move
                    else:
                        print(f"AI ({ai_player}) opening book suggested invalid move {book_move}: {reason}. Falling back.")
                # else:
                     # print("Debug: Key not found in opening book.") # Debug


            # --- Strategies 1, 2, 3 (Only if no move found yet) ---
            if move_to_return is None:
                # print("Debug: No book move. Checking win/block/random...") # Debug
                empty_spots = []
                occupied_spots = set()
                for r in range(BOARD_SIZE):
                    for c in range(BOARD_SIZE):
                        if self.board[r][c] == EMPTY:
                            empty_spots.append((r, c))
                        else:
                            occupied_spots.add((r,c))

                if not empty_spots:
                    print(f"AI ({ai_player}) found no empty spots.")
                    move_to_return = None
                else:
                    # 1. Check AI Win
                    # print("Debug: Checking for AI win...") # Debug
                    for r, c in empty_spots:
                        is_valid, _ = self._is_valid_move(r, c, ai_player)
                        if is_valid:
                            self.board[r][c] = ai_player
                            if self.check_win_condition(r, c, ai_player):
                                self.board[r][c] = EMPTY
                                print(f"AI ({ai_player}) found winning move at ({r},{c})")
                                move_to_return = (r, c)
                                break # Exit win check loop
                            self.board[r][c] = EMPTY
                    # if move_to_return: pass # Skip block/random if win found

                    # 2. Check Opponent Win (if no AI win)
                    if move_to_return is None:
                        # print("Debug: Checking for opponent block...") # Debug
                        for r, c in empty_spots:
                            self.board[r][c] = opponent_player
                            opponent_wins_here = self.check_win_condition(r, c, opponent_player)
                            self.board[r][c] = EMPTY
                            if opponent_wins_here:
                                can_block_here, _ = self._is_valid_move(r, c, ai_player)
                                if can_block_here:
                                    print(f"AI ({ai_player}) found opponent win threat at ({r},{c}). Blocking.")
                                    move_to_return = (r, c)
                                    break # Exit block check loop
                        # if move_to_return: pass # Skip random if block found

                    # 3. Adjacent/Random (if no win/block)
                    if move_to_return is None:
                        # print("Debug: Checking for adjacent/random moves...") # Debug
                        candidate_moves = []
                        neighbor_offsets = [(dr, dc) for dr in [-1, 0, 1] for dc in [-1, 0, 1] if not (dr == 0 and dc == 0)]
                        adjacent_empty_spots = set()
                        if not occupied_spots and ai_player == WHITE and self.move_count == 1:
                             # White's first move: check around Tengen
                             if self.board[7][7] == BLACK:
                                for dr, dc in neighbor_offsets:
                                    nr, nc = 7 + dr, 7 + dc
                                    if is_on_board(nr, nc) and self.board[nr][nc] == EMPTY:
                                        adjacent_empty_spots.add((nr, nc))
                             else:
                                  print("Warning: White's first move, but Tengen is not occupied by Black?")
                        else: # Normal case
                             for r_occ, c_occ in occupied_spots:
                                 for dr, dc in neighbor_offsets:
                                     nr, nc = r_occ + dr, c_occ + dc
                                     if is_on_board(nr, nc) and self.board[nr][nc] == EMPTY:
                                         adjacent_empty_spots.add((nr, nc))

                        # Filter adjacent
                        for r_adj, c_adj in adjacent_empty_spots:
                            is_valid, _ = self._is_valid_move(r_adj, c_adj, ai_player)
                            if is_valid:
                                candidate_moves.append((r_adj, c_adj))

                        if candidate_moves:
                            move_to_return = random.choice(candidate_moves)
                            print(f"AI ({ai_player}) chose adjacent move at {move_to_return} from {len(candidate_moves)} adjacent options.")
                        else:
                            # Fallback to all valid moves
                            all_valid_moves = []
                            for r_empty, c_empty in empty_spots:
                                is_valid, _ = self._is_valid_move(r_empty, c_empty, ai_player)
                                if is_valid:
                                    all_valid_moves.append((r_empty, c_empty))
                            if all_valid_moves:
                                move_to_return = random.choice(all_valid_moves)
                                print(f"AI ({ai_player}) no adjacent moves. Chose random valid move at {move_to_return} from {len(all_valid_moves)} total options.")
                            else:
                                print(f"AI ({ai_player}) has no valid moves left (all empty spots are forbidden?)!")
                                move_to_return = None

            # If after all checks, move_to_return is still None
            if move_to_return is None:
                 print(f"Error: AI ({ai_player}) failed to determine a move.") # Error message

        finally:
            self.ai_thinking = False
            # print(f"--- AI ({ai_player}) Finishing Turn. Returning: {move_to_return} ---") # Final Debug

        return move_to_return # Return the decided move (or None)