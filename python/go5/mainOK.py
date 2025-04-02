# -*- coding: utf-8 -*-
import pygame
import sys
from config import WIDTH, HEIGHT, GameState # Import necessary constants and GameState
from utils import get_board_coords, load_best_font # Import helpers
from game_logic import RenjuGame # Import the main game logic class
from drawing import (draw_grid, draw_stones, draw_hover_preview,
                     draw_info_panel, draw_analysis_panel) # Import drawing functions

# --- Main Game Loop ---
def main():
    # --- Initialization ---
    pygame.init()
    try:
        screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("五子棋 (日本規則)")
    except pygame.error as e:
        print(f"Fatal Error: Could not set display mode - {e}")
        sys.exit()

    clock = pygame.time.Clock()

    # --- Load Fonts (Essential for UI rendering) ---
    try:
        font_small = load_best_font(16) # For buttons, timers, move list
        font_medium = load_best_font(20) # For status messages, titles
        if not font_small or not font_medium:
            raise RuntimeError("Required fonts could not be loaded.") # Raise error if fonts fail
    except Exception as e: # Catch potential errors from load_best_font or RuntimeError
        print(f"Fatal Error: Font Loading Failed - {e}")
        pygame.quit()
        sys.exit()

    # --- Game Object ---
    game = RenjuGame()

    # --- UI Element State (Rects for buttons, updated by drawing functions) ---
    info_panel_buttons = {} # Will store {'restart': Rect, 'pause': Rect, ...}
    analysis_nav_buttons = {} # Will store {'first': Rect, 'prev': Rect, ...}

    # --- Main Loop Flag ---
    running = True
    hover_coords = None # Store board coords (r, c) if mouse is hovering

    # === Game Loop ===
    while running:
        # --- Event Handling ---
        mouse_pos = pygame.mouse.get_pos()

        # Determine hover coords only if actively playing
        hover_coords = get_board_coords(mouse_pos[0], mouse_pos[1]) if game.game_state == GameState.PLAYING else None

        try:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                # --- Mouse Click Handling ---
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1: # Left mouse button
                    clicked_ui_element = False

                    # 1. Check Info Panel Buttons
                    for name, rect in info_panel_buttons.items():
                        if rect and rect.collidepoint(mouse_pos):
                            clicked_ui_element = True
                            if name == 'restart':
                                game.restart_game()
                            elif name == 'pause':
                                if game.game_state == GameState.PLAYING: game.pause_game()
                                elif game.game_state == GameState.PAUSED: game.resume_game()
                            elif name == 'save':
                                game.save_game() # Use default filename or prompt later
                            elif name == 'load':
                                game.load_game() # Use default or prompt later
                            break # Stop checking buttons once one is clicked

                    # 2. Check Analysis Navigation Buttons (if not clicked above and in analysis mode)
                    if not clicked_ui_element and game.game_state == GameState.ANALYSIS:
                        for name, rect in analysis_nav_buttons.items():
                            if rect and rect.collidepoint(mouse_pos):
                                clicked_ui_element = True
                                game.analysis_navigate(name) # Pass the direction string ('next', 'prev', etc.)
                                break

                    # 3. Check Board Click (if no UI element clicked and in playing state)
                    if not clicked_ui_element and game.game_state == GameState.PLAYING:
                        click_coords = get_board_coords(mouse_pos[0], mouse_pos[1])
                        if click_coords:
                            game.make_move(click_coords[0], click_coords[1])
                            # Optionally reset hover preview immediately after successful click?
                            # hover_coords = None

                # --- Keyboard Shortcut Handling ---
                if event.type == pygame.KEYDOWN:
                    # Analysis Mode Navigation Shortcuts
                    if game.game_state == GameState.ANALYSIS:
                        if event.key == pygame.K_RIGHT: game.analysis_navigate('next')
                        elif event.key == pygame.K_LEFT: game.analysis_navigate('prev')
                        elif event.key in [pygame.K_UP, pygame.K_HOME]: game.analysis_navigate('first')
                        elif event.key in [pygame.K_DOWN, pygame.K_END]: game.analysis_navigate('last')
                    # Pause/Resume Shortcut (Only when playing/paused)
                    elif game.game_state == GameState.PLAYING and event.key == pygame.K_p:
                        game.pause_game()
                    elif game.game_state == GameState.PAUSED and event.key == pygame.K_p:
                        game.resume_game()
                    # Restart Shortcut (Available anytime, maybe check if game is over?)
                    elif event.key == pygame.K_r:
                        game.restart_game()

        except Exception as e:
            print(f"Error during event handling: {e}")
            # Decide if the error is critical enough to stop the game
            # running = False

        # --- Game Logic Update ---
        try:
            game.update_timers() # Update timers based on game state
        except Exception as e:
            print(f"Error during game logic update (timers): {e}")

        # --- Drawing ---
        try:
            # Determine which board state and last move to draw
            if game.game_state == GameState.ANALYSIS:
                board_to_draw = game.analysis_board
                # In analysis, last_move highlights the currently viewed step
                last_move_to_draw = game.last_move # This is updated by _reconstruct_board_to_step
            else:
                board_to_draw = game.board
                last_move_to_draw = game.last_move

            # 1. Draw the board background and grid lines
            draw_grid(screen) # Should fill the board area

            # 2. Draw stones based on the current/analysis state
            draw_stones(screen, board_to_draw, last_move_to_draw, game.game_state)

            # 3. Draw hover preview if applicable
            if game.game_state == GameState.PLAYING:
                 draw_hover_preview(screen, hover_coords, game.current_player, board_to_draw) # Pass board_to_draw

            # 4. Draw UI Panels (Info and Analysis) - These return button rects for event handling
            # Pass the required fonts to the drawing functions
            info_panel_buttons = draw_info_panel(screen, game, font_small, font_medium)
            analysis_nav_buttons = draw_analysis_panel(screen, game, font_small, font_medium)

            # 5. Update the display
            pygame.display.flip()

        except Exception as e:
            print(f"Error during drawing: {e}")
            # Decide if drawing errors are critical
            # running = False

        # --- Frame Rate Control ---
        clock.tick(30) # Limit FPS to 30

    # --- Cleanup ---
    pygame.quit()
    sys.exit()

# --- Execution Start ---
if __name__ == "__main__":
    main()