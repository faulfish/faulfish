# -*- coding: utf-8 -*-
import logging
from config import (BOARD_SIZE, EMPTY, BLACK, WHITE)
from utils import is_on_board
import os
import rules # 確保導入 rules

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

        # --- 修改數據結構：使用字典區分玩家 ---
        self.live_three_positions = {BLACK: [], WHITE: []}
        self.jump_live_three_positions = {BLACK: [], WHITE: []}
        self.four_positions = {BLACK: [], WHITE: []}
        self.jump_four_positions = {BLACK: [], WHITE: []}
        self.five_positions = {BLACK: [], WHITE: []}
        # 可以考慮為 33 和 34 也創建專門的存儲，如果需要精確區分
        self.three_three_positions = {BLACK: [], WHITE: []}
        self.three_four_positions = {BLACK: [], WHITE: []}

        self.influence_map = [[0 for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]

    # ... (navigate, _reconstruct_board, get_board_to_draw, get_last_move_to_draw 保持不變) ...
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
        # --- find_... 方法現在返回字典 ---
        self.live_three_positions = self.find_live_threes(self.analysis_board)
        self.jump_live_three_positions = self.find_jump_live_threes(self.analysis_board)
        logger.info(f"Updated Live Threes: B:{len(self.live_three_positions[BLACK])}, W:{len(self.live_three_positions[WHITE])}")
        logger.info(f"Updated Jump Live Threes: B:{len(self.jump_live_three_positions[BLACK])}, W:{len(self.jump_live_three_positions[WHITE])}")


    def update_live_four_positions(self):
        """更新連四和跳連四的位置"""
         # --- find_... 方法現在返回字典 ---
        self.four_positions = self.find_four_positions(self.analysis_board)
        self.jump_four_positions = self.find_jump_four_positions(self.analysis_board)
        self.five_positions = self.find_five_positions(self.analysis_board) # 更新連五位置
        logger.info(f"Updated Fours: B:{len(self.four_positions[BLACK])}, W:{len(self.four_positions[WHITE])}")
        logger.info(f"Updated Jump Fours: B:{len(self.jump_four_positions[BLACK])}, W:{len(self.jump_four_positions[WHITE])}")
        logger.info(f"Updated Fives: B:{len(self.five_positions[BLACK])}, W:{len(self.five_positions[WHITE])}")


    # --- 修改 find_live_threes ---
    def find_live_threes(self, board): 
        """尋找活三, 過濾黑方禁手"""
        positions = {BLACK: [], WHITE: []}
        current_board = board 
        current_move_count = self.game.move_count # 從 game_ref 獲取當前步數

        for player in [BLACK, WHITE]:
            player_positions_set = set()
            for row in range(BOARD_SIZE):
                for col in range(BOARD_SIZE):
                    if self.influence_map[row][col] > 0 and current_board[row][col] == EMPTY: # 使用當前棋盤檢查空點
                        temp_board = self.simulate_move(current_board, row, col, player) # 模擬落子
                        temp_spot_positions = [] # 收集此點的活三

                        # 檢查活三方向...
                        self.check_live_three_direction(temp_board, row, col, player, 1, 0, temp_spot_positions, "live_three")
                        self.check_live_three_direction(temp_board, row, col, player, 0, 1, temp_spot_positions, "live_three")
                        self.check_live_three_direction(temp_board, row, col, player, 1, 1, temp_spot_positions, "live_three")
                        self.check_live_three_direction(temp_board, row, col, player, 1, -1, temp_spot_positions, "live_three")

                        if temp_spot_positions:
                            # --- 在這裡加入禁手過濾 ---
                            if player == BLACK:
                                # 檢查 (row, col) 對於黑方是否為禁手
                                is_valid, reason = rules.is_legal_move(row, col, BLACK, current_move_count, temp_board)
                                if not is_valid:
                                    # print(f"find_live_threes {row},{col} reason is {reason}")
                                    continue # 如果是禁手，則不將此點加入活三列表

                            # --- 如果不是黑方禁手，或者玩家是白方 ---
                            # print(f"find_live_threes add {row},{col} in live_three")
                            player_positions_set.add((row, col, player, "live_three"))
                            # ... (可選的 33/34 檢測邏輯) ...

            positions[player] = list(player_positions_set)
        return positions

    def find_jump_live_threes(self, board):
        """尋找跳活三"""
        # 使用通用方法，傳遞 check_jump_live_three_direction
        return self._find_pattern_positions_direction(board, self.check_jump_live_three_direction, "jump_live_three")

    def find_four_positions(self, board):
         """尋找連四"""
         # 使用通用方法，傳遞 check_four_direction
         return self._find_pattern_positions_direction(board, self.check_four_direction, "four")

    def find_jump_four_positions(self, board):
        """尋找跳連四"""
        # 使用通用方法，傳遞 check_jump_four_direction
        return self._find_pattern_positions_direction(board, self.check_jump_four_direction, "jump_four")

    def find_five_positions(self, board):
        """尋找連五"""
         # 使用通用方法，傳遞 check_five_direction
        return self._find_pattern_positions_direction(board, self.check_five_direction, "five")

    # --- 修改通用查找方法以返回字典 ---
    def _find_pattern_positions_direction(self, board, check_func, pattern_type):
        """尋找指定棋型，需要指定方向的通用方法，返回按玩家區分的字典"""
        # print(f"_find_pattern_positions_direction...{check_func}111")
        positions = {BLACK: [], WHITE: []}
        for player in [BLACK, WHITE]:
            player_positions_set = set() # 使用 set 去重
            for row in range(BOARD_SIZE):
                for col in range(BOARD_SIZE):
                    # 考慮在有影響力的空點落子
                    #if self.influence_map[row][col] > 0 and board[row][col] == EMPTY:
                    if board[row][col] == EMPTY:
                        temp_board = self.simulate_move(board, row, col, player)
                        # check_func 會修改 player_positions_set (需要調整 check_func 或這裡的邏輯)
                        # 更好的方式是 check_func 將結果添加到一個臨時列表，然後在這裡添加到 set
                        # print(f"_find_pattern_positions_direction...{check_func}")
                        temp_spot_positions = []
                        check_func(temp_board, row, col, player, 1, 0, temp_spot_positions, pattern_type)  # 水平
                        check_func(temp_board, row, col, player, 0, 1, temp_spot_positions, pattern_type)  # 垂直
                        check_func(temp_board, row, col, player, 1, 1, temp_spot_positions, pattern_type)  # 正斜線
                        check_func(temp_board, row, col, player, 1, -1, temp_spot_positions, pattern_type)  # 反斜線

                        # 將從這個 (row, col) 點找到的所有 pattern 加入集合
                        # 注意 check_func 可能會因為不同方向找到同一個模式而多次添加同一個元組，set 會處理
                        for pos in temp_spot_positions:
                             # --- 在這裡加入禁手過濾 ---
                            if player == BLACK:
                                # 檢查 (row, col) 對於黑方是否為禁手
                                is_valid, reason = rules.is_legal_move(row, col, BLACK, self.game.move_count, temp_board)
                                if not is_valid:
                                    # print(f"{row},{col} reason is {reason}")
                                    continue # 如果是禁手，則不將此點加入活三列表

                            # --- 如果不是黑方禁手，或者玩家是白方 ---
                            # print(f"_find_pattern_positions_direction add {row},{col} in {pattern_type}")
                            player_positions_set.add(pos)
                            # ... (可選的 33/34 檢測邏輯) ...

            positions[player] = list(player_positions_set) # 轉換回列表
        return positions

    # --- 棋型檢查 (Check) 方法保持不變 ---
    # 確保 check_..._direction 方法正確地將 (row, col, player, pattern_type) 添加到 result_list
    # check_..._direction 方法現在不需要返回值，只需要修改傳入的 result_list
    def check_four_direction(self, board, row, col, player, row_dir, col_dir, result_list, pattern_type):
        """檢查指定方向上是否存在連四 (XXXX0 或 0XXXX)"""
        stones_str = self._get_stones_string(board, row, col, row_dir, col_dir)
        pattern1 = f'{player}{player}{player}{player}0'
        pattern2 = f'0{player}{player}{player}{player}'

        # print(f"Player {player} found potential Four at ({row}, {col}) dir ({row_dir},{col_dir})")
        # 找到一個就要添加，因為 AI 可能需要知道所有能形成四的點
        if pattern1 in stones_str or pattern2 in stones_str:
            logger.debug(f"Player {player} found potential Four at ({row}, {col}) dir ({row_dir},{col_dir})")
                               
            # --- 在這裡加入禁手過濾 ---
            # 檢查 (row, col) 是否為44禁手
            is_valid, _ = rules.is_legal_move(row, col, player, self.game.move_count + 1, board)
            if is_valid:
                result_list.append((row, col, player, pattern_type))

            # return True # 不需要返回，因為要找所有方向

    def check_jump_four_direction(self, board, row, col, player, row_dir, col_dir, result_list, pattern_type):
        """檢查指定方向上是否存在跳連四 (X0XXX、XXX0X 和 XX0XX)"""
        stones_str = self._get_stones_string(board, row, col, row_dir, col_dir)
        pattern1 = f'{player}0{player}{player}{player}'
        pattern2 = f'{player}{player}{player}0{player}'
        pattern3 = f'{player}{player}0{player}{player}'

        if pattern1 in stones_str or pattern2 in stones_str or pattern3 in stones_str:
            logger.debug(f"Player {player} found potential Jump Four at ({row}, {col}) dir ({row_dir},{col_dir})")
            # --- 在這裡加入禁手過濾 ---
            # 檢查 (row, col) 是否為44禁手
            is_valid, _ = rules.is_legal_move(row, col, player, self.game.move_count + 1, board)
            if is_valid:
                result_list.append((row, col, player, pattern_type))

        # return found # 不需要返回

    def check_live_three_direction(self, board, row, col, player, row_dir, col_dir, result_list, pattern_type):
        """檢查指定方向上是否存在活三 (0XXX0)"""
        stones_str = self._get_stones_string(board, row, col, row_dir, col_dir, length=7) # 活三檢查通常看7格
        pattern = f'0{player}{player}{player}0'

        if pattern in stones_str:
            logger.debug(f"Player {player} found potential Live Three at ({row}, {col}) dir ({row_dir},{col_dir})")
            result_list.append((row, col, player, pattern_type))
            # return True # 不需要返回

    def check_jump_live_three_direction(self, board, row, col, player, row_dir, col_dir, result_list, pattern_type):
        """檢查指定方向上是否存在跳活三 (0X0XX0 或 0XX0X0)"""
        stones_str = self._get_stones_string(board, row, col, row_dir, col_dir, length=7) # 跳活三也看7格
        pattern1 = f'0{player}0{player}{player}0'
        pattern2 = f'0{player}{player}0{player}0'

        found = False
        if pattern1 in stones_str or pattern2 in stones_str:
            logger.debug(f"Player {player} found potential Jump Live Three at ({row}, {col}) dir ({row_dir},{col_dir})")
            result_list.append((row, col, player, pattern_type))
            found = True
        # return found # 不需要返回

    def check_five_direction(self, board, row, col, player, row_dir, col_dir, result_list, pattern_type):
        """檢查指定方向上是否存在連五 (XXXXX)"""
        stones_str = self._get_stones_string(board, row, col, row_dir, col_dir)
        pattern = f'{player}{player}{player}{player}{player}'

        if pattern in stones_str:
            logger.debug(f"Player {player} found potential Five at ({row}, {col}) dir ({row_dir},{col_dir})")
            # --- 在這裡加入禁手過濾 ---
            # 檢查 (row, col) 是否為長連禁手
            is_valid, _ = rules.is_legal_move(row, col, player, self.game.move_count + 1, board)
            if is_valid:
                result_list.append((row, col, player, pattern_type))
            # return True # 不需要返回

    def check_34(self, board, row, col, player):
        """檢查在指定位置下子(已模擬在board中)是否會形成34棋型"""
        live_three_count = 0
        four_count = 0
        temp_positions_3 = []
        temp_positions_4 = []

        # 檢查活三
        self.check_live_three_direction(board, row, col, player, 1, 0, temp_positions_3, "live_three")
        self.check_live_three_direction(board, row, col, player, 0, 1, temp_positions_3, "live_three")
        self.check_live_three_direction(board, row, col, player, 1, 1, temp_positions_3, "live_three")
        self.check_live_three_direction(board, row, col, player, 1, -1, temp_positions_3, "live_three")
        # 可選：也檢查跳活三是否計入
        # self.check_jump_live_three_direction(...)

        live_three_count = len(set(pos[:2] for pos in temp_positions_3)) # 計算獨立活三線的數量

        # 檢查活四或衝四 (這裡的 check_four_direction 實際會找到活四和衝四)
        self.check_four_direction(board, row, col, player, 1, 0, temp_positions_4, "four")
        self.check_four_direction(board, row, col, player, 0, 1, temp_positions_4, "four")
        self.check_four_direction(board, row, col, player, 1, 1, temp_positions_4, "four")
        self.check_four_direction(board, row, col, player, 1, -1, temp_positions_4, "four")
        # 可選：也檢查跳四
        # self.check_jump_four_direction(...)

        four_count = len(set(pos[:2] for pos in temp_positions_4)) # 計算獨立四線的數量

        # 判斷標準：至少有一條活三線，並且至少有一條四線 (活四或衝四)
        # 注意：嚴格的34可能需要更精確的判斷，例如區分活三/眠三，活四/衝四
        # 這個簡化版本認為：只要落子後同時出現至少一條活三模式和至少一條（活/衝）四模式，就認為是34潛力點
        return live_three_count > 0 and four_count > 0


    # --- 輔助方法保持不變 ---
    def _get_stones_string(self, board, row, col, row_dir, col_dir, length=11):
        """獲取指定方向上的棋子字串"""
        stones = []
        # 確保中心點是 (row, col) 所在的模擬落子
        # 因此偏移量應圍繞 index 0
        center_index_in_string = length // 2
        start_offset = -center_index_in_string
        end_offset = length - center_index_in_string

        for i in range(start_offset, end_offset):
            r, c = row + i * row_dir, col + i * col_dir
            if is_on_board(r, c):
                stones.append(str(board[r][c]))
            else:
                # 用一個特殊字符表示邊界外，避免與 EMPTY 的 '0' 混淆
                # 但如果規則認為邊界等於對方棋子，則另當別論
                # 這裡暫時用 'X' 或其他非 0, 1, 2 的字符
                stones.append('0') # 'X' for Out of Bounds
        # 驗證一下生成的字串是否正確反映了中心點
        # logger.debug(f"String for ({row},{col}) dir({row_dir},{col_dir}): {''.join(stones)}")
        return ''.join(stones)

    def update_influence_map(self, player, x, y):
        print(f"analysis update_influence_map()")
        """更新影響力地圖"""
        # 注意：這個影響力地圖目前沒有區分黑白棋的影響力，
        # 它只是標記了某個空點周圍有多少棋子。
        # 如果需要更精細的 AI，可能需要為黑白棋分別計算影響力。
        # 但對於查找棋型，目前的影響力圖主要是為了縮小搜索範圍，還可以接受。

        self.analysis_board[x][y] = player # 這行應該在 _reconstruct_board 中完成
        self.influence_map[x][y] = 9 # 被佔據的點影響力設為最大 (或特殊值)

        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                if self.analysis_board[r][c] == EMPTY:  # 只計算空位
                    count = 0
                    # 查看周圍8個鄰居
                    for i in range(-1, 2):
                        for j in range(-1, 2):
                            if i == 0 and j == 0: continue
                            neighbor_r, neighbor_c = r + i, c + j
                            if is_on_board(neighbor_r, neighbor_c) and self.analysis_board[neighbor_r][neighbor_c] != EMPTY:
                                count += 1
                    self.influence_map[r][c] = count
                else:  # 非空位 (有棋子)
                    self.influence_map[r][c] = 9 # 或者 -1 表示不可落子且無影響力值


    # --- 修改 getter 方法以接受 player 參數 ---
    def get_live_three_positions(self, player):
        """獲取指定玩家的活三位置"""
        return self.live_three_positions.get(player, []) # 使用 .get 避免 KeyError

    def get_jump_live_three_positions(self, player):
        """獲取指定玩家的跳活三位置"""
        return self.jump_live_three_positions.get(player, [])

    def get_four_positions(self, player):
        """獲取指定玩家的連四位置"""
        return self.four_positions.get(player, [])

    def get_jump_four_positions(self, player):
        """獲取指定玩家的跳連四位置"""
        return self.jump_four_positions.get(player, [])

    def get_five_positions(self, player):
        """獲取指定玩家的連五位置"""
        return self.five_positions.get(player, [])

    def simulate_move(self, board, row, col, player):
        """模擬在指定位置下子，並返回新的棋盤狀態"""
        new_board = [r[:] for r in board]  # 複製棋盤
        new_board[row][col] = player
        return new_board