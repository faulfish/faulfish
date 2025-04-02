# -*- coding: utf-8 -*-
import pygame
import sys
import time
from config import (WIDTH, HEIGHT, GameState, BLACK, WHITE, BOARD_COLOR,
                    BOARD_AREA_WIDTH, BOARD_AREA_HEIGHT)
from utils import get_board_coords, load_best_font
from game_logic import RenjuGame # 導入遊戲邏輯類
from drawing import (draw_grid, draw_stones, draw_hover_preview,
                     draw_info_panel, draw_analysis_panel)

# --- 遊戲模式選擇函數 ---
def select_game_mode():
    """顯示菜單並獲取用戶選擇的遊戲模式，返回玩家類型。"""
    print("\n" + "="*30)
    print("   選擇遊戲模式:")
    print("="*30)
    print("  1. 人類 vs 人類 (Human vs Human)")
    print("  2. 人類 (黑) vs AI (白)")
    print("  3. AI (黑) vs 人類 (白)")
    print("  4. AI vs AI")
    print("="*30)

    while True:
        try:
            choice = input("請輸入選項 (1-4): ")
            choice_num = int(choice)
            if 1 <= choice_num <= 4:
                if choice_num == 1:
                    return "human", "human", "人類 vs 人類"
                elif choice_num == 2:
                    return "human", "ai", "人類 (黑) vs AI (白)"
                elif choice_num == 3:
                    return "ai", "human", "AI (黑) vs 人類 (白)"
                elif choice_num == 4:
                    return "ai", "ai", "AI vs AI"
            else:
                print("無效選項，請重新輸入。")
        except ValueError:
            print("輸入無效，請輸入數字 1-4。")
        except EOFError:
             print("\n輸入終止。使用默認模式 (Human vs AI)。")
             return "human", "ai", "人類 (黑) vs AI (白)" # 或其他默認值

# --- Main Game Loop ---
def main():
    # --- 在 Pygame 初始化前選擇模式 ---
    player1_type, player2_type, mode_description = select_game_mode()
    print(f"\n已選擇模式: {mode_description}")
    print("正在啟動遊戲...")

    # --- 初始化 Pygame ---
    pygame.init()
    try:
        screen = pygame.display.set_mode((WIDTH, HEIGHT))
        # 更新窗口標題以反映模式
        pygame.display.set_caption(f"五子棋 - {mode_description}")
    except pygame.error as e:
        print(f"嚴重錯誤：無法設置顯示模式 - {e}")
        sys.exit()

    clock = pygame.time.Clock()

    # --- 載入字體 ---
    try:
        font_small = load_best_font(16)
        font_medium = load_best_font(20)
        if not font_small or not font_medium:
            raise RuntimeError("無法載入必要的字體。")
    except Exception as e:
        print(f"嚴重錯誤：字體載入失敗 - {e}")
        pygame.quit()
        sys.exit()

    # --- 遊戲物件初始化 (使用選擇的模式) ---
    game = RenjuGame(black_player_type=player1_type, white_player_type=player2_type)

    # --- UI 元素狀態 ---
    info_panel_buttons = {}
    analysis_nav_buttons = {}
    running = True
    hover_coords = None
    ai_move_delay_timer = None # 用於 AI vs AI 模式的視覺延遲

    # === 遊戲主循環 ===
    while running:
        mouse_pos = pygame.mouse.get_pos()
        # 懸停和點擊只對人類玩家有效
        is_human_turn = (game.game_state == GameState.PLAYING and
                         game.player_types[game.current_player] == "human")
        can_hover = is_human_turn
        hover_coords = get_board_coords(mouse_pos[0], mouse_pos[1]) if can_hover else None

        # --- 事件處理 ---
        human_action_taken_this_frame = False
        try:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    continue

                # --- 滑鼠點擊處理 ---
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    human_action_taken_this_frame = True
                    clicked_ui_element = False

                    # 1. 檢查 UI 按鈕
                    # ... (檢查 info_panel_buttons 和 analysis_nav_buttons 的代碼不變) ...
                    for name, rect in info_panel_buttons.items():
                        if rect and rect.collidepoint(mouse_pos):
                            clicked_ui_element = True
                            if name == 'restart':
                                game.restart_game() # restart 會保留選擇的模式
                            # ... 其他按鈕處理 ...
                            elif name == 'pause':
                                if game.game_state == GameState.PLAYING: game.pause_game()
                                elif game.game_state == GameState.PAUSED: game.resume_game()
                            elif name == 'save': game.save_game()
                            elif name == 'load': game.load_game() # load 會讀取文件中的模式
                            break
                    if not clicked_ui_element and game.game_state == GameState.ANALYSIS:
                        for name, rect in analysis_nav_buttons.items():
                             if rect and rect.collidepoint(mouse_pos):
                                clicked_ui_element = True
                                game.analysis_navigate(name)
                                break

                    # 2. 檢查棋盤點擊 (僅限人類玩家回合)
                    if not clicked_ui_element and is_human_turn:
                        click_coords = get_board_coords(mouse_pos[0], mouse_pos[1])
                        if click_coords:
                            game.make_move(click_coords[0], click_coords[1])

                # --- 鍵盤快捷鍵處理 ---
                if event.type == pygame.KEYDOWN:
                    human_action_taken_this_frame = True
                    # ... (快捷鍵處理代碼不變, restart 會保留模式) ...
                    if game.game_state == GameState.ANALYSIS:
                         if event.key == pygame.K_RIGHT: game.analysis_navigate('next')
                         elif event.key == pygame.K_LEFT: game.analysis_navigate('prev')
                         elif event.key in [pygame.K_UP, pygame.K_HOME]: game.analysis_navigate('first')
                         elif event.key in [pygame.K_DOWN, pygame.K_END]: game.analysis_navigate('last')
                    elif game.game_state == GameState.PLAYING and event.key == pygame.K_p: game.pause_game()
                    elif game.game_state == GameState.PAUSED and event.key == pygame.K_p: game.resume_game()
                    elif event.key == pygame.K_r: game.restart_game()

        except Exception as e:
            print(f"事件處理期間出錯: {e}")

        # --- 遊戲邏輯更新 (計時器) ---
        try:
            if hasattr(game, 'update_timers') and callable(game.update_timers):
                 game.update_timers()
        except Exception as e:
            print(f"遊戲邏輯更新 (計時器) 期間出錯: {e}")

        # --- AI 行動邏輯 ---
        is_ai_turn = (game.game_state == GameState.PLAYING and
                      game.player_types[game.current_player] == "ai" and
                      not game.ai_thinking)

        # --- 為 AI vs AI 添加延遲計時器 ---
        ai_vs_ai_mode = (game.player_types[BLACK] == "ai" and game.player_types[WHITE] == "ai")
        allow_ai_move = False
        if is_ai_turn:
             if not ai_vs_ai_mode: # 人機模式下，AI 可以立即思考
                 allow_ai_move = True
             else: # AI vs AI 模式
                 current_time = time.time()
                 if ai_move_delay_timer is None:
                     # 開始計時，例如延遲 0.5 秒後再讓 AI 行動
                     ai_move_delay_timer = current_time + 0.5 # 設置 AI 可以行動的時間點
                     print("AI vs AI: Delaying next AI move...")
                 elif current_time >= ai_move_delay_timer:
                     allow_ai_move = True
                     ai_move_delay_timer = None # 重置計時器，等待下一次 AI 回合

        if allow_ai_move:
             try:
                 print(f"\n--- AI's Turn ({game.current_player}) ---")
                 game.ai_thinking = True # 開始思考

                 # --- 執行 AI 計算 ---
                 start_ai_time = time.time()
                 ai_move = game.find_best_move() # find_best_move 內部會重置 thinking 標誌
                 end_ai_time = time.time()
                 ai_decision_time = end_ai_time - start_ai_time
                 print(f"AI decision took: {ai_decision_time:.4f} seconds.")

                 # --- AI 下棋 ---
                 if ai_move:
                     print(f"AI decided to move at: {ai_move}")
                     # 人機模式下可選延遲，AI vs AI 已有延遲
                     if not ai_vs_ai_mode:
                         min_total_time = 0.3 # 人機模式思考時間短一點
                         delay_needed = max(0, min_total_time - ai_decision_time)
                         if delay_needed > 0.01:
                             # print(f"Waiting for {delay_needed:.2f} seconds...")
                             pygame.time.wait(int(delay_needed * 1000))

                     game.make_move(ai_move[0], ai_move[1])
                 else:
                     print("AI cannot find a valid move.")
                     # 在 AI vs AI 模式下，如果一方無法移動，可能需要特殊處理 (例如判負)
                     if ai_vs_ai_mode and game.game_state == GameState.PLAYING:
                          loser = game.current_player
                          winner = WHITE if loser == BLACK else BLACK
                          game.game_state = GameState.BLACK_WINS if winner == BLACK else GameState.WHITE_WINS
                          loser_name = "黑方(AI)" if loser == BLACK else "白方(AI)"
                          winner_name= "黑方(AI)" if winner == BLACK else "白方(AI)"
                          game.status_message = f"{loser_name} 無棋可下! {winner_name} 勝!"
                          print(game.status_message)


             except Exception as e:
                 print(f"AI 回合執行期間出錯: {e}")
                 game.ai_thinking = False # 確保出錯時重置標誌

        # --- 繪圖 ---
        try:
            screen.fill(BOARD_COLOR)
            draw_grid(screen)

            if game.game_state == GameState.ANALYSIS:
                board_to_draw = game.analysis_board
                last_move_to_draw = game.last_move
            else:
                board_to_draw = game.board
                last_move_to_draw = game.last_move

            draw_stones(screen, board_to_draw, last_move_to_draw, game.game_state)

            if can_hover: # 僅人類回合繪製懸停
                 draw_hover_preview(screen, hover_coords, game.current_player, board_to_draw)

            info_panel_buttons = draw_info_panel(screen, game, font_small, font_medium)
            analysis_nav_buttons = draw_analysis_panel(screen, game, font_small, font_medium)

            if game.ai_thinking: # 疊加思考提示
                 overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                 overlay.fill((100, 100, 100, 180))
                 screen.blit(overlay, (0, 0))
                 thinking_surf = font_medium.render("AI 正在思考...", True, (255, 255, 255))
                 thinking_rect = thinking_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2))
                 screen.blit(thinking_surf, thinking_rect)

            pygame.display.flip()

        except Exception as e:
             print(f"繪圖期間發生錯誤: {e}")
             # running = False # 可選

        clock.tick(30)

    pygame.quit()
    sys.exit()

# --- 程式執行入口 ---
if __name__ == "__main__":
    main()