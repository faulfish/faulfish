# -*- coding: utf-8 -*-
import time
import random
from config import (GameState, BOARD_SIZE, EMPTY, BLACK, WHITE, DEFAULT_TIME_LIMIT)
# --- 導入拆分後的模塊 ---
import rules
import ai_player  # Handles find_best_move and learn_from_loss
import game_io  # Handles save/load game and book I/O
from analysis import AnalysisHandler

class RenjuGame:
    """處理 Renju 遊戲的核心邏輯、狀態和規則，委託具體實現給其他模塊。"""

    def __init__(self, black_player_type="human", white_player_type="ai"):
        """初始化遊戲。"""
        # 注意：OPENING_BOOK 由 game_io 在加載時處理，這裡不需要 global
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
        self.player_types = {BLACK: black_player_type, WHITE: white_player_type}
        self.ai_thinking = False
        self.analysis_handler = AnalysisHandler(self)
        self._update_status_message()

    def _update_status_message(self):
        """根據當前狀態更新 status_message。"""
        if self.game_state == GameState.PLAYING:
            player_name = "黑方" if self.current_player == BLACK else "白方"
            player_type_str = "(H)" if self.player_types[self.current_player] == "human" else "(AI)"
            if self.move_count == 0 and self.current_player == BLACK:
                self.status_message = f"{player_name}{player_type_str} 回合 (請下天元)"
            else:
                self.status_message = f"{player_name}{player_type_str} 回合"
        elif self.game_state == GameState.PAUSED:
            player_name = "黑方" if self.current_player == BLACK else "白方"
            player_type_str = "(H)" if self.player_types[self.current_player] == "human" else "(AI)"
            self.status_message = f"{player_name}{player_type_str} 暫停 (按鈕恢復)"
        elif self.game_state == GameState.BLACK_WINS:
            player_type_str = "(H)" if self.player_types[BLACK] == "human" else "(AI)"
            self.status_message = f"黑方{player_type_str} 勝!"
        elif self.game_state == GameState.WHITE_WINS:
            player_type_str = "(H)" if self.player_types[WHITE] == "human" else "(AI)"
            self.status_message = f"白方{player_type_str} 勝!"
        elif self.game_state == GameState.DRAW:
            self.status_message = "平局!"
        # Analysis message handled by AnalysisHandler

    def restart_game(self):
        black_player_type = self.player_types[BLACK]
        white_player_type = self.player_types[WHITE]
        self.__init__(black_player_type=black_player_type, white_player_type=white_player_type)

    def pause_game(self):
        if self.game_state == GameState.PLAYING:
            self.game_state = GameState.PAUSED
            self.pause_start_time = time.time()
            elapsed = self.pause_start_time - self.last_update_time
            self.timers[self.current_player] = max(0, self.timers[self.current_player] - elapsed)
            self._update_status_message()
            print("Game Paused")

    def resume_game(self):
        if self.game_state == GameState.PAUSED and self.pause_start_time is not None:
            paused = time.time() - self.pause_start_time
            self.accumulated_pause_time += paused
            self.last_update_time = time.time()
            self.game_state = GameState.PLAYING
            self.pause_start_time = None
            self._update_status_message()
            print(f"Resumed (Paused {paused:.1f}s)")
        elif self.game_state == GameState.PAUSED:
            self.game_state = GameState.PLAYING
            self.last_update_time = time.time()
            self._update_status_message()
            print("Warn: Resuming inconsistent pause.")

    def update_timers(self):
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
            l_type = "(H)" if self.player_types[loser] == "human" else "(AI)"
            print(f"Timeout! Player {loser} ({l_type}) lost.")
            self._update_status_message()  # Update status based on new game state

            if self.player_types[loser] == "ai":
                print(f"AI {loser} lost by timeout. Learning...")
                # --- 調用 ai_player 模塊的學習函數 ---
                ai_player.ai_player.learn_from_ai_loss(self.move_log, self.player_types)
                # --- 結束調用 ---

    def make_move(self, r, c):
        # print(f"game_logic make_move {r},{c}")
        if self.game_state != GameState.PLAYING:
            self.status_message = "遊戲已結束或暫停"
            return False

        player = self.current_player
        print(f"[GAME DEBUG] make_move({r},{c}), player={player}, move_count={self.move_count}") #<-- 添加
        # --- 使用 rules 模塊驗證 ---
        valid, reason = rules.is_legal_move(r, c, player, self.move_count, self.board)
        print(f"[GAME DEBUG] rules.is_legal_move returned: valid={valid}, reason='{reason}'") #<-- 添加
        if not valid:
            print(f"[GAME DEBUG] Move determined invalid. Returning False.") #<-- 添加
            player_name = "黑方" if player == BLACK else "白方"
            player_type_str = "(H)" if self.player_types[player] == "human" else "(AI)"
            if reason == "First move must be Tengen (7,7)":
                self.status_message = f"{player_name}{player_type_str} 請下天元 (7, 7)"
            elif reason == "Occupied or Off-board":
                self.status_message = f"{player_name}{player_type_str} 無效位置!"
            else:
                self.status_message = f"{player_name}{player_type_str} 禁手: {reason}! 請選他處."
            print(f"Invalid move by {player_name}{player_type_str} at ({r},{c}): {reason}")
            return False

        # Execute move
        self.board[r][c] = player
        self.last_move = (r, c)
        self.move_count += 1
        log = {
            "player": player,
            "row": r,
            "col": c,
            "time": round(time.time() - self.current_move_start_time, 1),
            "pause": round(self.accumulated_pause_time, 1)
        }
        self.move_log.append(log)
        self.accumulated_pause_time = 0.0

        # 更新影響力地圖 (新增)
        self.analysis_handler.update_influence_map(player, r, c)  # 更新周圍點位

        # Check win/draw using rules module
        if rules.check_win_condition_at(r, c, player, self.board):
            self.game_state = GameState.BLACK_WINS if player == BLACK else GameState.WHITE_WINS
            loser = WHITE if player == BLACK else BLACK
            player_name = "黑方" if player == BLACK else "白方"
            player_type_str = "(H)" if self.player_types[player] == "human" else "(AI)"
            print(f"Win for {player_name}{player_type_str} at ({r},{c})")
            self._update_status_message()

            if self.player_types[loser] == "ai":
                print(f"AI {loser} lost. Learning...")
                # --- 調用 ai_player 模塊的學習函數 ---
                ai_player.ai_player.learn_from_ai_loss(self.move_log, self.player_types)
                # --- 結束調用 ---
            return True

        if self.move_count == BOARD_SIZE * BOARD_SIZE:
            self.game_state = GameState.DRAW
            print("Draw game.")
            self._update_status_message()
            return True

        self.switch_player()
        # 在移動後更新活三和跳活三的位置（遊戲進行中）
        self.analysis_handler.update_live_three_positions()
        # print(f"update_live_four_positions...")
        self.analysis_handler.update_live_four_positions()
        return True

    def switch_player(self):
        self.current_player = WHITE if self.current_player == BLACK else BLACK
        self.last_update_time = time.time()
        self.current_move_start_time = self.last_update_time
        self._update_status_message()  # 更新狀態消息

    # --- AI move ---
    def request_ai_move(self):
        """請求 AI 計算下一步著法。"""
        if self.game_state != GameState.PLAYING or self.player_types[self.current_player] != "ai":
            return None, False

        # 調用 ai_player 模塊的函數
        move, used_book = ai_player.ai_player.find_best_ai_move(  # 使用 ai_player 實例
            self.board, self.move_log, self.move_count, self.current_player, self.analysis_handler  # 傳入 self.analysis_handler
        )
        return move, used_book

    # --- Save/Load ---
    def save_game(self, filename=None):
        """保存遊戲狀態。"""
        fname = filename if filename else game_io.SAVE_GAME_FILE
        success, msg = game_io.save_game_data(self.move_log, self.player_types, fname)
        self.status_message = msg  # 更新狀態消息以反映保存結果

    def load_game(self, filename=None):
        """加載遊戲狀態，並進入分析模式。"""
        fname = filename if filename else game_io.SAVE_GAME_FILE
        # game_io 負責重新加載開局庫
        move_log_loaded, types_loaded, msg = game_io.load_game_data(fname)
        if move_log_loaded is not None:
            # Re-initialize the current game object with loaded data
            self.__init__(black_player_type=types_loaded[BLACK], white_player_type=types_loaded[WHITE])
            self.move_log = move_log_loaded
            self.game_state = GameState.ANALYSIS
            # Reset analysis state via handler
            self.analysis_handler.analysis_step = -1
            self.analysis_handler._reconstruct_board(self.analysis_handler.analysis_step)
            # Update status message based on loaded mode
            p1 = "(H)" if self.player_types[BLACK] == "human" else "(AI)"
            p2 = "(H)" if self.player_types[WHITE] == "human" else "(AI)"
            mode = f"{p1} vs {p2}"
            m = f"載入空棋譜 ({mode})" if not self.move_log else f"棋譜載入 ({mode})"
            self.status_message = f"{m} - 分析模式"
            print(f"Loaded {fname} ({mode}). Analysis.")
            return True
        else:
            self.restart_game()  # Reset to default if load fails
            self.status_message = msg
            print(f"Error loading: {msg}")
            return False

    # --- Analysis Navigation ---
    def analysis_navigate(self, direction):
        """委託給 AnalysisHandler 處理。"""
        if self.game_state == GameState.ANALYSIS:
            self.analysis_handler.navigate(direction)  # navigate 內部會更新 status_message

    # --- Getters for Drawing ---
    def get_board_to_draw(self):
        """根據遊戲狀態返回要繪製的棋盤。"""
        if self.game_state == GameState.ANALYSIS:
            return self.analysis_handler.get_board_to_draw()
        else:
            return self.board

    def get_last_move_to_draw(self):
        """根據遊戲狀態返回要高亮的最後一步棋。"""
        if self.game_state == GameState.ANALYSIS:
            return self.analysis_handler.get_last_move_to_draw()
        else:
            return self.last_move

    def get_live_three_positions(self,player):
        """Returns the list of live three positions to draw."""
        return self.analysis_handler.live_three_positions

    def get_jump_live_three_positions(self,player):
        """Returns the list of jump live three positions to draw."""
        return self.analysis_handler.jump_live_three_positions

    def get_live_four_positions(self,player):
        """Returns the list of live four positions to draw."""
        return self.analysis_handler.four_positions

    def get_jump_four_positions(self,player):
        """Returns the list of jump four positions to draw."""
        return self.analysis_handler.jump_four_positions

    def get_five_positions(self,player):
        """Returns the list of five positions to draw."""
        return self.analysis_handler.five_positions