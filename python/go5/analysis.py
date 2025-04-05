# -*- coding: utf-8 -*-
import logging
from config import (BOARD_SIZE, EMPTY, BLACK, WHITE)
from utils import is_on_board
import os

print(os.getcwd())

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
        self.five_positions = []  # 新增連五列表

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
                row, col, player = data.get('row', -1), data.get('col', -1), data.get('player', 0)
                if is_on_board(row, col):
                    if self.analysis_board[row][col] == EMPTY:  # 這裡不要改動
                        self.analysis_board[row][col] = player
                        self.update_influence_map(player, row, col)  # 傳入下棋者是誰
                        if i == target_idx:
                            self.last_analysis_move = (row, col)
                    else:
                        logger.warning(f"Warn: Analysis Recon Overwrite step {i+1} at ({row},{col})")
                        self.last_analysis_move = None
                        break
                else:
                    logger.warning(f"Warn: Analysis Recon Invalid coord step {i+1} at ({row},{col})")
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
        self.five_positions = self.find_five_positions(self.analysis_board) # 更新連五位置

    # 棋型查找 (Find)
    def find_live_threes(self, board):
        """尋找活三, 並且判斷33"""
        #return self._find_pattern_positions_direction(board, self.check_live_three_direction, "live_three")
        positions = []
        for player in [BLACK, WHITE]:
            for row in range(BOARD_SIZE):
                for col in range(BOARD_SIZE):
                    if self.influence_map[row][col] > 0 and board[row][col] == EMPTY:
                        # 檢查所有方向
                        #print(f"假設玩家下一手點下去的點board[{row}][{col}] = {player}")
                        #print(f"然後去找水平,垂直,正斜,逆斜, 所產生的線，用字串表示0001210表示, 再去找是否有要找的pattern01110之類的")
                        #board[row][col] = player ###先假設他是玩家下一手點下去的點
                        temp_board = self.simulate_move(board,row,col,player)

                        # 统计活三数量
                        live_three_count = 0
                        temp_positions = [] # 临时存储活三位置，不直接修改 positions

                        self.check_live_three_direction(temp_board, row, col, player, 1, 0, temp_positions, "live_three")  # 水平
                        self.check_live_three_direction(temp_board, row, col, player, 0, 1, temp_positions, "live_three")  # 垂直
                        self.check_live_three_direction(temp_board, row, col, player, 1, 1, temp_positions, "live_three")  # 正斜線
                        self.check_live_three_direction(temp_board, row, col, player, 1, -1, temp_positions, "live_three")  # 反斜線

                        #check_func执行后，活三的位置已经记录在 temp_positions
                        live_three_count = len(temp_positions)
                        
                        # 檢查是否形成34
                        if self.check_34(temp_board, row, col, player):
                            print(f"在 ({row}, {col}) 找到 34！")
                            positions.extend(temp_positions)  # 将临时位置添加到最终结果
                        elif live_three_count >= 2:
                            print(f"在 ({row}, {col}) 找到 33！")
                            positions.extend(temp_positions)  # 将临时位置添加到最终结果
        return positions

    def find_jump_live_threes(self, board):
        """尋找跳活三"""
        return self._find_pattern_positions_direction(board, self.check_jump_live_three_direction, "jump_live_three")

    def find_four_positions(self, board):
         """尋找連四"""
         return self._find_pattern_positions_direction(board, self.check_four_direction, "four")

    def find_jump_four_positions(self, board):
        """尋找跳連四"""
        return self._find_pattern_positions_direction(board, self.check_jump_four_direction, "jump_four")

    def find_five_positions(self, board):
        """尋找連五"""
        return self._find_pattern_positions_direction(board, self.check_five_direction, "five")  # 新增連五尋找

    def _find_pattern_positions_direction(self, board, check_func, pattern_type):
        """尋找指定棋型，需要指定方向的通用方法"""
        positions = []
        for player in [BLACK, WHITE]:
            for row in range(BOARD_SIZE):
                for col in range(BOARD_SIZE):
                    if self.influence_map[row][col] > 0 and board[row][col] == EMPTY:
                        # 檢查所有方向
                        #print(f"假設玩家下一手點下去的點board[{row}][{col}] = {player}")
                        #print(f"然後去找水平,垂直,正斜,逆斜, 所產生的線，用字串表示0001210表示, 再去找是否有要找的pattern01110之類的")
                        #board[row][col] = player ###先假設他是玩家下一手點下去的點
                        temp_board = self.simulate_move(board,row,col,player)
                        check_func(temp_board, row, col, player, 1, 0, positions, pattern_type)  # 水平
                        check_func(temp_board, row, col, player, 0, 1, positions, pattern_type)  # 垂直
                        check_func(temp_board, row, col, player, 1, 1, positions, pattern_type)  # 正斜線
                        check_func(temp_board, row, col, player, 1, -1, positions, pattern_type)  # 反斜線
                        #print(f"還原=>假設玩家下一手點下去的點board[{row}][{col}] = {EMPTY}")
                        #board[row][col] = EMPTY
        return positions

    # 棋型檢查 (Check)
    def check_four_direction(self, board, row, col, player, row_dir, col_dir, result_list, pattern_type):
        """檢查指定方向上是否存在連四 (XXXX0 或 0XXXX)"""
        stones_str = self._get_stones_string(board, row, col, row_dir, col_dir)

        # 檢查 XXXX0 和 0XXXX 模式
        pattern1 = f'{player}{player}{player}{player}0'
        pattern2 = f'0{player}{player}{player}{player}'

        if pattern1 in stones_str:
            logger.info(f"在 ({row}, {col}) 方向 ({row_dir}, {col_dir}) 找到連四模式 XXXX0！")
            result_list.append((row, col, player, pattern_type))
            return True

        if pattern2 in stones_str:
            logger.info(f"在 ({row}, {col}) 方向 ({row_dir}, {col_dir}) 找到連四模式 0XXXX！")
            result_list.append((row, col, player, pattern_type))
            return True

        return False

    def check_jump_four_direction(self, board, row, col, player, row_dir, col_dir, result_list, pattern_type):
        """檢查指定方向上是否存在跳連四 (X0XXX、XXX0X 和 XX0XX)"""
        stones_str = self._get_stones_string(board, row, col, row_dir, col_dir)

        # 檢查 X0XXX、XXX0X 和 XX0XX 模式
        pattern1 = f'{player}0{player}{player}{player}'
        pattern2 = f'{player}{player}{player}0{player}'
        pattern3 = f'{player}{player}0{player}{player}'

        if pattern1 in stones_str:
            logger.info(f"在 ({row}, {col}) 方向 ({row_dir}, {col_dir}) 找到跳連四模式 X0XXX！")
            result_list.append((row, col, player, pattern_type))

        if pattern2 in stones_str:
            logger.info(f"在 ({row}, {col}) 方向 ({row_dir}, {col_dir}) 找到跳連四模式 XXX0X！")
            result_list.append((row, col, player, pattern_type))

        if pattern3 in stones_str:
            logger.info(f"在 ({row}, {col}) 方向 ({row_dir}, {col_dir}) 找到跳連四模式 XX0XX！")
            result_list.append((row, col, player, pattern_type))

        return # 確保有返回值

    def check_live_three_direction(self, board, row, col, player, row_dir, col_dir, result_list, pattern_type):
        """檢查指定方向上是否存在活三"""
        stones_str = self._get_stones_string(board, row, col, row_dir, col_dir, length=7)
        pattern = f'0{player}{player}{player}0'
        logger.debug(f"stones3_str={stones_str}, pattern={pattern}")

        if pattern in stones_str:
            logger.info(f"在 ({row}, {col}) 方向 ({row_dir}, {col_dir}) 找到活三模式 0XXX0！")
            result_list.append((row, col, player, pattern_type))

        return #确保所有case都会return

    def check_jump_live_three_direction(self, board, row, col, player, row_dir, col_dir, result_list, pattern_type):
        """檢查指定方向上是否存在跳活三"""
        stones_str = self._get_stones_string(board, row, col, row_dir, col_dir, length=7)
        pattern1 = f'0{player}0{player}{player}0'
        pattern2 = f'0{player}{player}0{player}0'
        logger.debug(f"check_jump_live_three_direction stones_str={stones_str}, pattern1={pattern1}, pattern2={pattern2}")

        if pattern1 in stones_str:
            logger.info(f"在 ({row}, {col}) 方向 ({row_dir}, {col_dir}) 找到跳活三模式 0X0XX0！")
            result_list.append((row, col, player, pattern_type))
        
        if pattern2 in stones_str:
            logger.info(f"在 ({row}, {col}) 方向 ({row_dir}, {col_dir}) 找到跳活三模式 0XX0X0！")
            result_list.append((row, col, player, pattern_type))

        return

    def check_five_direction(self, board, row, col, player, row_dir, col_dir, result_list, pattern_type):
        """檢查指定方向上是否存在連五 (XXXXX)"""
        stones_str = self._get_stones_string(board, row, col, row_dir, col_dir)

        # 檢查 XXXXX 模式
        pattern = f'{player}{player}{player}{player}{player}'

        if pattern in stones_str:
            logger.info(f"在 ({row}, {col}) 方向 ({row_dir}, {col_dir}) 找到連五模式 XXXXX！")
            result_list.append((row, col, player, pattern_type))
            return True

        return False

    def check_34(self, board, row, col, player):
        """檢查在指定位置下子是否會形成34棋型 (同時存在活三和活四/沖四)"""
        # 檢查是否形成活三
        has_live_three = False
        temp_positions = []
        self.check_live_three_direction(board, row, col, player, 1, 0, temp_positions, "live_three")  # 水平
        self.check_live_three_direction(board, row, col, player, 0, 1, temp_positions, "live_three")  # 垂直
        self.check_live_three_direction(board, row, col, player, 1, 1, temp_positions, "live_three")  # 正斜線
        self.check_live_three_direction(board, row, col, player, 1, -1, temp_positions, "live_three")  # 反斜線

        if len(temp_positions) > 0:
            has_live_three = True

        # 檢查是否形成活四或冲四
        has_live_four = False
        has_冲四 = False #待定

        temp_positions2 = []
        self.check_four_direction(board, row, col, player, 1, 0, temp_positions2, "four")  # 水平
        self.check_four_direction(board, row, col, player, 0, 1, temp_positions2, "four")  # 垂直
        self.check_four_direction(board, row, col, player, 1, 1, temp_positions2, "four")  # 正斜線
        self.check_four_direction(board, row, col, player, 1, -1, temp_positions2, "four")  # 反斜線

        if len(temp_positions2) > 0:
            has_live_four = True

        return has_live_three and (has_live_four or has_冲四)

    # 輔助方法
    def _get_stones_string(self, board, row, col, row_dir, col_dir, length=11):
        """獲取指定方向上的棋子字串"""
        stones = []
        start = -(length // 2)
        end = length // 2 + 1

        for i in range(start, end):  # 擴大範圍，檢查更多位置
            r, c = row + i * row_dir, col + i * col_dir
            if is_on_board(r, c):
                stones.append(str(board[r][c]))
            else:
                stones.append('0')  # 超出邊界

        return ''.join(stones)

    def update_influence_map(self, player, x, y):
        """更新影響力地圖"""
        self.analysis_board[x][y] = player
        self.influence_map[x][y] = 9

        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                count = 0
                is_empty = self.analysis_board[r][c] == EMPTY

                if is_empty:  # 只統計空位
                    for i in range(-1, 2):
                        for j in range(-1, 2):
                            if i == 0 and j == 0:  # 排除自身
                                continue

                            neighbor_r, neighbor_c = r + i, c + j
                            if is_on_board(neighbor_r, neighbor_c) and self.analysis_board[neighbor_r][neighbor_c] != EMPTY:
                                count += 1

                    self.influence_map[r][c] = count
                else:  # 不是代表空格，代表有子
                    self.influence_map[r][c] = 9

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

    def get_five_positions(self):
        """獲取連五位置"""
        return self.five_positions  # 新增連五位置獲取

    def simulate_move(self, board, row, col, player):
        """模擬在指定位置下子，並返回新的棋盤狀態"""
        new_board = [row[:] for row in board]  # 複製棋盤
        new_board[row][col] = player
        return new_board