import random
from config import BOARD_SIZE, EMPTY, BLACK, WHITE, DIRECTIONS
from utils import is_on_board
import rules
from game_io import OPENING_BOOK, save_opening_book_to_file
import analysis  # 導入 analysis.py

class AIPlayer:  # 封装 AI 逻辑，避免与 game_logic 耦合
    def __init__(self):
        pass  # 你可以在這裡初始化 AI 的內部狀態

    def find_best_ai_move(self, board, move_log, move_count, current_player, analysis_handler):  # 添加 analysis_handler 参数
        """AI 尋找最佳著法，加入開局庫、天元規則、威脅評估和啟發式隨機選擇。"""
        ai_player = current_player
        opponent_player = WHITE if ai_player == BLACK else BLACK
        empty_spots = [(r, c) for r in range(BOARD_SIZE) for c in range(BOARD_SIZE) if board[r][c] == EMPTY]
        occupied_spots = set((r, c) for r in range(BOARD_SIZE) for c in range(BOARD_SIZE) if board[r][c] != EMPTY)

        #analysis_handler._reconstruct_board(len(move_log) - 1)  # 重建棋盤狀態 (在game_logic處理)
        #analysis_handler.update_live_three_positions()  # 更新活三資訊 (在game_logic處理)
        #analysis_handler.update_live_four_positions()  # 更新連四資訊 (在game_logic處理)

        live_three_positions = analysis_handler.get_live_three_positions() #拿取資訊
        four_positions = analysis_handler.get_four_positions()  # 從 AnalysisHandler 獲取
        jump_four_positions = analysis_handler.get_jump_four_positions() # 從 AnalysisHandler 獲取
        five_positions = analysis_handler.get_five_positions()  # 從 AnalysisHandler 獲取 (新增)

        def check_win_or_block(player):
            """檢查是否有立即獲勝的機會或需要阻止對手獲勝。"""
            for r, c in empty_spots:
                if rules.is_legal_move(r, c, ai_player, move_count, board)[0]:
                    board[r][c] = player
                    win = rules.check_win_condition_at(r, c, player, board)
                    board[r][c] = EMPTY  # Revert
                    if win: return (r, c)
            return None

        # Strategy -1: AI Black First Move (Tengen)
        if move_count == 0 and ai_player == BLACK:
            if rules.is_legal_move(7, 7, ai_player, move_count, board)[0]:
                print(f"AI ({ai_player}) mandatory Tengen")
                return (7, 7), False

        # Strategy 0: Opening Book
        if move_count > 0:
            seq = tuple(tuple(m[k] for k in ['row', 'col']) for m in move_log)
            if seq in OPENING_BOOK:
                possible_moves = OPENING_BOOK[seq]
                valid_moves = [m for m in possible_moves if rules.is_legal_move(m[0], m[1], ai_player, move_count, board)[0]]
                if valid_moves:
                    move = random.choice(valid_moves)
                    print(f"AI ({ai_player}) using book {move} from {len(valid_moves)}")
                    return move, True

        # Strategy 1: Win
        winning_move = check_win_or_block(ai_player)
        if winning_move:
            print(f"AI ({ai_player}) found win at {winning_move}")
            return winning_move, False

        # Strategy 2: Block Win
        blocking_move = check_win_or_block(opponent_player)
        if blocking_move:
            print(f"AI ({ai_player}) blocking win at {blocking_move}")
            return blocking_move, False

        def find_threatening_moves(player, threat_level): # Added helper function
            """通用函數，用於尋找特定威脅等級的著法。"""
            threatening_moves = []
            for r, c in empty_spots:
                if rules.is_legal_move(r, c, ai_player, move_count, board)[0]:
                    board[r][c] = player
                    threat_exists = False
                    lines_info = rules.count_line(r, c, player, board)
                    for count, ends in lines_info.values():
                        if count == threat_level and ends >= 1:
                            threat_exists = True
                            break
                    board[r][c] = EMPTY
                    if threat_exists:
                        threatening_moves.append((r, c))
            return threatening_moves

        # Strategy 2.25: Block Threatening Four
        four_blocks = find_threatening_moves(opponent_player, 4)
        if four_blocks:
            move = random.choice(four_blocks)
            print(f"AI ({ai_player}) blocking four at {move}")
            return move, False

        # Strategy 2.5: Block Open Three
        three_blocks = []
        for r, c in empty_spots:
            if rules.is_legal_move(r, c, ai_player, move_count, board)[0]:
                board[r][c] = opponent_player
                forms_open_three = False
                for dr_dc in DIRECTIONS:
                    is_three, is_open = rules.check_specific_line_at(r, c, opponent_player, board, dr_dc, 3)
                    if is_open:
                        lines_info_temp = rules.count_line(r, c, opponent_player, board)
                        count_overall, _ = lines_info_temp[dr_dc]
                        if count_overall == 3:
                            forms_open_three = True
                            break
                board[r][c] = EMPTY
                if forms_open_three:
                    three_blocks.append((r, c))

        if three_blocks:
            move = random.choice(three_blocks)
            print(f"AI ({ai_player}) blocking open three at {move}")
            return move, False

        # Strategy 2.75: Block Opponent's "Sleeping Three to Four" Threat
        sleeping_three_blocks = []
        for r, c in empty_spots:
            if rules.is_legal_move(r, c, ai_player, move_count, board)[0]:
                board[r][c] = opponent_player
                creates_sleeping_threat = False
                lines_info = rules.count_line(r, c, opponent_player, board)
                for count, open_ends in lines_info.values():
                    if count == 3 and open_ends == 1:  # Check for sleeping three pattern
                        creates_sleeping_threat = True
                        break
                board[r][c] = EMPTY
                if creates_sleeping_threat:
                    sleeping_three_blocks.append((r, c))

        if sleeping_three_blocks:
            block_choice = random.choice(sleeping_three_blocks)
            print(f"AI ({ai_player}) blocking sleeping three threat at {block_choice}")
            return block_choice, False

        # Strategy 3: Adjacent/Random
        adjacent_spots = set()
        offsets = [(dr, dc) for dr in [-1, 0, 1] for dc in [-1, 0, 1] if not (dr == 0 and dc == 0)]

        if ai_player == WHITE and move_count == 1 and board[7][7] == BLACK:
            adjacent_spots = {(7 + dr, 7 + dc) for dr, dc in offsets if is_on_board(7 + dr, 7 + dc) and board[7 + dr][7 + dc] == EMPTY}
        else:
            adjacent_spots = {(r_o + dr, c_o + dc) for r_o, c_o in occupied_spots for dr, dc in offsets if is_on_board(r_o + dr, c_o + dc) and board[r_o + dr, c_o + dc] == EMPTY}

        candidate_moves = [spot for spot in adjacent_spots if rules.is_legal_move(spot[0], spot[1], ai_player, move_count, board)[0]]

        # 策略 4: 優先選擇形成活三/連四/連五的位置
        best_moves = []
        for r, c in candidate_moves:
            if (r, c, ai_player, "five") in five_positions:  # 優先連五
                best_moves.append((r, c))
            elif (r, c, ai_player, "four") in four_positions:
                best_moves.append((r, c))
            elif (r, c, ai_player, "jump_four") in jump_four_positions:
                best_moves.append((r, c))
            elif (r, c, ai_player, "live_three") in live_three_positions:
                best_moves.append((r, c))

        if best_moves:
            move = random.choice(best_moves)
            print(f"AI ({ai_player}) chose strategic move (five/four/jump_four/live_three) at {move}...")
            return move, False
        elif candidate_moves:
            move = random.choice(candidate_moves)
            print(f"AI ({ai_player}) chose adjacent {move}...")
            return move, False
        else:
            all_valid_moves = [spot for spot in empty_spots if rules.is_legal_move(spot[0], spot[1], ai_player, move_count, board)[0]]
            if all_valid_moves:
                move = random.choice(all_valid_moves)
                print(f"AI ({ai_player}) chose random {move}...")
                return move, False
            else:
                print(f"AI ({ai_player}) no valid moves!")
                return None, False

        print(f"Error: AI ({ai_player}) failed to determine move after all checks.")
        return None, False


    def learn_from_ai_loss(self, final_move_log, current_player_types):
        """從 AI 的失敗中學習，更新開局庫。"""
        print("--- Entering AI learn_from_loss ---")
        if not final_move_log or len(final_move_log) < 2:
            print("Learn: Log too short.")
            return

        winner = final_move_log[-1].get('player')
        loser = WHITE if winner == BLACK else BLACK
        if current_player_types.get(loser) != "ai":
            print(f"Learn: Loser {loser} not AI.")
            return

        ai_last_idx = next((i for i in range(len(final_move_log) - 2, -1, -1) if final_move_log[i].get('player') == loser), -1)
        if ai_last_idx == -1:
            print(f"Learn: AI {loser} move not found before loss.")
            return

        ai_losing_data = final_move_log[ai_last_idx]
        losing_move = tuple(ai_losing_data[k] for k in ['row', 'col'])
        seq_before = final_move_log[:ai_last_idx]
        key_seq = tuple(tuple(m[k] for k in ['row', 'col']) for m in seq_before)
        print(f"Learn: AI {loser} lost. Last AI move {losing_move} at index {ai_last_idx}")
        print(f"Learn: Sequence key {key_seq}")

        # Reconstruct board state
        print("Learn: Reconstructing board state...")
        temp_board = [[EMPTY for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
        current_move_count = 0
        for i, m in enumerate(seq_before):
            r, c, p = m.get('row', -1), m.get('col', -1), m.get('player', 0)
            if not is_on_board(r, c) or temp_board[r][c] != EMPTY:
                print(f"Learn Err: Recon failed at step {i + 1} ({r},{c}). Invalid coord or overwrite.")
                return
            temp_board[r][c] = p
            current_move_count += 1

        print("Learn: Board reconstructed.")

        # Find alternative valid moves
        print(f"Learn: Finding valid moves for player {loser} (move_count={current_move_count})...")
        valid_moves = [(r, c) for r in range(BOARD_SIZE) for c in range(BOARD_SIZE)
                       if temp_board[r][c] == EMPTY and rules.is_legal_move(r, c, loser, current_move_count, temp_board)[0]]

        print(f"Learn: Found {len(valid_moves)} valid moves then: {valid_moves}")
        alternatives = [m for m in valid_moves if m != losing_move]
        print(f"Learn: Losing move {losing_move}. Found {len(alternatives)} alternatives: {alternatives}")

        # Update book
        book_entry = OPENING_BOOK.get(key_seq)
        updated = False

        if isinstance(book_entry, list):
            if losing_move in book_entry:
                book_entry.remove(losing_move)
                print(f"Learn: Removed {losing_move} from book list for {key_seq}.")
                if not book_entry:
                    del OPENING_BOOK[key_seq]
                    print(f"Learn: Removed key {key_seq} as list empty.")
                updated = True
            else:
                print(f"Learn: Losing move {losing_move} not in book list {book_entry}. No update.")
        elif book_entry == losing_move:
            if alternatives:
                new_move = random.choice(alternatives)
                OPENING_BOOK[key_seq] = [new_move]
                print(f"Learn: Replaced single losing {losing_move} with [{new_move}] for {key_seq}.")
                updated = True
            else:
                del OPENING_BOOK[key_seq]
                print(f"Learn: Removed single losing {key_seq} no alternatives.")
                updated = True
        elif book_entry is None and alternatives:
            new_move = random.choice(alternatives)
            OPENING_BOOK[key_seq] = [new_move]
            print(f"Learn: Added new seq {key_seq} to book with [{new_move}].")
            updated = True
        else:
            print(f"Learn: No update needed/possible. Entry: {book_entry}, Alts: {len(alternatives)}")

        if updated:
            print("Learn: Saving updated book...")
            save_opening_book_to_file(OPENING_BOOK)
            print("Learn: Save called.")
        else:
            print("Learn: No changes to opening book.")
        print("--- Exiting learn_from_loss ---")

#  创建 AIPlayer 实例 (在 game_logic 中)
ai_player = AIPlayer()

# 修改 game_logic.py 中的 request_ai_move

# --- AI move ---
#def request_ai_move(self):
#    """請求 AI 計算下一步著法。"""
#    if self.game_state != GameState.PLAYING or self.player_types[self.current_player] != "ai":
#        return None, False
#    # 調用 ai_player 模塊的函數
#    move, used_book = ai_player.find_best_ai_move(
#        self.board, self.move_log, self.move_count, self.current_player, self.analysis_handler
#    )
#    return move, used_book

if __name__ == '__main__':
    # 示例用法 (需要實現 config, utils, rules, game_io 等模組)
    # 這只是一個骨架，你需要根據你的實際遊戲環境來調整
    # 例如創建一個棋盤，模擬一些移動，然後調用 AI 函數
    print("This file contains the AI logic.  It needs to be integrated with a game environment.")
    # Example Usage (Illustrative - Requires Setup of other modules)
    board = [[EMPTY for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
    move_log = []
    current_player = BLACK
    current_player_types = {BLACK: "ai", WHITE: "human"}  # Or "ai" for both
    move_count = 0

    # Simulate a few moves
    board[7][7] = BLACK
    move_log.append({'row': 7, 'col': 7, 'player': BLACK})
    board[6][7] = WHITE
    move_log.append({'row': 6, 'col': 7, 'player': WHITE})

    # Create dummy Game and AnalysisHandler for testing
    class Game:
        def __init__(self, board, move_log):
            self.board = board
            self.move_log = move_log
            self.game_state = "playing" # Just for test
    game = Game(board, move_log) # Create a Game instance
    analysis_handler = analysis.AnalysisHandler(game) # Initialize AnalysisHandler
    analysis_handler._reconstruct_board(len(move_log) - 1)
    analysis_handler.update_live_three_positions() #更新棋型
    analysis_handler.update_live_four_positions()

    best_move, used_book = ai_player.find_best_ai_move(board, move_log, move_count, current_player, analysis_handler) # pass handler

    if best_move:
        print(f"AI suggests move: {best_move}")
        # ... (Update board, move_log, and other game state variables)

    # Example of learning after a game
    # ... (Simulate game to completion, record final_move_log)

    # learn_from_ai_loss(final_move_log, current_player_types)