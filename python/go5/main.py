# main.py
import pygame
import sys
import os
import time
from config import (WIDTH, HEIGHT, GameState, BLACK, WHITE, BOARD_COLOR,
                    BOARD_AREA_WIDTH, BOARD_AREA_HEIGHT)
from utils import get_board_coords
from game_logic import RenjuGame
from drawing import (draw_grid, draw_stones, draw_hover_preview,
                     draw_info_panel, draw_analysis_panel, draw_live_threes, 
                     draw_jump_live_threes, draw_live_fours, draw_jump_fours, draw_live_fives, draw_influence_map) # 导入 draw_influence_map

# Use an absolute path here
# font_path = "/Users/alan/Desktop/faulfish/python/go5/Noto Sans SC/NotoSansSC-VariableFont_wght.ttf"  #  <--  YOUR ABSOLUTE PATH HERE
FONT_FILE_PATH = os.path.join("Noto Sans SC", "NotoSansSC-VariableFont_wght.ttf")
# Declare the font here to allow access in multiple functions
font_small = None
font_medium = None


def initialize_fonts():
    """Initializes fonts, handling potential errors."""
    global font_small, font_medium, influence_font  # Access the global variables

    try:
        font_small = pygame.font.Font(FONT_FILE_PATH, 12)  # Smaller font size for font_small
        font_medium = pygame.font.Font(FONT_FILE_PATH, 20)
        influence_font = pygame.font.Font(FONT_FILE_PATH, 40)  # 影响值字体 (原來的兩倍)

        # Check if all fonts loaded successfully
        if not font_small or not font_medium or not influence_font:
            raise RuntimeError("無法載入必要的字體。")
        # No need to return anything, globals are modified directly

    except FileNotFoundError:
        print(f"Error: Font file not found at {FONT_FILE_PATH}")  # Use FONT_FILE_PATH here
        font_small = pygame.font.SysFont("Arial", 12)  # Example fallback with Arial
        font_medium = pygame.font.SysFont("Arial", 20)  # Example fallback with Arial
        influence_font = pygame.font.SysFont("Arial", 40)  # Example fallback with Arial
        # No need to return anything, globals are modified directly

    except Exception as e:
        print(f"嚴重錯誤：字體載入失敗 - {e}")
        pygame.quit()
        sys.exit()


def select_game_mode():
    # ... (不變) ...
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
        initialize_fonts()
        # font_small = pygame.font.Font(None, 12); font_medium = pygame.font.Font(None, 20)
        # influence_font = pygame.font.Font(None, 40)  # 影响值字体 (原來的兩倍)
        if not font_small or not font_medium or not influence_font: raise RuntimeError("無法載入必要的字體。")
    except Exception as e: print(f"嚴重錯誤：字體載入失敗 - {e}"); pygame.quit(); sys.exit()

    game = RenjuGame(black_player_type=player1_type, white_player_type=player2_type)
    info_panel_buttons = {}; analysis_nav_buttons = {}
    running = True; hover_coords = None; ai_move_delay_timer = None
    should_show_thinking_overlay = False

    while running:
        mouse_pos = pygame.mouse.get_pos()
        is_human_turn = (game.game_state == GameState.PLAYING and game.player_types[game.current_player] == "human")
        can_hover = is_human_turn
        hover_coords = get_board_coords(mouse_pos[0], mouse_pos[1]) if can_hover else None

        human_action_taken_this_frame = False
        try: # --- Event Handling ---
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
                        if click_coords:
                            print(f"人類點擊: {click_coords}") # Log
                            game.make_move(click_coords[0], click_coords[1])
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

        # --- Game Logic Update (Timer) ---
        try: game.update_timers()
        except Exception as e: print(f"遊戲邏輯更新 (計時器) 期間出錯: {e}")

        # --- AI Action Logic ---
        is_ai_turn_now = (game.game_state == GameState.PLAYING and
                          game.player_types[game.current_player] == "ai" and
                          not game.ai_thinking) # Check game's thinking flag
        ai_vs_ai_mode = (player1_type == "ai" and player2_type == "ai")
        allow_ai_move_now = False

        if is_ai_turn_now:
             if not ai_vs_ai_mode: allow_ai_move_now = True
             else: # AI vs AI delay
                 current_time = time.time()
                 if ai_move_delay_timer is None: ai_move_delay_timer = current_time + 0.5
                 elif current_time >= ai_move_delay_timer: allow_ai_move_now = True; ai_move_delay_timer = None

        # --- Wrap AI turn in try...finally ---
        if allow_ai_move_now:
             try:
                 game.ai_thinking = True # Set thinking flag BEFORE calculation
                 should_show_thinking_overlay = False # Reset overlay flag

                 start_ai_time = time.time()
                 ai_move, used_book = game.request_ai_move()
                 end_ai_time = time.time(); ai_decision_time = end_ai_time - start_ai_time
                 print(f"AI decision took: {ai_decision_time:.4f} seconds. Used book: {used_book}")

                 if ai_move:
                     needs_delay = (not used_book and not ai_vs_ai_mode)
                     is_slow_calculation = ai_decision_time > 0.05

                     if is_slow_calculation or needs_delay:
                          should_show_thinking_overlay = True # Set overlay flag

                     if needs_delay:
                         min_total_time = 0.3
                         delay_needed = max(0, min_total_time - ai_decision_time)
                         if delay_needed > 0.01: pygame.time.wait(int(delay_needed * 1000))

                     print(f"AI 移動: {ai_move}")  # Log
                     game.make_move(ai_move[0], ai_move[1]) # Make move
                 else: # AI cannot move
                     print("AI cannot find a valid move.")
                     if ai_vs_ai_mode and game.game_state == GameState.PLAYING:
                          loser = game.current_player; winner = WHITE if loser == BLACK else BLACK
                          game.game_state = GameState.BLACK_WINS if winner == BLACK else GameState.WHITE_WINS
                          loser_name="黑方(AI)" if loser==BLACK else "白方(AI)"; winner_name="黑方(AI)" if winner==BLACK else "白方(AI)"
                          game.status_message = f"{loser_name} 無棋可下! {winner_name} 勝!"
                          print(game.status_message); game._update_status_message()

             except Exception as e:
                 print(f"AI 回合執行期間出錯: {e}")
                 # Ensure flag is reset even if calculation/move fails
             finally:
                 game.ai_thinking = False # <-- 重置標誌在 finally 中
        
        influence_map = game.analysis_handler.influence_map # 获取 influence_map
        live_three_positions = game.get_live_three_positions(game.current_player)
        jump_live_three_positions = game.get_jump_live_three_positions(game.current_player)
        live_four_positions = game.get_live_four_positions(game.current_player)
        jump_four_positions = game.get_jump_four_positions(game.current_player)
        five_positions = game.get_five_positions(game.current_player)

        # --- 繪圖 ---
        try:
            screen.fill(BOARD_COLOR); draw_grid(screen)
            board_to_draw = game.get_board_to_draw(); last_move_to_draw = game.get_last_move_to_draw()
            draw_stones(screen, board_to_draw, last_move_to_draw, game.game_state)

            if game.game_state != GameState.PAUSED:
                draw_live_threes(screen, live_three_positions)
                draw_jump_live_threes(screen, jump_live_three_positions)
                draw_live_fours(screen, live_four_positions)
                draw_jump_fours(screen, jump_four_positions)
                draw_live_fives(screen, five_positions)
                draw_influence_map(screen, influence_map, influence_font) # 绘制 influence_map

            if can_hover: draw_hover_preview(screen, hover_coords, game.current_player, board_to_draw)
            info_panel_buttons = draw_info_panel(screen, game, font_small, font_medium)
            analysis_nav_buttons = draw_analysis_panel(screen, game, font_small, font_medium)

            # Draw "AI Thinking" overlay if flag is set
            if should_show_thinking_overlay:
                 overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA); overlay.fill((100, 100, 100, 180))
                 screen.blit(overlay, (0, 0)); thinking_surf = font_medium.render("AI 正在思考...", True, (255, 255, 255))
                 screen.blit(thinking_surf, thinking_surf.get_rect(center=(WIDTH//2, HEIGHT//2)))
                 # Reset overlay flag for next frame
                 should_show_thinking_overlay = False

            pygame.display.flip()
        except Exception as e: print(f"繪圖期間發生錯誤: {e}")

        clock.tick(30)

    pygame.quit(); sys.exit()

if __name__ == "__main__": main()