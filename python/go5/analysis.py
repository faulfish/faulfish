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
        if self.check_live_three_direction(board, row, col, player, 0, 1):
            return True
        if self.check_live_three_direction(board, row, col, player, 1, 0):
            return True
        if self.check_live_three_direction(board, row, col, player, 1, 1):
            return True
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
        count = 0
        empty_count = 0
        pattern_found = False # 检查标志

        # 构建包含目标位置在内的 5 个棋子的潜在序列
        stones = []
        for i in range(-2, 3):  # 从目标位置向前和向后检查 2 个位置
            r, c = row + i * row_dir, col + i * col_dir
            if is_on_board(r, c):
                stone = board[r][c]
                stones.append(stone)
            else:
                stones.append(-1)  # Use -1 to indicate out-of-bounds

        # 检查活三模式 [EMPTY, player, player, player, EMPTY]
        pattern = [EMPTY, player, player, player, EMPTY]

        # 确保线段的长度至少为 5
        if len(stones) == 5:
            # 检查石头是否与模式匹配
            valid = True
            for i in range(5):
                if stones[i] != pattern[i]:
                    valid = False
                    break

            if valid:
                print(f"({row}, {col}) 在方向 ({row_dir}, {col_dir}) 上找到活三模式")
                return True
        else:
             print(f"({row}, {col}) 在方向 ({row_dir}, {col_dir}) 上，长度不足 {len(stones)}")

        # 如果没有发现活三模式，则返回 False
        return False

    def check_jump_live_three_direction(self, board, row, col, player, row_dir, col_dir):
        return False  # 暫時不處理跳活三

    def update_influence_map(self,player,x,y):
        # print(f"更新影響力地圖: ({r}, {c}) 的值設為 9 (有棋子)")
        self.analysis_board[x][y] = player
        self.influence_map[x][y] = 9
        print(f"更新影響力地圖: ({x}, {y}) elf.influence_map[x][y] = 9")
        # """更新影響力地圖，統計九宮格內棋子數量"""
        print("update_influence_map called")
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
                        print(f"更新影響力地圖: ({r}, {c}) 的值為 {self.influence_map[r][c]}")
                
                else: #不是代表空格，代表有子
                    self.influence_map[r][c] = 9
                    print(f"更新影響力地圖: ({r}, {c}) 的值設為 9 (有棋子)")
                    pass

    def get_live_three_positions(self):
        return self.live_three_positions

    def get_jump_live_three_positions(self):
        return self.jump_live_three_positions