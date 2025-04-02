# -*- coding: utf-8 -*-
import pygame
import sys
import time
from config import (WIDTH, HEIGHT, GameState, BLACK, WHITE, BOARD_COLOR,
                    BOARD_AREA_WIDTH, BOARD_AREA_HEIGHT) # 導入必要的常量
from utils import get_board_coords, load_best_font # 導入輔助函數
# --- 修改導入：只導入主遊戲類 ---
from game_logic import RenjuGame
# --- 結束修改 ---
from drawing import (draw_grid, draw_stones, draw_hover_preview,
                     draw_info_panel, draw_analysis_panel) # 繪圖函數不變

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
        except EOFError: # Handle Ctrl+D or similar issues
             print("\n輸入終止。使用默認模式 (Human vs AI)。")
             return "human", "ai", "人類 (黑) vs AI (白)" # Default on EOF

# --- Main Game Loop ---
def main():
    # --- 在 Pygame 初始化前選擇模式 ---
    player1_type, player2_type, mode_description = select_game_mode()
    print(f"\n已選擇模式: {mode_description}\n正在啟動遊戲...")

    # --- 初始化 Pygame ---
    pygame.init()
    try:
        screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption(f"五子棋 - {mode_description}") # 更新窗口標題
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
        # --- 計算滑鼠位置和懸停座標 ---
        mouse_pos = pygame.mouse.get_pos()
        # 懸停和點擊只對人類玩家有效
        is_human_turn = (game.game_state == GameState.PLAYING and
                         game.player_types[game.current_player] == "human")
        can_hover = is_human_turn
        hover_coords = get_board_coords(mouse_pos[0], mouse_pos[1]) if can_hover else None

        # --- 事件處理 ---
        human_action_taken_this_frame = False # 重置標誌
        try:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    continue # 退出事件後無需處理其他事件

                # --- 滑鼠點擊處理 ---
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1: # 左鍵點擊
                    human_action_taken_this_frame = True
                    clicked_ui_element = False

                    # 1. 檢查 UI 按鈕 (調用 game 對象的方法)
                    for name, rect in info_panel_buttons.items():
                        if rect and rect.collidepoint(mouse_pos):
                            clicked_ui_element = True
                            if name == 'restart': game.restart_game()
                            elif name == 'pause': game.pause_game() if game.game_state == GameState.PLAYING else game.resume_game() if game.game_state == GameState.PAUSED else None
                            elif name == 'save': game.save_game()
                            elif name == 'load': game.load_game()
                            break # Clicked one button, stop checking

                    if not clicked_ui_element and game.game_state == GameState.ANALYSIS:
                        for name, rect in analysis_nav_buttons.items():
                             if rect and rect.collidepoint(mouse_pos):
                                 clicked_ui_element = True
                                 game.analysis_navigate(name) # Use game object's method
                                 break

                    # 2. 檢查棋盤點擊 (僅限人類玩家回合)
                    if not clicked_ui_element and is_human_turn:
                        click_coords = get_board_coords(mouse_pos[0], mouse_pos[1])
                        if click_coords:
                            game.make_move(click_coords[0], click_coords[1]) # Use game object's method

                # --- 鍵盤快捷鍵處理 ---
                if event.type == pygame.KEYDOWN:
                    human_action_taken_this_frame = True
                    # Keyboard shortcuts (use game object's methods)
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

        # --- 遊戲邏輯更新 (計時器) - Use game object's method ---
        try:
            game.update_timers()
        except Exception as e:
            print(f"遊戲邏輯更新 (計時器) 期間出錯: {e}")


        # --- AI 行動邏輯 ---
        is_ai_turn_now = (game.game_state == GameState.PLAYING and
                          game.player_types[game.current_player] == "ai" and
                          not game.ai_thinking) # Check game's thinking flag
        ai_vs_ai_mode = (player1_type == "ai" and player2_type == "ai")
        allow_ai_move_now = False

        if is_ai_turn_now:
             # AI vs AI 模式下，仍然需要延遲以觀察
             if ai_vs_ai_mode:
                 current_time = time.time()
                 if ai_move_delay_timer is None:
                     ai_move_delay_timer = current_time + 0.5 # Start timer (adjust delay as needed)
                 elif current_time >= ai_move_delay_timer:
                     allow_ai_move_now = True
                     ai_move_delay_timer = None # Reset timer
             else: # 人機模式下，AI 立即行動，延遲在請求後判斷
                 allow_ai_move_now = True

        if allow_ai_move_now:
             try:
                 game.ai_thinking = True # Set thinking flag on game object BEFORE calling AI
                 start_ai_time = time.time()
                 # --- Call game object's method to get AI move ---
                 ai_move, used_book = game.request_ai_move()
                 # --- End Call ---
                 end_ai_time = time.time(); ai_decision_time = end_ai_time - start_ai_time
                 # print(f"AI decision took: {ai_decision_time:.4f} seconds. Used book: {used_book}") # Optional debug

                 # --- AI Makes Move (if found) ---
                 if ai_move:
                     # --- Apply Delay logic corrected ---
                     # Only delay if NOT using book AND it's NOT AI vs AI mode (AIvsAI delay handled above)
                     needs_delay = (not used_book and not ai_vs_ai_mode)

                     if needs_delay:
                         min_total_time = 0.3 # Minimum perceived thinking time for non-book moves in HvAI
                         delay_needed = max(0, min_total_time - ai_decision_time)
                         if delay_needed > 0.01:
                             # print(f"Waiting for {delay_needed:.2f} seconds...") # Optional debug
                             pygame.time.wait(int(delay_needed * 1000))

                     # AI makes the move using the game object's method
                     game.make_move(ai_move[0], ai_move[1])
                 else: # AI cannot find a valid move
                     print("AI cannot find a valid move.")
                     if ai_vs_ai_mode and game.game_state == GameState.PLAYING:
                          # AI vs AI: if one AI can't move, it loses
                          loser = game.current_player; winner = WHITE if loser == BLACK else BLACK
                          game.game_state = GameState.BLACK_WINS if winner == BLACK else GameState.WHITE_WINS
                          loser_name="黑方(AI)" if loser==BLACK else "白方(AI)"; winner_name="黑方(AI)" if winner==BLACK else "白方(AI)"
                          game.status_message = f"{loser_name} 無棋可下! {winner_name} 勝!"
                          print(game.status_message); game._update_status_message() # Ensure status reflects win state

                 # --- Reset thinking flag ---
                 # This should be handled by find_best_move's finally block
                 # game.ai_thinking = False # Removed from here

             except Exception as e:
                 print(f"AI 回合執行期間出錯: {e}")
                 game.ai_thinking = False # Ensure reset on error


        # --- 繪圖 ---
        try:
            screen.fill(BOARD_COLOR) # Clear screen with background color
            draw_grid(screen) # Draw board grid

            # Get appropriate board and last move from game object
            board_to_draw = game.get_board_to_draw()
            last_move_to_draw = game.get_last_move_to_draw()

            # Draw stones (handles PAUSED state internally)
            draw_stones(screen, board_to_draw, last_move_to_draw, game.game_state)

            # Draw hover preview only if it's human's turn
            if can_hover:
                 draw_hover_preview(screen, hover_coords, game.current_player, board_to_draw)

            # Draw UI Panels - These return button rects
            info_panel_buttons = draw_info_panel(screen, game, font_small, font_medium)
            analysis_nav_buttons = draw_analysis_panel(screen, game, font_small, font_medium)

            # Draw "AI Thinking" overlay if needed
            # Ensure checking game.ai_thinking AFTER potential AI move calculation
            if game.ai_thinking:
                 overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                 overlay.fill((100, 100, 100, 180)) # Semi-transparent grey
                 screen.blit(overlay, (0, 0))
                 thinking_surf = font_medium.render("AI 正在思考...", True, (255, 255, 255))
                 screen.blit(thinking_surf, thinking_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2)))

            # Update the display
            pygame.display.flip()

        except Exception as e:
            print(f"繪圖期間發生錯誤: {e}")
            # running = False # Optional: Decide if drawing errors are critical

        # --- 控制幀率 ---
        clock.tick(30) # Limit FPS to 30

    # --- Cleanup ---
    pygame.quit()
    sys.exit()

# --- 程式執行入口 ---
if __name__ == "__main__":
    main()