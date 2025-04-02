# -*- coding: utf-8 -*-
import pygame
import sys
import time
from config import (WIDTH, HEIGHT, GameState, BLACK, WHITE, BOARD_COLOR,
                    BOARD_AREA_WIDTH, BOARD_AREA_HEIGHT)
from utils import get_board_coords, load_best_font
from game_logic import RenjuGame
from drawing import (draw_grid, draw_stones, draw_hover_preview,
                     draw_info_panel, draw_analysis_panel)

def select_game_mode():
    # ... (函數內容不變) ...
    print("\n" + "="*30); print("   選擇遊戲模式:"); print("="*30)
    print("  1. 人類 vs 人類 (Human vs Human)")
    print("  2. 人類 (黑) vs AI (白)")
    print("  3. AI (黑) vs 人類 (白)")
    print("  4. AI vs AI"); print("="*30)
    while True:
        try:
            choice = input("請輸入選項 (1-4): "); choice_num = int(choice)
            if 1 <= choice_num <= 4:
                if choice_num == 1: return "human", "human", "人類 vs 人類"
                elif choice_num == 2: return "human", "ai", "人類 (黑) vs AI (白)"
                elif choice_num == 3: return "ai", "human", "AI (黑) vs 人類 (白)"
                elif choice_num == 4: return "ai", "ai", "AI vs AI"
            else: print("無效選項，請重新輸入。")
        except ValueError: print("輸入無效，請輸入數字 1-4。")
        except EOFError: print("\n輸入終止。使用默認模式 (Human vs AI)。"); return "human", "ai", "人類 (黑) vs AI (白)"


def main():
    player1_type, player2_type, mode_description = select_game_mode()
    print(f"\n已選擇模式: {mode_description}\n正在啟動遊戲...")
    pygame.init()
    try:
        screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption(f"五子棋 - {mode_description}")
    except pygame.error as e: print(f"嚴重錯誤：無法設置顯示模式 - {e}"); sys.exit()
    clock = pygame.time.Clock()
    try:
        font_small = load_best_font(16); font_medium = load_best_font(20)
        if not font_small or not font_medium: raise RuntimeError("無法載入必要的字體。")
    except Exception as e: print(f"嚴重錯誤：字體載入失敗 - {e}"); pygame.quit(); sys.exit()

    game = RenjuGame(black_player_type=player1_type, white_player_type=player2_type)
    info_panel_buttons = {}; analysis_nav_buttons = {}
    running = True; hover_coords = None; ai_move_delay_timer = None

    while running:
        mouse_pos = pygame.mouse.get_pos()
        is_human_turn = (game.game_state == GameState.PLAYING and game.player_types[game.current_player] == "human")
        can_hover = is_human_turn
        hover_coords = get_board_coords(mouse_pos[0], mouse_pos[1]) if can_hover else None

        human_action_taken_this_frame = False
        try:
            for event in pygame.event.get():
                if event.type == pygame.QUIT: running = False; continue
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    human_action_taken_this_frame = True; clicked_ui_element = False
                    for name, rect in info_panel_buttons.items():
                        if rect and rect.collidepoint(mouse_pos):
                            clicked_ui_element = True
                            if name=='restart': game.restart_game()
                            elif name=='pause': game.pause_game() if game.game_state==GameState.PLAYING else game.resume_game() if game.game_state==GameState.PAUSED else None
                            elif name=='save': game.save_game()
                            elif name=='load': game.load_game()
                            break
                    if not clicked_ui_element and game.game_state == GameState.ANALYSIS:
                        for name, rect in analysis_nav_buttons.items():
                             if rect and rect.collidepoint(mouse_pos): clicked_ui_element = True; game.analysis_navigate(name); break
                    if not clicked_ui_element and is_human_turn:
                        click_coords = get_board_coords(mouse_pos[0], mouse_pos[1])
                        if click_coords: game.make_move(click_coords[0], click_coords[1])
                if event.type == pygame.KEYDOWN:
                    human_action_taken_this_frame = True
                    if game.game_state==GameState.ANALYSIS:
                         if event.key==pygame.K_RIGHT: game.analysis_navigate('next')
                         elif event.key==pygame.K_LEFT: game.analysis_navigate('prev')
                         elif event.key in [pygame.K_UP, pygame.K_HOME]: game.analysis_navigate('first')
                         elif event.key in [pygame.K_DOWN, pygame.K_END]: game.analysis_navigate('last')
                    elif game.game_state==GameState.PLAYING and event.key==pygame.K_p: game.pause_game()
                    elif game.game_state==GameState.PAUSED and event.key==pygame.K_p: game.resume_game()
                    elif event.key == pygame.K_r: game.restart_game()
        except Exception as e: print(f"事件處理期間出錯: {e}")

        try:
            if hasattr(game, 'update_timers') and callable(game.update_timers): game.update_timers()
        except Exception as e: print(f"遊戲邏輯更新 (計時器) 期間出錯: {e}")

        is_ai_turn_now = (game.game_state == GameState.PLAYING and
                          game.player_types[game.current_player] == "ai" and
                          not game.ai_thinking)
        ai_vs_ai_mode = (player1_type == "ai" and player2_type == "ai")
        allow_ai_move_now = False

        if is_ai_turn_now:
             if not ai_vs_ai_mode: allow_ai_move_now = True # 人機模式立即執行
             else: # AI vs AI 模式延遲
                 current_time = time.time()
                 if ai_move_delay_timer is None: ai_move_delay_timer = current_time + 0.5 # Start timer
                 elif current_time >= ai_move_delay_timer: allow_ai_move_now = True; ai_move_delay_timer = None

        if allow_ai_move_now:
             try:
                 # print(f"\n--- AI's Turn ({game.current_player}) ---") # Optional debug
                 # 不再在這裡設置 game.ai_thinking = True
                 start_ai_time = time.time()
                 # --- *** 修改：傳入標誌指示是否使用了開局庫 *** ---
                 ai_move, used_book = game.find_best_move(return_book_usage=True)
                 # --- *** 結束修改 ***
                 end_ai_time = time.time(); ai_decision_time = end_ai_time - start_ai_time
                 # print(f"AI decision took: {ai_decision_time:.4f} seconds. Used book: {used_book}") # Optional debug

                 if ai_move:
                     # print(f"AI decided to move at: {ai_move}") # Optional debug
                     # --- *** 修改延遲邏輯 *** ---
                     # 只有在 AI vs AI 且 *沒有* 使用開局庫時才延遲
                     # 或在人機模式下 *沒有* 使用開局庫時才延遲 (可選，讓計算顯得不那麼快)
                     needs_delay = (ai_vs_ai_mode and not used_book) or \
                                   (not ai_vs_ai_mode and not used_book) # <-- 可以調整這個條件
                     if needs_delay:
                         min_total_time = 0.3 # 延遲後至少花費的時間
                         delay_needed = max(0, min_total_time - ai_decision_time)
                         if delay_needed > 0.01:
                             # print(f"Waiting for {delay_needed:.2f} seconds...") # Optional debug
                             pygame.time.wait(int(delay_needed * 1000))
                     # --- *** 結束修改延遲邏輯 *** ---

                     game.make_move(ai_move[0], ai_move[1])
                 else: # AI 無法移動
                     print("AI cannot find a valid move.")
                     if ai_vs_ai_mode and game.game_state == GameState.PLAYING:
                          # AI vs AI 時，一方無法移動則判負
                          loser = game.current_player; winner = WHITE if loser == BLACK else BLACK
                          game.game_state = GameState.BLACK_WINS if winner == BLACK else GameState.WHITE_WINS
                          loser_name="黑方(AI)" if loser==BLACK else "白方(AI)"; winner_name="黑方(AI)" if winner==BLACK else "白方(AI)"
                          game.status_message = f"{loser_name} 無棋可下! {winner_name} 勝!"
                          print(game.status_message)

             except Exception as e: print(f"AI 回合執行期間出錯: {e}"); game.ai_thinking = False # 確保重置

        # --- 繪圖 ---
        try:
            screen.fill(BOARD_COLOR); draw_grid(screen)
            if game.game_state == GameState.ANALYSIS: board_to_draw = game.analysis_board; last_move_to_draw = game.last_move
            else: board_to_draw = game.board; last_move_to_draw = game.last_move
            draw_stones(screen, board_to_draw, last_move_to_draw, game.game_state)
            if can_hover: draw_hover_preview(screen, hover_coords, game.current_player, board_to_draw)
            info_panel_buttons = draw_info_panel(screen, game, font_small, font_medium)
            analysis_nav_buttons = draw_analysis_panel(screen, game, font_small, font_medium)
            if game.ai_thinking: # 繪製思考遮罩
                 overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA); overlay.fill((100, 100, 100, 180))
                 screen.blit(overlay, (0, 0)); thinking_surf = font_medium.render("AI 正在思考...", True, (255, 255, 255))
                 screen.blit(thinking_surf, thinking_surf.get_rect(center=(WIDTH//2, HEIGHT//2)))
            pygame.display.flip()
        except Exception as e: print(f"繪圖期間發生錯誤: {e}") # running = False # 可選

        clock.tick(30)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()