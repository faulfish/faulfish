# -*- coding: utf-8 -*-
import logging
from config import (BOARD_SIZE, EMPTY, BLACK, WHITE)
from utils import is_on_board

# 設定 logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


class AnalysisHandler:
    """五子棋分析處理器"""

    def __init__(self, game_ref):
        """初始化分析處理器"""
        self.game = game_ref
        self.analysis_step = -1
        self.analysis_board = [[EMPTY for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
        self.last_analysis_move = None

        # 棋型列表
        self.live_three_positions = []
        self.jump_live_three_positions = []
        self.four_positions = []
        self.jump_four_positions = []

        self.influence_map = [[0 for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]

    def navigate(self, direction):
        """在分析模式下導航步數"""
        if self.game.game_state != self.game.GameState.ANALYSIS or not self.game.move_log:
            logger.warning("Analysis Error: Not in analysis mode or no move log.")
            return

        # TODO: 實現 navigate 方法
        pass

    def _reconstruct_board(self, target_idx):
        """重建指定步數的棋盤狀態"""
        logger.info("_reconstruct_board called")
        self.analysis_board = [[EMPTY for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
        self.last_analysis_move = None
        self.influence_map = [[0 for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]

        for i in range(target_idx + 1):
            if i < len(self.game.move_log):
                data = self.game.move_log[i]  # 使用 self.game.move_log
                r, c, p = data.get('row', -1), data.get('col', -1), data.get('player', 0)
                if is_on_board(r, c):
                    if self.analysis_board[r][c] == EMPTY:  # 這裡不要改動
                        self.analysis_board[r][c] = p
                        self.update_influence_map(p,r,c) #傳入下棋者是誰
                        if i == target_idx:
                            self.last_analysis_move = (r, c)
                    else:
                        logger.warning(f"Warn: Analysis Recon Overwrite step {i+1} at ({r},{c})")
                        self.last_analysis_move = None
                        break
                else:
                    logger.warning(f"Warn: Analysis Recon Invalid coord step {i+1} ({r},{c})")
                    self.last_analysis_move = None
                    break

    def get_board_to_draw(self):
        """獲取用於繪製的棋盤"""
        return self.analysis_board

    def get_last_move_to_draw(self):
        """獲取最後分析的落子位置"""
        return self.last_analysis_move

    def update_live_three_positions(self):
        """更新活三和跳活三的位置"""
        self.live_three_positions = self.find_live_threes(self.analysis_board)
        self.jump_live_three_positions = self.find_jump_live_threes(self.analysis_board)

    def update_live_four_positions(self):
        """更新連四和跳連四的位置"""
        self.four_positions = self.find_four_positions(self.analysis_board)
        self.jump_four_positions = self.find_jump_four_positions(self.analysis_board)

    # 棋型查找 (Find)
    def find_live_threes(self, board):
        """尋找活三"""
        live_threes = []
        for player in [BLACK, WHITE]:
            for row in range(BOARD_SIZE):
                for col in range(BOARD_SIZE):
                    if self.influence_map[row][col] > 0 and board[row][col] == EMPTY:
                        board[row][col] = player
                        if self.is_live_three(board, row, col, player):
                            live_threes.append((row, col, player))
                            logger.info(f"找到活三: ({row}, {col}), 玩家: {player}")
                        board[row][col] = EMPTY
        return live_threes

    def find_jump_live_threes(self, board):
        """尋找跳活三"""
        jump_live_threes = []
        for player in [BLACK, WHITE]:
            for row in range(BOARD_SIZE):
                for col in range(BOARD_SIZE):
                    if self.influence_map[row][col] > 0 and board[row][col] == EMPTY:
                        board[row][col] = player
                        if self.is_jump_live_three(board, row, col, player):
                            jump_live_threes.append((row, col, player))
                            logger.info(f"找到跳活三: ({row}, {col}), 玩家: {player}")
                        board[row][col] = EMPTY
        return jump_live_threes

    def find_four_positions(self, board):
        """尋找連四"""
        fours = []
        logger.info("find_four_positions: 掃描棋盤以尋找連四")
        for player in [BLACK, WHITE]:
            for r in range(BOARD_SIZE):
                for c in range(BOARD_SIZE):
                    if self.influence_map[r][c] > 0 and board[r][c] == EMPTY:
                        # 檢查所有方向
                        self.check_four_direction(board, r, c, player, 1, 0, fours)  # 水平
                        self.check_four_direction(board, r, c, player, 0, 1, fours)  # 垂直
                        self.check_four_direction(board, r, c, player, 1, 1, fours)  # 正斜線
                        self.check_four_direction(board, r, c, player, 1, -1, fours)  # 反斜線
        return fours

    def find_jump_four_positions(self, board):
        """尋找跳連四"""
        jump_fours = []
        logger.info("find_jump_four_positions: 掃描棋盤以尋找跳連四")
        print("find_jump_four_positions: 掃描棋盤以尋找跳連四")
        for player in [BLACK, WHITE]:
            for r in range(BOARD_SIZE):
                for c in range(BOARD_SIZE):
                    if self.influence_map[r][c] > 0 and board[r][c] == EMPTY:
                        # 檢查所有方向
                        self.check_jump_four_direction(board, r, c, player, 1, 0, jump_fours)  # 水平
                        self.check_jump_four_direction(board, r, c, player, 0, 1, jump_fours)  # 垂直
                        self.check_jump_four_direction(board, r, c, player, 1, 1, jump_fours)  # 正斜線
                        self.check_jump_four_direction(board, r, c, player, 1, -1, jump_fours)  # 反斜線
        return jump_fours

    # 棋型檢查 (Check)
    def check_four_direction(self, board, row, col, player, row_dir, col_dir, result_list):
        """
        檢查指定方向上是否存在連四 (XXXX0 或 0XXXX)
        """
        stones_str = self._get_stones_string(board, row, col, row_dir, col_dir)

        # 檢查 XXXX0 和 0XXXX 模式
        pattern1 = f'{player}{player}{player}{player}0'
        pattern2 = f'0{player}{player}{player}{player}'

        if pattern1 in stones_str:
            index = stones_str.find(pattern1)
            r, c = row + (index - 5 + 4) * row_dir, col + (index - 5 + 4) * col_dir
            logger.info(f"在 ({row}, {col}) 方向 ({row_dir}, {col_dir}) 找到連四模式 XXXX0！")
            print(f"在 ({row}, {col}) 方向 ({row_dir}, {col_dir}) 找到連四模式 XXXX0！")
            # result_list.append(((row, col), (r, c), player, "four"))
            result_list.append((row, col, player))
            return True

        if pattern2 in stones_str:
            index = stones_str.find(pattern2)
            r, c = row + (index - 5) * row_dir, col + (index - 5) * col_dir
            logger.info(f"在 ({row}, {col}) 方向 ({row_dir}, {col_dir}) 找到連四模式 0XXXX！")
            print(f"在 ({row}, {col}) 方向 ({row_dir}, {col_dir}) 找到連四模式 0XXXX！")
            #result_list.append(((row, col), (r, c), player, "four"))
            result_list.append((row, col, player))
            return True

        return False

    def check_jump_four_direction(self, board, row, col, player, row_dir, col_dir, result_list):
        """
        檢查指定方向上是否存在跳連四 (X0XXX、XXX0X 和 XX0XX)
        """
        stones_str = self._get_stones_string(board, row, col, row_dir, col_dir)

        # 檢查 X0XXX、XXX0X 和 XX0XX 模式
        pattern1 = f'{player}0{player}{player}{player}'
        pattern2 = f'{player}{player}{player}0{player}'
        pattern3 = f'{player}{player}0{player}{player}'

        if pattern1 in stones_str:
            index = stones_str.find(pattern1)
            r, c = row + (index - 5 + 1) * row_dir, col + (index - 5 + 1) * col_dir # 0的位置
            logger.info(f"在 ({row}, {col}) 方向 ({row_dir}, {col_dir}) 找到跳連四模式 X0XXX！")
            #result_list.append(((row, col), (r, c), player, "jump_four"))
            result_list.append((row, col, player))

        if pattern2 in stones_str:
            index = stones_str.find(pattern2)
            r, c = row + (index - 5 + 3) * row_dir, col + (index - 5 + 3) * col_dir # 0的位置
            logger.info(f"在 ({row}, {col}) 方向 ({row_dir}, {col_dir}) 找到跳連四模式 XXX0X！")
            #result_list.append(((row, col), (r, c), player, "jump_four"))
            result_list.append((row, col, player))

        if pattern3 in stones_str:
            index = stones_str.find(pattern3)
            r, c = row + (index - 5 + 2) * row_dir, col + (index - 5 + 2) * col_dir # 0的位置
            logger.info(f"在 ({row}, {col}) 方向 ({row_dir}, {col_dir}) 找到跳連四模式 XX0XX！")
            #result_list.append(((row, col), (r, c), player, "jump_four"))
            result_list.append((row, col, player))

    def check_live_three_direction(self, board, row, col, player, row_dir, col_dir):
        """檢查指定方向上是否存在活三"""
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
        # 活三的 pattern，0 代表空格
        pattern = f'0{player}{player}{player}0'
        logger.debug(f"stones3_str={stones_str}, pattern={pattern}")

        if pattern in stones_str:
            logger.info(f"在 ({row}, {col}) 方向 ({row_dir}, {col_dir}) 找到活三模式！")
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
            logger.info(f"在 ({row}, {col}) 方向 ({row_dir}, {col_dir}) 找到跳活三模式！")
            return True
        else:
            # print(f"在 ({row}, {col}) 方向 ({row_dir}, {col_dir}) 沒找到跳活三模式")
            return False

    # 輔助方法
    def _get_stones_string(self, board, row, col, row_dir, col_dir):
        """獲取指定方向上的棋子字串"""
        stones = []
        for i in range(-5, 6):  # 擴大範圍，檢查更多位置
            r, c = row + i * row_dir, col + i * col_dir
            if is_on_board(r, c):
                stones.append(board[r][c])
            else:
                stones.append(0)  # 超出邊界

        return ''.join(map(str, stones))

    # 其他方法
    def navigate(self, direction):
        """在分析模式下導航步數"""
        if self.game.game_state != self.game.GameState.ANALYSIS or not self.game.move_log:
            logger.warning("Analysis Error: Not in analysis mode or no move log.")
            return

    def _reconstruct_board(self, target_idx):
        """重建指定步數的棋盤狀態"""
        logger.info("_reconstruct_board called")
        self.analysis_board = [[EMPTY for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
        self.last_analysis_move = None
        self.influence_map = [[0 for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]

        for i in range(target_idx + 1):
            if i < len(self.game.move_log):
                data = self.game.move_log[i] #使用 self.game.move_log
                r, c, p = data.get('row', -1), data.get('col', -1), data.get('player', 0)
                if is_on_board(r, c):
                    if self.analysis_board[r][c] == EMPTY:  # 這裡不要改動
                        self.analysis_board[r][c] = p
                        self.update_influence_map(p,r,c) #傳入下棋者是誰
                        if i == target_idx:
                            self.last_analysis_move = (r, c)
                    else:
                        logger.warning(f"Warn: Analysis Recon Overwrite step {i+1} at ({r},{c})")
                        self.last_analysis_move = None
                        break
                else:
                    logger.warning(f"Warn: Analysis Recon Invalid coord step {i+1} ({r},{c})")
                    self.last_analysis_move = None
                    break

    def get_board_to_draw(self):
        """獲取用於繪製的棋盤"""
        return self.analysis_board

    def get_last_move_to_draw(self):
        """獲取最後分析的落子位置"""
        return self.last_analysis_move

    def update_live_three_positions(self):
        """更新活三和跳活三的位置"""
        self.live_three_positions = self.find_live_threes(self.analysis_board)
        self.jump_live_three_positions = self.find_jump_live_threes(self.analysis_board)

    def update_live_four_positions(self):
        """更新連四和跳連四的位置"""
        self.four_positions = self.find_four_positions(self.analysis_board)
        self.jump_four_positions = self.find_jump_four_positions(self.analysis_board)

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

    def update_influence_map(self,player,x,y):
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

    # getter 方法
    def get_live_three_positions(self):
        """獲取活三位置"""
        return self.live_three_positions

    def get_jump_live_three_positions(self):
        """獲取跳活三位置"""
        return self.jump_live_three_positions

    def get_four_positions(self):
        """獲取連四位置"""
        return self.four_positions

    def get_jump_four_positions(self):
        """獲取跳連四位置"""
        return self.jump_four_positions