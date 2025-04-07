# test_game_logic.py
import unittest
import os
import sys

# --- 路徑設定 ---
# 確保主要的專案目錄在 Python 的搜尋路徑中
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '.'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
    print(f"已將 {project_root} 加入 sys.path") # 顯示路徑已被加入
else:
    print(f"{project_root} 已在 sys.path 中")
# --- 結束路徑設定 ---

# --- 匯入 ---
# 嘗試匯入必要的模組，並提供更詳細的錯誤訊息
try:
    print("正在嘗試從 game_logic 匯入 RenjuGame...")
    from game_logic import RenjuGame
    print("成功匯入 RenjuGame。")

    print("正在嘗試從 config 匯入 BLACK, WHITE, GameState...")
    # 根據之前的錯誤，我們不從 config 匯入 EMPTY_SLOT
    from config import BLACK, WHITE, GameState
    print("成功匯入 BLACK, WHITE, GameState。")

except ImportError as e:
    print(f"錯誤：無法匯入遊戲模組: {e}")
    print("請檢查：")
    print("1. test_game_logic.py 是否與 game_logic.py 和 config.py 在同一個目錄，或路徑設定是否正確。")
    print(f"2. Python 的 sys.path: {sys.path}")
    sys.exit(1)
except Exception as e_other:
    print(f"匯入時發生非預期的錯誤: {e_other}")
    sys.exit(1)
# --- 結束匯入 ---

print("模組匯入完成，定義測試類別...")

class TestRenjuGameKifu(unittest.TestCase):
    """測試 RenjuGame 類別處理特定棋譜序列的功能。"""

    def setUp(self):
        """在每個測試方法執行前，設定一個新的遊戲實例和空位代表值。"""
        print(f"\n--- Running setUp for {self.id()} ---") # 顯示正在執行哪個測試的 setUp
        self.game = RenjuGame(black_player_type="human", white_player_type="human")
        # 根據之前的錯誤 'AssertionError: 0 != 1' 和 '0 != 2'，
        # 我們確定遊戲邏輯中使用 0 代表空位。
        self.EMPTY_SLOT = 0
        print(f"setUp 完成：已建立 RenjuGame 實例, EMPTY_SLOT = {self.EMPTY_SLOT}")

    def test_kifu_sequence_basic(self):
        """
        測試執行一個特定的 7 步棋譜序列 (kifu)。
        棋譜: (7,7)(8,6)(9,7)(8,5)(8,8)(9,5)(7,10)
        並驗證最終棋盤狀態、當前玩家、遊戲狀態和步數。
        """
        print(f"\n--- Starting test: {self.id()} ---")
        # 棋譜: (7,7)(8,6)(9,7)(8,5)(8,8)(9,5)(7,10)
        # 假設是 (欄, 列) 並且是 0-based 索引
        moves = [
            (7, 7), (8, 6), (9, 7), (8, 5),
            (8, 8), (9, 5), (7, 10)
        ]
        # 預期的玩家順序：黑, 白, 黑, 白, 黑, 白, 黑
        expected_players = [BLACK, WHITE, BLACK, WHITE, BLACK, WHITE, BLACK]
        print(f"棋譜序列: {moves}")
        print(f"預期玩家順序 (BLACK={BLACK}, WHITE={WHITE}): {expected_players}")

        # 1. 檢查初始狀態
        print("檢查初始遊戲狀態...")
        self.assertEqual(self.game.current_player, BLACK, "初始玩家應為黑方 (BLACK)")
        self.assertEqual(self.game.game_state, GameState.PLAYING, "初始遊戲狀態應為 PLAYING")
        self.assertEqual(self.game.move_count, 0, "初始步數應為 0")
        print("初始狀態檢查通過。")

        # 2. 執行棋譜序列
        print("開始執行棋譜序列...")
        for i, move in enumerate(moves):
            turn = i + 1
            player = expected_players[i]
            print(f"\n--- 第 {turn} 手 ({'黑' if player == BLACK else '白'}) ---")
            print(f"預期玩家: {player}")
            # 檢查輪到誰下棋
            self.assertEqual(self.game.current_player, player, f"第 {turn} 手: 應輪到玩家 {player}")
            print(f"當前玩家符合預期 ({self.game.current_player}). 嘗試下棋於: {move}")

            # --- 下棋 ---
            try:
                # 呼叫 game_logic 中的 make_move
                # 我們期望 game_logic 中的 print 語句會在這裡顯示詳細過程
                self.game.make_move(move[0], move[1])
                print(f"make_move({move[0]}, {move[1]}) 呼叫完成 (未引發例外)。")
                # 注意：我們在這裡不假設 make_move 返回值，主要依賴後續的狀態斷言。
            except Exception as e:
                # 如果 make_move 意外引發例外，測試將失敗
                self.fail(f"make_move({move[0]}, {move[1]}) 在第 {turn} 手引發未預期的例外: {e}")
            # --- 下棋完成 ---

        print("\n棋譜序列執行完成。")

        # 3. 在整個序列完成後進行斷言檢查
        print("開始進行最終狀態斷言檢查...")

        # 檢查下過棋的位置
        print("檢查棋盤上已下棋子的位置...")
        expected_board_states = {
            (7, 7): BLACK, (8, 6): WHITE, (9, 7): BLACK, (8, 5): WHITE,
            (8, 8): BLACK, (9, 5): WHITE, (7, 10): BLACK
        }
        for (x, y), expected_player in expected_board_states.items():
            actual_player = self.game.board[y][x]
            self.assertEqual(actual_player, expected_player,
                             f"位置 ({x},{y}) 應為 {'黑棋' if expected_player == BLACK else '白棋'} (值={expected_player}), 但實際是 (值={actual_player})")
        print("已下棋子位置檢查通過。")

        # 檢查一些周圍的空位
        print("檢查棋盤上部分空位...")
        empty_checks = [(7, 6), (8, 7), (0, 0), (14, 14)] # 包含邊界和中間空位
        for (x, y) in empty_checks:
             # 確保座標在範圍內才檢查
             if 0 <= x < self.game.board_size and 0 <= y < self.game.board_size:
                  actual_value = self.game.board[y][x]
                  self.assertEqual(actual_value, self.EMPTY_SLOT,
                                   f"位置 ({x},{y}) 應為空 (值={self.EMPTY_SLOT}), 但實際是 (值={actual_value})")
        print("空位檢查通過。")

        # 檢查最終玩家
        print("檢查最終輪到誰下棋...")
        # 下了 7 手棋 (奇數)，應該輪到白方
        self.assertEqual(self.game.current_player, WHITE, f"下了 7 手後，應輪到白方 (WHITE={WHITE}), 但實際是 {self.game.current_player}")
        print(f"最終玩家檢查通過 (應為 {WHITE})。")

        # 檢查最終遊戲狀態
        print("檢查最終遊戲狀態...")
        # 這個序列不會導致遊戲結束
        self.assertEqual(self.game.game_state, GameState.PLAYING, f"遊戲狀態應仍為 PLAYING, 但實際是 {self.game.game_state}")
        print(f"最終遊戲狀態檢查通過 (應為 {GameState.PLAYING})。")

        # 檢查最終步數
        print("檢查最終步數...")
        self.assertEqual(self.game.move_count, 7, f"步數應為 7, 但實際是 {self.game.move_count}")
        print(f"最終步數檢查通過 (應為 7)。")

        # (可選) 檢查歷史紀錄
        if hasattr(self.game, 'history'):
            print("檢查歷史紀錄...")
            self.assertEqual(len(self.game.history), 7, f"歷史紀錄長度應為 7, 但實際是 {len(self.game.history)}")
            # 可選擇性地更深入檢查 history 內容
            # recorded_moves = [(x, y) for _, x, y in self.game.history] # 假設 history 格式是 (player, x, y)
            # self.assertEqual(recorded_moves, moves, "遊戲歷史紀錄內容與輸入棋譜不符")
            print("歷史紀錄長度檢查通過。")
        else:
            print("遊戲物件沒有 'history' 屬性，跳過歷史紀錄檢查。")

        print(f"--- Test finished: {self.id()} ---")


# 你可以在這裡加入更多的測試類別或測試方法
# (例如：測試勝利條件、測試禁手、測試 AI 等)

if __name__ == '__main__':
    """當直接執行此腳本時，運行測試。"""
    print("\n--- Running Unittests ---")
    # verbosity=2 提供更詳細的輸出
    unittest.main(verbosity=2)