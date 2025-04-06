# ai_player.py
import random
from config import BOARD_SIZE, EMPTY, BLACK, WHITE, DIRECTIONS
from utils import is_on_board
import rules
# game_io 用於學習，這裡不需要
# analysis 模組會在傳入的 handler 中使用

# --- 可以定義權重常量 ---
WEIGHT_WIN = 100000  # 獲勝或阻止對方獲勝
WEIGHT_FOUR = 1000   # 形成活四/衝四 或 阻止對方活四/衝四
WEIGHT_JUMP_FOUR = 800 # 跳四
WEIGHT_LIVE_THREE = 100 # 活三
WEIGHT_JUMP_LIVE_THREE = 50 # 跳活三
WEIGHT_SLEEP_THREE = 10 # 眠三 (較低，但仍有潛力)
WEIGHT_BLOCK_LIVE_THREE = 150 # 阻止對方活三，價值可能略高於自己活三
WEIGHT_BLOCK_JUMP_LIVE_THREE = 70
WEIGHT_BLOCK_SLEEP_THREE = 15

class AIPlayer:
    def __init__(self):
        pass

    def _evaluate_and_find_best_heuristic(self, board, move_count, ai_player, analysis_handler):
        """
        評估所有合法的下一步棋的啟發式分數，並返回最佳分數的著法列表。
        分數基於形成自身威脅和阻止對手威脅。
        """
        opponent_player = WHITE if ai_player == BLACK else BLACK
        candidate_moves_scores = {} # {(r, c): score}
        best_score = -float('inf')

        # --- 從 AnalysisHandler 獲取已過濾的棋型數據 ---
        # (確保 AnalysisHandler 的 get_player_... 返回的是過濾禁手後的列表)
        ai_fives = analysis_handler.get_player_fives(ai_player)
        ai_fours = analysis_handler.get_player_fours(ai_player)
        ai_jump_fours = analysis_handler.get_player_jump_fours(ai_player)
        ai_live_threes = analysis_handler.get_player_live_threes(ai_player)
        ai_jump_live_threes = analysis_handler.get_player_jump_live_threes(ai_player)
        # 可以考慮加入眠三的數據 (如果 AnalysisHandler 提供)
        # ai_sleep_threes = analysis_handler.get_player_sleep_threes(ai_player)

        opponent_fives = analysis_handler.get_player_fives(opponent_player)
        opponent_fours = analysis_handler.get_player_fours(opponent_player)
        opponent_jump_fours = analysis_handler.get_player_jump_fours(opponent_player)
        opponent_live_threes = analysis_handler.get_player_live_threes(opponent_player)
        opponent_jump_live_threes = analysis_handler.get_player_jump_live_threes(opponent_player)
        # opponent_sleep_threes = analysis_handler.get_player_sleep_threes(opponent_player)

        # --- 遍歷有潛力的空點 ---
        # 可以基於 influence_map 或簡單地遍歷所有空點附近的點
        empty_spots = []
        if move_count == 0: # 特殊處理第一步 (雖然通常會被天元規則覆蓋)
            empty_spots = [(r, c) for r in range(BOARD_SIZE) for c in range(BOARD_SIZE) if board[r][c] == EMPTY]
        else:
            occupied_spots = set((r, c) for r in range(BOARD_SIZE) for c in range(BOARD_SIZE) if board[r][c] != EMPTY)
            adjacent_spots = set()
            offsets = [(dr, dc) for dr in [-1, 0, 1] for dc in [-1, 0, 1] if not (dr == 0 and dc == 0)]
            for r_o, c_o in occupied_spots:
                 for dr, dc in offsets:
                      nr, nc = r_o + dr, c_o + dc
                      if is_on_board(nr, nc) and board[nr][nc] == EMPTY:
                           adjacent_spots.add((nr, nc))
            empty_spots = list(adjacent_spots)
            # 如果相鄰點太少，可以考慮擴大範圍或加入所有 influence > 0 的點
            if not empty_spots:
                 empty_spots = [(r, c) for r in range(BOARD_SIZE) for c in range(BOARD_SIZE) if board[r][c] == EMPTY]


        for r, c in empty_spots:
            # 1. 檢查合法性
            is_valid, _ = rules.is_legal_move(r, c, ai_player, move_count, board)
            if not is_valid:
                continue

            # 2. 計算啟發式分數
            score = 0
            pos_tuple = (r, c) # 用於快速查找

            # --- 進攻分數 ---
            # (檢查時只需要座標，不需要 player 和 type)
            if any(p[0] == r and p[1] == c for p in ai_fives): score += WEIGHT_WIN
            elif any(p[0] == r and p[1] == c for p in ai_fours): score += WEIGHT_FOUR
            elif any(p[0] == r and p[1] == c for p in ai_jump_fours): score += WEIGHT_JUMP_FOUR
            elif any(p[0] == r and p[1] == c for p in ai_live_threes): score += WEIGHT_LIVE_THREE
            elif any(p[0] == r and p[1] == c for p in ai_jump_live_threes): score += WEIGHT_JUMP_LIVE_THREE
            # elif any(p[0] == r and p[1] == c for p in ai_sleep_threes): score += WEIGHT_SLEEP_THREE # 如果有眠三數據

            # --- 防守分數 ---
            if any(p[0] == r and p[1] == c for p in opponent_fives): score += WEIGHT_WIN # 阻止對方五是最高優先級
            elif any(p[0] == r and p[1] == c for p in opponent_fours): score += WEIGHT_BLOCK_LIVE_THREE # 使用稍高的防守權重
            elif any(p[0] == r and p[1] == c for p in opponent_jump_fours): score += WEIGHT_BLOCK_JUMP_LIVE_THREE
            elif any(p[0] == r and p[1] == c for p in opponent_live_threes): score += WEIGHT_BLOCK_LIVE_THREE
            elif any(p[0] == r and p[1] == c for p in opponent_jump_live_threes): score += WEIGHT_BLOCK_JUMP_LIVE_THREE
            # elif any(p[0] == r and p[1] == c for p in opponent_sleep_threes): score += WEIGHT_BLOCK_SLEEP_THREE

            # 基礎分數 (例如靠近中心的點或自己的棋子給微小加分) - 可選
            # score += (7 - abs(r - 7)) * 0.01 + (7 - abs(c - 7)) * 0.01

            # --- 記錄分數 ---
            if score > 0: # 只考慮有正面價值的點
                 candidate_moves_scores[(r, c)] = score
                 if score > best_score:
                      best_score = score

        # --- 找出最佳分數對應的位置 ---
        best_moves = []
        if best_score > -float('inf'): # 確保找到了至少一個有價值的點
            # 如果最高分是致勝/防五，只返回這些點
            if best_score >= WEIGHT_WIN:
                 best_moves = [pos for pos, score in candidate_moves_scores.items() if score >= WEIGHT_WIN]
            else:
                 # 返回所有達到最高分數的點
                 best_moves = [pos for pos, score in candidate_moves_scores.items() if score >= best_score]

        # print(f"AI Heuristic Eval: Best score={best_score}, Found {len(best_moves)} moves: {best_moves}")
        return best_moves


    def find_best_ai_move(self, board, move_log, move_count, current_player, analysis_handler):
        """AI 尋找最佳著法，整合啟發式評估。"""
        ai_player = current_player
        opponent_player = WHITE if ai_player == BLACK else BLACK

        # --- 策略 -1: 天元開局 ---
        if move_count == 0 and ai_player == BLACK:
            if rules.is_legal_move(7, 7, ai_player, move_count, board)[0]:
                # print(f"AI ({ai_player}) mandatory Tengen")
                return (7, 7), False

        # --- 策略 0: 開局庫 (保持不變) ---
        # ... (開局庫邏輯) ...
        if move_count > 0:
            # (假設 OPENING_BOOK 已從 game_io 導入或在此可用)
            from game_io import OPENING_BOOK # 臨時導入示例
            seq = tuple(tuple(m[k] for k in ['row', 'col']) for m in move_log)
            if seq in OPENING_BOOK:
                possible_moves = OPENING_BOOK[seq]
                valid_moves = [m for m in possible_moves if rules.is_legal_move(m[0], m[1], ai_player, move_count, board)[0]]
                if valid_moves:
                    move = random.choice(valid_moves)
                    # print(f"AI ({ai_player}) using book {move} from {len(valid_moves)}")
                    return move, True


        # --- 策略 1: 檢查 AI 能否立即獲勝 ---
        # (需要一個檢查獲勝的輔助函式，或者直接利用 AnalysisHandler 的 five_positions)
        ai_winning_moves = analysis_handler.get_player_fives(ai_player)
        valid_winning_moves = [(r, c) for r, c, _, _ in ai_winning_moves if rules.is_legal_move(r, c, ai_player, move_count, board)[0]]
        if valid_winning_moves:
            move = random.choice(valid_winning_moves)
            # print(f"AI ({ai_player}) found win at {move}")
            return move, False

        # --- 策略 2: 檢查對手能否立即獲勝並阻止 ---
        opponent_winning_moves = analysis_handler.get_player_fives(opponent_player)
        valid_blocking_moves = [(r, c) for r, c, _, _ in opponent_winning_moves if rules.is_legal_move(r, c, ai_player, move_count, board)[0]]
        if valid_blocking_moves:
            # 如果有多個點可以阻止對手獲勝，選擇哪個？
            # 這裡可以簡單隨機選，或者調用啟發式評估來選擇防守價值最高的點
            blocking_scores = {}
            heuristic_block_candidates = self._evaluate_and_find_best_heuristic(board, move_count, ai_player, analysis_handler)
            # 找出既是阻擋點又是啟發式高分點的交集
            preferred_blocks = [move for move in valid_blocking_moves if move in heuristic_block_candidates]
            if preferred_blocks:
                 move = random.choice(preferred_blocks)
                 # print(f"AI ({ai_player}) blocking win strategically at {move}")
            elif valid_blocking_moves: # 如果啟發式沒建議，隨機選一個阻擋點
                 move = random.choice(valid_blocking_moves)
                 # print(f"AI ({ai_player}) blocking win at {move}")
            else: # 理論上不應發生，如果 opponent_winning_moves 有但 valid_blocking_moves 沒有
                 print(f"AI Warning: Opponent has winning moves but AI cannot block?")
                 # Fallback needed here, maybe heuristic?
                 pass
            if 'move' in locals(): return move, False


        # --- 策略 3: 使用啟發式評估選擇最佳著法 ---
        heuristic_best_moves = self._evaluate_and_find_best_heuristic(board, move_count, ai_player, analysis_handler)
        if heuristic_best_moves:
            move = random.choice(heuristic_best_moves) # 從最佳啟發式著法中隨機選一個
            # print(f"AI ({ai_player}) chose heuristic move {move} from {len(heuristic_best_moves)} options.")
            return move, False

        # --- 策略 4: 備用策略 (如果啟發式沒有找到任何有價值的點) ---
        # 可以選擇相鄰點或隨機點
        occupied_spots = set((r, c) for r in range(BOARD_SIZE) for c in range(BOARD_SIZE) if board[r][c] != EMPTY)
        adjacent_spots = set()
        offsets = [(dr, dc) for dr in [-1, 0, 1] for dc in [-1, 0, 1] if not (dr == 0 and dc == 0)]
        for r_o, c_o in occupied_spots:
             for dr, dc in offsets:
                  nr, nc = r_o + dr, c_o + dc
                  if is_on_board(nr, nc) and board[nr][nc] == EMPTY:
                       adjacent_spots.add((nr, nc))

        valid_adjacent_moves = [spot for spot in adjacent_spots if rules.is_legal_move(spot[0], spot[1], ai_player, move_count, board)[0]]

        if valid_adjacent_moves:
            move = random.choice(valid_adjacent_moves)
            # print(f"AI ({ai_player}) chose adjacent fallback {move}")
            return move, False
        else:
            # 最後的備用：隨機選擇任何合法空點
            all_empty_spots = [(r, c) for r in range(BOARD_SIZE) for c in range(BOARD_SIZE) if board[r][c] == EMPTY]
            all_valid_moves = [spot for spot in all_empty_spots if rules.is_legal_move(spot[0], spot[1], ai_player, move_count, board)[0]]
            if all_valid_moves:
                move = random.choice(all_valid_moves)
                # print(f"AI ({ai_player}) chose random fallback {move}")
                return move, False
            else:
                # print(f"AI ({ai_player}) no valid moves!")
                return None, False # 真正無棋可走

        # print(f"Error: AI ({ai_player}) failed to determine move after all checks.") # 理論上不應執行到這裡
        return None, False

    # --- learn_from_ai_loss 保持不變 ---
    def learn_from_ai_loss(self, final_move_log, current_player_types):
        """從 AI 的失敗中學習，更新開局庫。"""
        # ... (之前的學習邏輯) ...
        pass # 佔位符，假設之前的邏輯還在


# --- 在 game_logic.py 中創建實例 ---
# ai_player_instance = AIPlayer() # 或者根據需要命名