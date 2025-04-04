# analysis.py
# -*- coding: utf-8 -*-
from config import (BOARD_SIZE, EMPTY, BLACK, WHITE)
from utils import is_on_board

class AnalysisHandler:
    def __init__(self, game_ref):
        self.game = game_ref
        self.analysis_step = -1
        self.analysis_board = [[EMPTY for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
        self.last_analysis_move = None
        self.live_three_positions = []
        self.jump_live_three_positions = []
        self.influence_map = [[0 for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]

    def navigate(self, direction):
        if self.game.game_state != self.game.GameState.ANALYSIS or not self.game.move_log:
            print("Analysis Error: Not in analysis mode or no move log.")
            return

    def _reconstruct_board(self, target_idx):
        print("_reconstruct_board called")
        self.analysis_board = [[EMPTY for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
        self.last_analysis_move = None
        self.influence_map = [[0 for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]

        for i in range(target_idx + 1):
            if i < len(self.game.move_log):
                data = self.move_log[i]
                r, c, p = data.get('row', -1), data.get('col', -1), data.get('player', 0)
                if is_on_board(r, c):
                    if self.analysis_board[r][c] == EMPTY:  # 這裡不要改動
                        self.analysis_board[r][c] = p
                        self.update_influence_map()
                        if i == target_idx:
                            self.last_analysis_move = (r, c)
                    else:
                        print(f"Warn: Analysis Recon Overwrite step {i+1} at ({r},{c})")
                        self.last_analysis_move = None
                        break
                else:
                    print(f"Warn: Analysis Recon Invalid coord step {i+1} ({r},{c})")
                    self.last_analysis_move = None
                    break

    def get_board_to_draw(self):
        return self.analysis_board

    def get_last_move_to_draw(self):
        return self.last_analysis_move

    def update_live_three_positions(self):
        self.live_three_positions = self.find_live_threes(self.analysis_board)
        self.jump_live_three_positions = self.find_jump_live_threes(self.analysis_board)

    def find_live_threes(self, board):
        live_threes = []
        for player in [BLACK, WHITE]:
            for row in range(BOARD_SIZE):
                for col in range(BOARD_SIZE):
                    if self.influence_map[row][col] > 0 and board[row][col] == EMPTY:
                        board[row][col] = player
                        if self.is_live_three(board, row, col, player):
                            live_threes.append((row, col, player))
                            print(f"找到活三: ({row}, {col}), 玩家: {player}")
                        board[row][col] = EMPTY
        return live_threes

    def find_jump_live_threes(self, board):
        jump_live_threes = []
        for player in [BLACK, WHITE]:
            for row in range(BOARD_SIZE):
                for col in range(BOARD_SIZE):
                    if self.influence_map[row][col] > 0 and board[row][col] == EMPTY:
                        board[row][col] = player
                        if self.is_jump_live_three(board, row, col, player):
                            jump_live_threes.append((row, col, player))
                            print(f"找到跳活三: ({row}, {col}), 玩家: {player}")
                        board[row][col] = EMPTY
        return jump_live_threes

    def is_live_three(self, board, row, col, player):
        """Checks if placing a stone at (row, col) results in a live three for the given player."""
        # 檢查水平方向
        # print(f"找到跳活三檢查水平方向: ({row}, {col}), 玩家: {player}")
        if self.check_live_three_direction(board, row, col, player, 0, 1):
            return True

        # 檢查垂直方向
        # print(f"找到跳活三檢查垂直方向: ({row}, {col}), 玩家: {player}")
        if self.check_live_three_direction(board, row, col, player, 1, 0):
            return True

        # 檢查正斜線方向
        # print(f"找到跳活三檢查正斜線方向: ({row}, {col}), 玩家: {player}")
        if self.check_live_three_direction(board, row, col, player, 1, 1):
            return True

        # 檢查反斜線方向
        # print(f"找到跳活三檢查反斜線方向: ({row}, {col}), 玩家: {player}")
        if self.check_live_three_direction(board, row, col, player, 1, -1):
            return True

        return False

    def is_jump_live_three(self, board, row, col, player):
        if self.check_jump_live_three_direction(board, row, col, player, 0, 1):
            return True
        if self.check_jump_live_three_direction(board, row, col, player, 1, 0):
            return True
        if self.check_jump_live_three_direction(board, row, col, player, 1, 1):
            return True
        if self.check_jump_live_three_direction(board, row, col, player, 1, -1):
            return True
        return False

    def check_live_three_direction(self, board, row, col, player, row_dir, col_dir):
        # """Helper function to check for live three in a specific direction."""

        # 從 (row, col) 出發，往 row_dir 和 col_dir 兩個方向尋找，總共找 7 個點
        stones = []
        for i in range(-3, 4):
            r, c = row + i * row_dir, col + i * col_dir
            if is_on_board(r, c):
                stones.append(board[r][c])
            else:
                stones.append(0)  # 超出邊界 換成 0

        # 轉為字串方便判斷
        stones_str = ''.join(map(str, stones))
        # print(f"check_live_three_direction" + stones_str)

        # 活三的 pattern，0 代表空格
        pattern = f'0{player}{player}{player}0'
        # print(f"check_live_three_direction" + pattern)

        if pattern in stones_str:
            print(f"在 ({row}, {col}) 方向 ({row_dir}, {col_dir}) 找到活三模式！")
            return True
        else:
            # print(f"在 ({row}, {col}) 方向 ({row_dir}, {col_dir}) 沒找到活三模式")
            return False
    
    def check_jump_live_three_direction(self, board, row, col, player, row_dir, col_dir):
        # """Helper function to check for jump live three in a specific direction."""

        # 從 (row, col) 出發，往 row_dir 和 col_dir 兩個方向尋找，總共找 7 個點
        stones = []
        for i in range(-3, 4):
            r, c = row + i * row_dir, col + i * col_dir
            if is_on_board(r, c):
                stones.append(board[r][c])
            else:
                stones.append(0)  # 超出邊界

        # 轉為字串方便判斷
        stones_str = ''.join(map(str, stones))
        # print(f"check_jump_live_three_direction" + stones_str)

        # 跳活三的 pattern，0 代表空格
        pattern = f'0{player}0{player}{player}0'
        # print(f"check_jump_live_three_direction" + pattern)

        if pattern in stones_str:
            print(f"在 ({row}, {col}) 方向 ({row_dir}, {col_dir}) 找到跳活三模式！")
            return True
        else:
            # print(f"在 ({row}, {col}) 方向 ({row_dir}, {col_dir}) 沒找到跳活三模式")
            return False

    def update_influence_map(self,player,x,y):
        # print(f"更新影響力地圖: ({r}, {c}) 的值設為 9 (有棋子)")
        self.analysis_board[x][y] = player
        self.influence_map[x][y] = 9
        # print(f"更新影響力地圖: ({x}, {y}) elf.influence_map[x][y] = 9")
        # """更新影響力地圖，統計九宮格內棋子數量"""
        # print("update_influence_map called")
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                count = 0
                # 檢查該點是否為空位

                is_empty = self.analysis_board[r][c] == EMPTY
                # if self.analysis_board[r][c] == 9:
                    # self.influence_map[r][c] = 9
                    # print(f"更新影響力地圖: ({r}, {c}) 的值設為 9 (有棋子)")
                    # continue
                # if self.analysis_board[r][c] == EMPTY: #保證只更新沒有棋子的點位
                # print(f"更新影響力地圖: 檢查 ({r}, {c}) 是否为空: {is_empty}")
                # is_empty = self.analysis_board[r][c] == EMPTY
                # if is_empty:  # 只统计空位
                if is_empty:  # 只统计空位
                    for i in range(-1, 2):
                        for j in range(-1, 2):
                            neighbor_r, neighbor_c = r + i, c + j
                            # 排除自身 (新增)
                            if i == 0 and j == 0:
                                continue

                            neighbor_r, neighbor_c = r + i, c + j
                            is_valid = is_on_board(neighbor_r, neighbor_c)
                            # Log
                            #print(f" 檢查 ({r}, {c}) 的鄰居 ({neighbor_r}, {neighbor_c}) 是否有效: {is_valid}")
                            if is_valid:
                                if self.analysis_board[neighbor_r][neighbor_c] != EMPTY:
                                    count += 1
                                    # Log
                                    #print(f" ({neighbor_r}, {neighbor_c}) 有棋子，count 增加到 {count}")
                    
                    if self.analysis_board[r][c] == EMPTY: #代表無子
                        self.influence_map[r][c] = count
                        # print(f"更新影響力地圖: ({r}, {c}) 的值為 {self.influence_map[r][c]}")
                
                else: #不是代表空格，代表有子
                    self.influence_map[r][c] = 9
                    # print(f"更新影響力地圖: ({r}, {c}) 的值設為 9 (有棋子)")
                    pass

    def get_live_three_positions(self):
        return self.live_three_positions

    def get_jump_live_three_positions(self):
        return self.jump_live_three_positions