# -*- coding: utf-8 -*-
from config import (BOARD_SIZE, EMPTY, BLACK, WHITE)
from utils import is_on_board

class AnalysisHandler:
    def __init__(self, game_ref):
        self.game = game_ref # Reference to the main game object for move_log, player_types etc.
        self.analysis_step = -1
        self.analysis_board = [[EMPTY for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
        self.last_analysis_move = None # Renamed from self.last_move to avoid confusion

    def navigate(self, direction):
        """Navigates through moves in analysis mode."""
        # Needs access to game.move_log and game.game_state
        if self.game.game_state != self.game.GameState.ANALYSIS or not self.game.move_log:
             print("Analysis Error: Not in analysis mode or no move log.")
             return

        target_step = self.analysis_step
        total_moves = len(self.game.move_log)

        if direction == 'next': target_step = min(self.analysis_step + 1, total_moves - 1)
        elif direction == 'prev': target_step = max(self.analysis_step - 1, -1)
        elif direction == 'first': target_step = -1
        elif direction == 'last': target_step = total_moves - 1

        if target_step != self.analysis_step:
            self.analysis_step = target_step
            self._reconstruct_board(self.analysis_step)
            # Update status message (needs access to game.status_message and player types)
            p1_type = "(H)" if self.game.player_types[BLACK] == "human" else "(AI)"
            p2_type = "(H)" if self.game.player_types[WHITE] == "human" else "(AI)"
            if self.analysis_step == -1:
                 self.game.status_message = f"分析 ({p1_type} vs {p2_type}): 初始局面"
            else:
                 move_num = self.analysis_step + 1
                 move_data = self.game.move_log[self.analysis_step]
                 player = move_data.get('player', '?')
                 p_name = "黑" if player == BLACK else "白" if player == WHITE else "?"
                 p_type = "(H)" if self.game.player_types.get(player) == "human" else "(AI)" if self.game.player_types.get(player) == "ai" else ""
                 self.game.status_message = f"分析: 第 {move_num} 手 ({p_name}{p_type})"


    def _reconstruct_board(self, target_idx):
        """Reconstructs the analysis board state up to a specific move index."""
        # Needs access to game.move_log
        self.analysis_board = [[EMPTY for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
        self.last_analysis_move = None
        for i in range(target_idx + 1):
             if i < len(self.game.move_log):
                 data = self.game.move_log[i]
                 r,c,p = data.get('row',-1), data.get('col',-1), data.get('player',0)
                 if is_on_board(r,c):
                     if self.analysis_board[r][c] == EMPTY:
                         self.analysis_board[r][c] = p
                         if i == target_idx: self.last_analysis_move = (r,c)
                     else: print(f"Warn: Analysis Recon Overwrite step {i+1} at ({r},{c})"); self.last_analysis_move=None; break
                 else: print(f"Warn: Analysis Recon Invalid coord step {i+1} ({r},{c})"); self.last_analysis_move=None; break

    def get_board_to_draw(self):
        """Returns the board to be drawn in analysis mode."""
        return self.analysis_board

    def get_last_move_to_draw(self):
        """Returns the last move to highlight in analysis mode."""
        return self.last_analysis_move