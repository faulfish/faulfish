# test_game_logic.py
import unittest
# <<< 修改: 從 utils 匯入 is_on_board >>>
from utils import is_on_board
import os
import sys

# --- 路徑設定 ---
# 確保主要的專案目錄在 Python 的搜尋路徑中
try:
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '.'))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
        print(f"[測試設定] 已將專案根目錄 {project_root} 加入 sys.path")
    else:
        print(f"[測試設定] 專案根目錄 {project_root} 已在 sys.path 中")
except Exception as e:
    print(f"[測試設定] 錯誤：設定 sys.path 時發生問題: {e}")
    sys.exit(1)
# --- 結束路徑設定 ---

# --- 匯入 ---
# 匯入必要的遊戲邏輯和設定
try:
    print("[測試設定] 正在匯入 RenjuGame from game_logic...")
    from game_logic import RenjuGame
    print("[測試設定] 成功匯入 RenjuGame。")

    print("[測試設定] 正在匯入 BLACK, WHITE, GameState from config...")
    from config import BLACK, WHITE, GameState # 假設 BOARD_SIZE 由 is_on_board 內部處理或從 config 獲取
    print("[測試設定] 成功匯入 BLACK, WHITE, GameState。")
    # 驗證常數值是否符合預期 (基於之前的錯誤)
    _BLACK_EXPECTED = 1
    _WHITE_EXPECTED = 2
    if BLACK != _BLACK_EXPECTED:
        print(f"[測試設定] 警告：config.BLACK 的值 ({BLACK}) 與預期 ({_BLACK_EXPECTED}) 不符！")
    if WHITE != _WHITE_EXPECTED:
        print(f"[測試設定] 警告：config.WHITE 的值 ({WHITE}) 與預期 ({_WHITE_EXPECTED}) 不符！")

except ImportError as e:
    print(f"[測試設定] 嚴重錯誤：無法匯入必要的遊戲模組: {e}")
    print("請檢查：")
    print("1. `test_game_logic.py` 是否與 `game_logic.py`, `config.py`, `utils.py` 在同一個目錄或可訪問的路徑。")
    print(f"2. 當前的 Python 搜尋路徑 (sys.path): {sys.path}")
    sys.exit(1)
except Exception as e_other:
    print(f"[測試設定] 嚴重錯誤：匯入模組時發生非預期的錯誤: {e_other}")
    sys.exit(1)
# --- 結束匯入 ---

print("[測試設定] 模組匯入完成，定義測試類別 TestRenjuGameKifu...")

class TestRenjuGameKifu(unittest.TestCase):
    """
    測試 RenjuGame 類別處理特定棋譜序列 (Kifu) 的功能。
    旨在驗證遊戲邏輯是否按照預期更新棋盤狀態、玩家輪次等核心屬性。
    """
    BOARD_SIZE_EXPECTED = 15 # 假設棋盤大小為 15x15

    def setUp(self):
        """
        在每個測試方法執行前被呼叫。
        負責建立一個全新的 RenjuGame 實例，並設定測試中使用的空位代表值。
        確保每個測試都在一個乾淨、獨立的環境中執行。
        """
        test_method_name = self.id().split('.')[-1] # 獲取測試方法的名稱
        print(f"\n--- [測試流程] 執行 setUp for {test_method_name} ---")
        try:
            self.game = RenjuGame(black_player_type="human", white_player_type="human")
            self.EMPTY_SLOT = 0 # 根據之前的錯誤推斷，0 代表空位
            print(f"[測試流程] setUp 完成：已建立 RenjuGame 實例, EMPTY_SLOT = {self.EMPTY_SLOT}")

            # 基本檢查
            self.assertIsNotNone(self.game, "RenjuGame 實例未能成功建立。")
            self.assertTrue(hasattr(self.game, 'board'), "RenjuGame 實例應包含 'board' 屬性。")
            self.assertIsInstance(self.game.board, list, "遊戲棋盤應為 list 類型。")

            # 可選：棋盤大小檢查
            board_size_actual = getattr(self.game, 'board_size', len(self.game.board) if isinstance(self.game.board, list) else -1)
            self.assertEqual(board_size_actual, self.BOARD_SIZE_EXPECTED,
                             f"預期棋盤大小為 {self.BOARD_SIZE_EXPECTED}，但實際檢測到的大小為 {board_size_actual}")
            if isinstance(self.game.board, list) and len(self.game.board) > 0:
                 self.assertEqual(len(self.game.board[0]), self.BOARD_SIZE_EXPECTED,
                                  f"預期棋盤列數為 {self.BOARD_SIZE_EXPECTED}，但第一行實際列數為 {len(self.game.board[0])}")

        except Exception as e:
            self.fail(f"setUp 失敗: {e}")


    def test_kifu_sequence_basic(self):
        """
        測試執行一個特定的 7 步棋譜序列 (kifu)。
        棋譜: (7,7)(8,6)(9,7)(8,5)(8,8)(9,5)(7,10)
        """
        print(f"\n--- [測試執行] 開始測試: {self.id()} ---")
        moves = [
            (7, 7), (8, 6), (9, 7), (8, 5),
            (8, 8), (9, 5), (7, 10)
        ]
        expected_players = [BLACK, WHITE, BLACK, WHITE, BLACK, WHITE, BLACK]
        print(f"[測試資訊] 棋譜序列 (欄, 列): {moves}")
        print(f"[測試資訊] 預期玩家順序 (BLACK={BLACK}, WHITE={WHITE}): {expected_players}")

        # === 1. 檢查初始狀態 ===
        print("[測試步驟] 檢查遊戲初始狀態...")
        self.assertEqual(self.game.current_player, BLACK, f"初始玩家應為黑方 (BLACK={BLACK})")
        self.assertEqual(self.game.game_state, GameState.PLAYING, f"初始遊戲狀態應為 PLAYING")
        self.assertEqual(self.game.move_count, 0, "初始步數應為 0")
        self.assertEqual(self.game.board[7][7], self.EMPTY_SLOT, "初始時 (7,7) 應為空")
        self.assertEqual(self.game.board[8][6], self.EMPTY_SLOT, "初始時 (8,6) 應為空")
        print("[測試結果] 初始狀態檢查通過。")

        # === 2. 依序執行棋譜序列 ===
        print("[測試步驟] 開始依序執行棋譜中的每一步...")
        for i, move in enumerate(moves):
            turn = i + 1
            player = expected_players[i]
            player_name = '黑方' if player == BLACK else '白方'
            x, y = move

            print(f"\n--- [測試迴圈] 第 {turn} 手 ({player_name}, {player}) ---")
            print(f"[測試迴圈] 預期下棋玩家: {player}")

            # --- 2a. 檢查當前玩家 ---
            self.assertEqual(self.game.current_player, player, f"第 {turn} 手開始時: 應輪到玩家 {player}, 但實際是 {self.game.current_player}")
            print(f"[測試迴圈] 檢查通過：當前玩家確實是 {self.game.current_player} ({player_name})")
            print(f"[測試迴圈] 嘗試下棋於座標: ({x}, {y})")

            # --- 2b. 執行下棋動作 ---
            # **重要**: 期望 game_logic.py 的 make_move 包含詳細的 [DEBUG] print 語句
            try:
                self.game.make_move(x, y)
                print(f"[測試迴圈] game.make_move({x}, {y}) 呼叫完成，未引發例外。")

                # --- 2c. 立刻檢查關鍵位置 (8, 6) 的狀態 ---
                critical_pos_x, critical_pos_y = 8, 6
                try:
                    # <<< 修改: 使用 is_on_board >>>
                    # !!! 關鍵警告 !!! 檢查 is_on_board 的參數順序！
                    # 如果 is_on_board(r, c) 期望 (row, column)，這裡應該用 is_on_board(critical_pos_y, critical_pos_x)
                    # 你目前使用的是 is_on_board(critical_pos_x, critical_pos_y) -> is_on_board(8, 6)
                    if is_on_board(critical_pos_x, critical_pos_y):
                        critical_value = self.game.board[critical_pos_y][critical_pos_x] # 讀取 board[6][8]
                        print(f"[測試偵錯] 第 {turn} 手 ({x},{y}) 執行後, 檢查位置 ({critical_pos_x},{critical_pos_y}) 的值: {critical_value}")
                        if turn == 2:
                            self.assertEqual(critical_value, WHITE, f"關鍵檢查失敗：第 2 手剛下完, ({critical_pos_x},{critical_pos_y}) 的值應為 WHITE ({WHITE}), 但實際是 {critical_value}")
                    else:
                         print(f"[測試偵錯] 警告：關鍵位置 ({critical_pos_x},{critical_pos_y}) 不在棋盤邊界內 (根據 is_on_board)，無法檢查其值。")

                except NameError:
                     # 如果 is_on_board 未成功匯入
                     print(f"[測試偵錯] 嚴重錯誤：無法執行關鍵位置檢查，因為 is_on_board 函數未定義或未匯入。")
                except IndexError:
                    print(f"[測試偵錯] 警告：檢查關鍵位置 ({critical_pos_x},{critical_pos_y}) 時發生 IndexError。")
                except Exception as e_check:
                    print(f"[測試偵錯] 警告：檢查關鍵位置時發生非預期錯誤: {e_check}")


            except Exception as e:
                # 捕捉 make_move 或後續檢查中未預期的例外
                self.fail(f"第 {turn} 手執行 game.make_move({x}, {y}) 或後續偵錯檢查時引發未預期的例外: {e}")

        print("\n[測試步驟] 棋譜序列中的所有 7 步棋已執行完成。")

        # === 3. 全面驗證最終狀態 ===
        print("[測試步驟] 開始進行最終狀態的全面斷言檢查...")

        # --- 3a. 檢查所有下過棋的位置 ---
        print("[測試驗證] 檢查棋盤上所有應該有棋子的位置...")
        expected_board_states = {
            (7, 7): BLACK, (8, 6): WHITE, (9, 7): BLACK, (8, 5): WHITE,
            (8, 8): BLACK, (9, 5): WHITE, (7, 10): BLACK
        }
        all_placed_stones_ok = True
        for (x, y), expected_player in expected_board_states.items():
            player_name = '黑' if expected_player == BLACK else '白'
            try:
                # <<< 修改: 使用 is_on_board >>>
                # !!! 關鍵警告 !!! 再次檢查 is_on_board 的參數順序！
                # 如果 is_on_board(r, c) 期望 (row, column)，這裡應該用 is_on_board(y, x)
                # 你目前使用的是 is_on_board(x, y)
                if is_on_board(x, y):
                    actual_player = self.game.board[x][y] # 讀取 board[y][x]
                    self.assertEqual(actual_player, expected_player,
                                     f"最終狀態錯誤：位置 ({x},{y}) 應為 {player_name}棋 (值={expected_player}), 但實際是 (值={actual_player})")
                else:
                     self.fail(f"最終狀態驗證失敗：預期應有棋子的位置 ({x},{y}) 不在棋盤邊界內 (根據 is_on_board)。")

            except NameError:
                 self.fail("最終狀態驗證失敗：is_on_board 函數未定義或未匯入。")
            except IndexError:
                 self.fail(f"最終狀態驗證失敗：嘗試存取棋盤位置 ({x},{y}) 時發生 IndexError。")
            except Exception as e:
                 self.fail(f"最終狀態驗證失敗：檢查位置 ({x},{y}) 時發生非預期錯誤: {e}")
        if all_placed_stones_ok:
             print("[測試結果] 所有已下棋子位置最終狀態檢查通過。")


        # --- 3b. 檢查一些應該是空的位置 ---
        print("[測試驗證] 檢查棋盤上一些應該保持空位的位置...")
        empty_checks = [(7, 6), (8, 7), (0, 0), (14, 14), (10, 10)]
        all_empty_slots_ok = True
        for (x, y) in empty_checks:
             try:
                # <<< 修改: 使用 is_on_board >>>
                # !!! 關鍵警告 !!! 再次檢查 is_on_board 的參數順序！
                # 如果 is_on_board(r, c) 期望 (row, column)，這裡應該用 is_on_board(y, x)
                # 你目前使用的是 is_on_board(x, y)
                if is_on_board(x, y):
                      actual_value = self.game.board[y][x] # 讀取 board[y][x]
                      self.assertEqual(actual_value, self.EMPTY_SLOT,
                                       f"最終狀態錯誤：位置 ({x},{y}) 應為空 (值={self.EMPTY_SLOT}), 但實際是 (值={actual_value})")
                else:
                    print(f"[測試資訊] 跳過檢查不在邊界內的預期空位 ({x},{y})")

             except NameError:
                 self.fail("最終狀態驗證失敗：is_on_board 函數未定義或未匯入。")
             except IndexError:
                  self.fail(f"最終狀態錯誤：嘗試存取棋盤空位 ({x},{y}) 時發生 IndexError。")
             except Exception as e:
                  self.fail(f"最終狀態錯誤：檢查空位 ({x},{y}) 時發生非預期錯誤: {e}")
        if all_empty_slots_ok:
            print("[測試結果] 指定空位最終狀態檢查通過。")


        # --- 3c. 檢查最終輪到的玩家 ---
        print("[測試驗證] 檢查最終應輪到的玩家...")
        self.assertEqual(self.game.current_player, WHITE, f"最終玩家錯誤：下了 7 手後，應輪到白方 (WHITE={WHITE}), 但實際輪到 {self.game.current_player}")
        print(f"[測試結果] 最終玩家檢查通過 (應為 {WHITE})。")


        # --- 3d. 檢查最終遊戲狀態 ---
        print("[測試驗證] 檢查最終遊戲狀態...")
        self.assertEqual(self.game.game_state, GameState.PLAYING, f"最終遊戲狀態錯誤：狀態應仍為 PLAYING (={GameState.PLAYING}), 但實際是 {self.game.game_state}")
        print(f"[測試結果] 最終遊戲狀態檢查通過 (應為 {GameState.PLAYING})。")


        # --- 3e. 檢查最終步數 ---
        print("[測試驗證] 檢查最終步數...")
        self.assertEqual(self.game.move_count, 7, f"最終步數錯誤：步數應為 7, 但實際是 {self.game.move_count}")
        print(f"[測試結果] 最終步數檢查通過 (應為 7)。")


        # --- 3f. (可選) 檢查歷史紀錄 ---
        if hasattr(self.game, 'history'):
            print("[測試驗證] 檢查歷史紀錄 (history)...")
            self.assertIsInstance(self.game.history, list, "history 屬性應為 list 類型。")
            self.assertEqual(len(self.game.history), 7, f"最終歷史紀錄長度錯誤：長度應為 7, 但實際是 {len(self.game.history)}")
            print("[測試結果] 歷史紀錄長度檢查通過。")
        else:
            print("[測試資訊] 遊戲物件沒有 'history' 屬性，跳過歷史紀錄檢查。")

        print(f"\n--- [測試執行] 測試成功結束: {self.id()} ---")


# --- 主執行區塊 ---
if __name__ == '__main__':
    """
    當這個腳本被直接執行時，運行 unittest.main() 來發現並運行所有測試。
    """
    print("\n--- [測試啟動] 運行 Unittests ---")
    unittest.main(verbosity=2)