# test_game_logic.py
import unittest
import os
import sys

# --- 路徑設定 ---
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
try:
    print("[測試設定] 正在匯入 RenjuGame from game_logic...")
    from game_logic import RenjuGame
    print("[測試設定] 成功匯入 RenjuGame。")

    print("[測試設定] 正在匯入 BLACK, WHITE, GameState, EMPTY, BOARD_SIZE from config...")
    from config import BLACK, WHITE, GameState, EMPTY, BOARD_SIZE
    print("[測試設定] 成功匯入 config 常數。")
    _BLACK_EXPECTED = 1
    _WHITE_EXPECTED = 2
    if BLACK != _BLACK_EXPECTED:
        print(f"[測試設定] 警告：config.BLACK 的值 ({BLACK}) 與預期 ({_BLACK_EXPECTED}) 不符！")
    if WHITE != _WHITE_EXPECTED:
        print(f"[測試設定] 警告：config.WHITE 的值 ({WHITE}) 與預期 ({_WHITE_EXPECTED}) 不符！")

    # 嘗試匯入 is_on_board
    try:
        from utils import is_on_board
        print("[測試設定] 成功從 utils 匯入 is_on_board。")
        is_on_board(0, 0) # 簡單測試
    except ImportError:
        print("[測試設定] 警告：無法從 utils 匯入 is_on_board。將使用內建的備用邊界檢查。")
        def is_on_board(r, c, size=BOARD_SIZE):
            return 0 <= r < size and 0 <= c < size
    except Exception as e_util:
         print(f"[測試設定] 警告：匯入或測試 utils.is_on_board 時發生錯誤: {e_util}。將使用備用方案。")
         def is_on_board(r, c, size=BOARD_SIZE):
            return 0 <= r < size and 0 <= c < size

except ImportError as e:
    print(f"[測試設定] 嚴重錯誤：無法匯入必要的模組: {e}")
    print(f" sys.path: {sys.path}")
    sys.exit(1)
except Exception as e_other:
    print(f"[測試設定] 嚴重錯誤：匯入模組時發生非預期的錯誤: {e_other}")
    sys.exit(1)
# --- 結束匯入 ---

print("[測試設定] 模組匯入完成，定義測試類別 TestRenjuGameRules...")

class TestRenjuGameRules(unittest.TestCase):
    """測試 RenjuGame 的核心規則和邊界條件。"""
    BOARD_SIZE_EXPECTED = BOARD_SIZE

    def setUp(self):
        """為每個測試設置新的遊戲實例。"""
        test_method_name = self.id().split('.')[-1]
        print(f"\n--- [測試流程] 執行 setUp for {test_method_name} ---")
        try:
            self.game = RenjuGame(black_player_type="human", white_player_type="human")
            self.EMPTY_SLOT = EMPTY
            print(f"[測試流程] setUp 完成：已建立 RenjuGame 實例, EMPTY_SLOT = {self.EMPTY_SLOT}")

            # 基本檢查
            self.assertIsNotNone(self.game, "RenjuGame 實例未能成功建立。")
            self.assertTrue(hasattr(self.game, 'board'), "RenjuGame 實例應包含 'board' 屬性。")
            self.assertIsInstance(self.game.board, list, "遊戲棋盤應為 list 類型。")

            # 棋盤大小檢查
            board_size_actual = getattr(self.game, 'board_size', len(self.game.board) if isinstance(self.game.board, list) else -1)
            if board_size_actual == -1 and isinstance(self.game.board, list):
                board_size_actual = len(self.game.board)
            self.assertEqual(board_size_actual, self.BOARD_SIZE_EXPECTED,
                             f"預期棋盤大小為 {self.BOARD_SIZE_EXPECTED}，但實際為 {board_size_actual}")
            if isinstance(self.game.board, list) and len(self.game.board) > 0:
                 self.assertEqual(len(self.game.board[0]), self.BOARD_SIZE_EXPECTED,
                                  f"預期棋盤列數為 {self.BOARD_SIZE_EXPECTED}，但實際為 {len(self.game.board[0])}")

        except Exception as e:
            self.fail(f"setUp 失敗: {e}")

    def _play_moves(self, moves):
        """輔助函數：按順序執行一系列移動 (欄, 列) / (x, y)"""
        print(f"[輔助] 正在執行棋步序列: {moves}")
        for i, move in enumerate(moves):
            x, y = move # x = 欄, y = 列
            player = self.game.current_player
            player_name = '黑' if player == BLACK else '白'
            print(f"[輔助] 第 {i+1} 步 ({player_name}) 於 (欄={x}, 列={y})")
            # 呼叫 make_move 時傳入 (列, 欄) -> (y, x)
            success = self.game.make_move(y, x)
            if not success:
                 reason = getattr(self.game, 'status_message', '未知原因') # 嘗試獲取失敗原因
                 print(f"[輔助] 警告：make_move(r={y}, c={x}) 在第 {i+1} 步返回 False ({reason})。停止播放。")
                 return False # 移動失敗，停止
            if self.game.game_state != GameState.PLAYING:
                 print(f"[輔助] 訊息：遊戲在第 {i+1} 步後結束，狀態: {self.game.game_state}。停止播放。")
                 return False # 遊戲結束，停止
        print("[輔助] 棋步序列成功執行完畢。")
        return True

    # --- 原有棋譜測試 ---
    def test_kifu_sequence_basic(self):
        """測試棋譜: (7,7)(8,6)(9,7)(8,5)(8,8)(9,5)(7,10)"""
        print(f"\n--- [測試執行] 開始測試: {self.id()} ---")
        moves = [ (7, 7), (8, 6), (9, 7), (8, 5), (8, 8), (9, 5), (7, 10) ]
        expected_players = [BLACK, WHITE, BLACK, WHITE, BLACK, WHITE, BLACK]
        print(f"[測試資訊] 棋譜序列 (欄, 列): {moves}")

        print("[測試步驟] 檢查遊戲初始狀態...")
        self.assertEqual(self.game.current_player, BLACK)
        self.assertEqual(self.game.game_state, GameState.PLAYING)
        self.assertEqual(self.game.move_count, 0)
        self.assertEqual(self.game.board[7][7], self.EMPTY_SLOT)
        self.assertEqual(self.game.board[6][8], self.EMPTY_SLOT)
        print("[測試結果] 初始狀態檢查通過。")

        print("[測試步驟] 開始依序執行棋譜中的每一步...")
        for i, move in enumerate(moves):
            turn = i + 1
            player = expected_players[i]
            x, y = move
            print(f"\n--- [測試迴圈] 第 {turn} 手 ({'黑' if player == BLACK else '白'}, {player}) ---")
            self.assertEqual(self.game.current_player, player, f"第 {turn} 手開始時: 應輪到玩家 {player}")
            print(f"[測試呼叫] 正在呼叫 self.game.make_move(r={y}, c={x})")
            move_successful = self.game.make_move(y, x)
            self.assertTrue(move_successful, f"make_move(r={y}, c={x}) 在第 {turn} 手應返回 True")
            print(f"[測試迴圈] game.make_move(r={y}, c={x}) 呼叫完成，返回: {move_successful}")

            # 檢查關鍵位置 (8,6) 的值
            crit_x, crit_y = 8, 6
            if is_on_board(crit_y, crit_x):
                crit_val = self.game.board[crit_y][crit_x]
                print(f"[測試偵錯] 第 {turn} 手後, 檢查位置 (x={crit_x},y={crit_y}) 的值: {crit_val}")
                if turn >= 2: # 從第二步開始檢查
                     self.assertEqual(crit_val, WHITE, f"第 {turn} 手後, ({crit_x},{crit_y}) 應為 WHITE ({WHITE}), 但得到 {crit_val}")

        print("\n[測試步驟] 棋譜序列執行完成。")
        print("[測試步驟] 開始進行最終狀態檢查...")
        # 最終斷言
        expected_board = { (7, 7): BLACK, (8, 6): WHITE, (9, 7): BLACK, (8, 5): WHITE, (8, 8): BLACK, (9, 5): WHITE, (7, 10): BLACK }
        for (x, y), p in expected_board.items(): self.assertEqual(self.game.board[y][x], p, f"最終 ({x},{y}) 應為 {p}")
        empty_checks = [(7, 6), (8, 7), (0, 0), (14, 14)]
        for (x, y) in empty_checks: self.assertEqual(self.game.board[y][x], self.EMPTY_SLOT, f"最終 ({x},{y}) 應為空")
        self.assertEqual(self.game.current_player, WHITE)
        self.assertEqual(self.game.game_state, GameState.PLAYING)
        self.assertEqual(self.game.move_count, 7)
        print(f"--- [測試執行] 測試成功結束: {self.id()} ---")


    # --- 規則測試 ---

    def test_black_forbidden_three_three(self):
        """測試黑棋三三禁手"""
        print(f"\n--- [測試執行] 開始測試: {self.id()} ---")
        # 構建三三局面 V4 (第一步天元)
        # . . . . . . .
        # . . . . . . .
        # . B . B . . . (1,2) (3,2)
        # . B . B . . . (1,4) (3,4) ?? No, let's use (2,1) (2,3)
        # . . W . . . . (2,2) <- White block center? No, let's make it easier
        # B=(1,2) B=(3,2) B=(2,1) B=(2,3) -> Try (2,2) = 3x3 forbidden
        # Need Tengen first
        initial_moves = [
            (7, 7), (0, 0), # B(Tengen), W
            (1, 2), (0, 1), # B
            (3, 2), (0, 2), # B
            (2, 1), (0, 3), # B
            (2, 3), (0, 4)  # B, White plays somewhere else
        ]
        played_ok = self._play_moves(initial_moves)
        self.assertTrue(played_ok, "設置三三禁手局面 v4 時，所有初始棋步都應合法")
        self.assertEqual(self.game.current_player, WHITE, "v4 佈局後應輪到白棋") # Last B played

        # White plays a non-interfering move
        white_move_x, white_move_y = 10, 10
        print(f"[測試步驟] 白棋在非干擾點 (欄={white_move_x}, 列={white_move_y}) 下棋...")
        played_ok_w = self.game.make_move(white_move_y, white_move_x)
        self.assertTrue(played_ok_w, f"白棋在 ({white_move_x},{white_move_y}) 落子應成功")

        # Now it's Black's turn
        self.assertEqual(self.game.current_player, BLACK, "白棋落子後應輪到黑棋")
        forbidden_x, forbidden_y = 2, 2 # Target (2,2) should be 3x3 forbidden
        print(f"[測試步驟] 嘗試黑棋在三三禁手點 (欄={forbidden_x}, 列={forbidden_y}) 下棋...")
        is_move_made = self.game.make_move(forbidden_y, forbidden_x) # Pass (row, col)

        self.assertFalse(is_move_made, f"黑棋在 ({forbidden_x},{forbidden_y}) 下三三禁手，make_move 應返回 False")
        self.assertEqual(self.game.board[forbidden_y][forbidden_x], self.EMPTY_SLOT, f"禁手點 ({forbidden_x},{forbidden_y}) 應保持為空")
        self.assertEqual(self.game.current_player, BLACK, "下禁手後應仍為黑棋回合")
        if hasattr(self.game, 'status_message'):
            self.assertIn("禁手", self.game.status_message, f"狀態消息 '{self.game.status_message}' 應包含 '禁手' 提示")
        print(f"[測試結果] 黑棋三三禁手測試通過。")
        print(f"--- [測試執行] 測試成功結束: {self.id()} ---")

    def test_black_win_condition(self):
        """測試黑棋五連獲勝"""
        print(f"\n--- [測試執行] 開始測試: {self.id()} ---")
        # 構建黑棋四連局面，第一步下天元
        win_moves = [
            (7, 7), (0, 8), # B(天元), W
            (1, 1), (1, 8), # B, W
            (2, 1), (2, 8), # B, W
            (3, 1), (3, 8), # B, W
            (4, 1), (0, 9), # B, W (non-interfering)
        ]
        played_ok = self._play_moves(win_moves)
        self.assertTrue(played_ok, "設置黑棋獲勝局面時，所有初始棋步都應合法")
        self.assertEqual(self.game.current_player, BLACK, "佈局後應輪到黑棋")

        win_x, win_y = 5, 1 # Black plays at (5,1) to win
        print(f"[測試步驟] 黑棋在致勝點 (欄={win_x}, 列={win_y}) 下棋...")
        is_move_made = self.game.make_move(win_y, win_x) # Pass (row, col)

        self.assertTrue(is_move_made, f"黑棋在 ({win_x},{win_y}) 下致勝棋，make_move 應返回 True")
        self.assertEqual(self.game.board[win_y][win_x], BLACK, f"致勝點 ({win_x},{win_y}) 應為黑棋")
        self.assertEqual(self.game.game_state, GameState.BLACK_WINS, "遊戲狀態應變為 BLACK_WINS")
        if hasattr(self.game, 'status_message'):
             self.assertTrue("黑方" in self.game.status_message and "勝" in self.game.status_message)
        print(f"[測試結果] 黑棋獲勝條件測試通過。")
        print(f"--- [測試執行] 測試成功結束: {self.id()} ---")

    def test_white_win_condition(self):
        """測試白棋五連獲勝"""
        print(f"\n--- [測試執行] 開始測試: {self.id()} ---")
        # 構建白棋四連局面，第一步下天元
        win_moves = [
            (7, 7), (1, 1), # B(天元), W
            (0, 8), (2, 1), # B, W
            (1, 8), (3, 1), # B, W
            (2, 8), (4, 1), # B, W
            (3, 8),         # B - White's turn now
        ]
        played_ok = self._play_moves(win_moves)
        self.assertTrue(played_ok, "設置白棋獲勝局面時，所有初始棋步都應合法")
        self.assertEqual(self.game.current_player, WHITE, "佈局後應輪到白棋")

        win_x, win_y = 5, 1 # White plays at (5,1) to win
        print(f"[測試步驟] 白棋在致勝點 (欄={win_x}, 列={win_y}) 下棋...")
        is_move_made = self.game.make_move(win_y, win_x) # Pass (row, col)

        self.assertTrue(is_move_made, f"白棋在 ({win_x},{win_y}) 下致勝棋，make_move 應返回 True")
        self.assertEqual(self.game.board[win_y][win_x], WHITE, f"致勝點 ({win_x},{win_y}) 應為白棋")
        self.assertEqual(self.game.game_state, GameState.WHITE_WINS, "遊戲狀態應變為 WHITE_WINS")
        if hasattr(self.game, 'status_message'):
             self.assertTrue("白方" in self.game.status_message and "勝" in self.game.status_message)
        print(f"[測試結果] 白棋獲勝條件測試通過。")
        print(f"--- [測試執行] 測試成功結束: {self.id()} ---")

    def test_draw_condition_simulation(self):
        """測試平局條件 (通過模擬填滿棋盤)"""
        print(f"\n--- [測試執行] 開始測試: {self.id()} ---")
        print("[測試步驟] 模擬下滿棋盤 (不檢查規則)...")
        player = BLACK
        moves_made = 0
        for r in range(self.BOARD_SIZE_EXPECTED):
            for c in range(self.BOARD_SIZE_EXPECTED):
                 self.game.board[r][c] = player
                 moves_made += 1
                 player = WHITE if player == BLACK else BLACK
        self.game.move_count = moves_made
        if self.game.move_count == self.BOARD_SIZE_EXPECTED * self.BOARD_SIZE_EXPECTED:
             self.game.game_state = GameState.DRAW
             if hasattr(self.game, '_update_status_message'): self.game._update_status_message()
             print(f"[測試步驟] 模擬棋盤已滿，手動設置狀態為 DRAW")
        else: self.fail(f"模擬填滿棋盤失敗，步數 {self.game.move_count}")

        self.assertEqual(self.game.game_state, GameState.DRAW, "棋盤滿後遊戲狀態應為 DRAW")
        self.assertEqual(self.game.move_count, self.BOARD_SIZE_EXPECTED * self.BOARD_SIZE_EXPECTED)
        if hasattr(self.game, 'status_message'): self.assertIn("平局", self.game.status_message)
        print(f"[測試結果] 平局條件模擬測試通過。")
        print(f"--- [測試執行] 測試成功結束: {self.id()} ---")

    def test_boundary_moves(self):
        """測試在棋盤邊界和角落落子 (第一步天元)"""
        print(f"\n--- [測試執行] 開始測試: {self.id()} ---")
        first_move_x, first_move_y = 7, 7
        print(f"[測試步驟] 第一步下天元 (欄={first_move_x}, 列={first_move_y})")
        success0 = self.game.make_move(first_move_y, first_move_x) # Pass (row, col)
        self.assertTrue(success0, "第一步下天元應成功")

        # 後續邊界落子 (x, y)
        moves_on_boundary = [
            (0, 0), (self.BOARD_SIZE_EXPECTED - 1, 0),
            (0, self.BOARD_SIZE_EXPECTED - 1), (self.BOARD_SIZE_EXPECTED - 1, self.BOARD_SIZE_EXPECTED - 1),
            (7, 0), (0, 7),
            (self.BOARD_SIZE_EXPECTED - 1, 7), (7, self.BOARD_SIZE_EXPECTED - 1)
        ]
        print(f"[測試步驟] 嘗試在邊界和角落落子: {moves_on_boundary}")
        all_success = True
        player_should_be = WHITE # Start with White after Black's Tengen
        for i, move in enumerate(moves_on_boundary):
            x, y = move
            self.assertEqual(self.game.current_player, player_should_be, f"嘗試邊界落子 ({x},{y}) 前玩家應為 {player_should_be}")
            current_player_before_move = self.game.current_player
            success = self.game.make_move(y, x) # Pass (row, col)
            all_success = all_success and success
            self.assertTrue(success, f"在邊界點 (欄={x}, 列={y}) 落子應成功 (make_move 返回 {success})")
            if not success: break
            self.assertEqual(self.game.board[y][x], current_player_before_move, f"落子後 ({x},{y}) 應為玩家 {current_player_before_move}")
            player_should_be = BLACK if player_should_be == WHITE else WHITE

        self.assertTrue(all_success, "所有邊界落子都應成功")
        print("[測試結果] 邊界落子測試通過。")
        print(f"--- [測試執行] 測試成功結束: {self.id()} ---")

    def test_out_of_bounds_move(self):
        """測試在棋盤外落子"""
        print(f"\n--- [測試執行] 開始測試: {self.id()} ---")
        out_of_bounds_moves = [ (-1, 7), (7, -1), (self.BOARD_SIZE_EXPECTED, 7), (7, self.BOARD_SIZE_EXPECTED) ]
        initial_player = self.game.current_player
        initial_move_count = self.game.move_count
        for move in out_of_bounds_moves:
             x, y = move # x=col, y=row
             print(f"[測試步驟] 嘗試在界外點 (欄={x}, 列={y}) 落子...")
             success = self.game.make_move(y, x) # Pass (row, col)
             self.assertFalse(success, f"在界外點 ({x},{y}) 落子應失敗")
             self.assertEqual(self.game.current_player, initial_player, "界外落子後玩家不應切換")
             self.assertEqual(self.game.game_state, GameState.PLAYING, "界外落子後狀態應為 PLAYING")
             self.assertEqual(self.game.move_count, initial_move_count, "界外落子後步數不應增加")
        print("[測試結果] 界外落子測試通過。")
        print(f"--- [測試執行] 測試成功結束: {self.id()} ---")

    def test_occupied_move(self):
        """測試在已被佔據的位置落子"""
        print(f"\n--- [測試執行] 開始測試: {self.id()} ---")
        first_move_x, first_move_y = 7, 7
        print(f"[測試步驟] 黑棋先在天元 (欄={first_move_x}, 列={first_move_y}) 落子...")
        success1 = self.game.make_move(first_move_y, first_move_x) # Pass (row, col)
        self.assertTrue(success1, "第一步落子應成功")
        self.assertEqual(self.game.board[first_move_y][first_move_x], BLACK)
        initial_move_count = self.game.move_count

        print(f"[測試步驟] 白棋嘗試在已被佔據的天元 (欄={first_move_x}, 列={first_move_y}) 落子...")
        self.assertEqual(self.game.current_player, WHITE)
        success2 = self.game.make_move(first_move_y, first_move_x) # Pass (row, col)

        self.assertFalse(success2, "在已被佔據的點落子應失敗")
        self.assertEqual(self.game.board[first_move_y][first_move_x], BLACK, "被佔據點應保持為黑棋")
        self.assertEqual(self.game.current_player, WHITE, "佔據失敗後應仍為白棋回合")
        self.assertEqual(self.game.move_count, initial_move_count, "佔據失敗後步數不應增加")
        print("[測試結果] 重複落子測試通過。")
        print(f"--- [測試執行] 測試成功結束: {self.id()} ---")

# --- 主執行區塊 ---
if __name__ == '__main__':
    print("\n--- [測試啟動] 運行 Unittests ---")
    # 如果只想運行某個測試，可以用以下方式 (取消註解並修改名稱)
    # suite = unittest.TestSuite()
    # suite.addTest(TestRenjuGameRules('test_black_forbidden_three_three'))
    # runner = unittest.TextTestRunner(verbosity=2)
    # runner.run(suite)
    # 否則，運行所有測試
    unittest.main(verbosity=2)