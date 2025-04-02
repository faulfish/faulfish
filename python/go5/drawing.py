# -*- coding: utf-8 -*-
import pygame
from config import (BOARD_SIZE, SQUARE_SIZE, MARGIN, GRID_WIDTH, GRID_HEIGHT,
                    INFO_HEIGHT, ANALYSIS_WIDTH, BOARD_AREA_WIDTH, BOARD_AREA_HEIGHT,
                    WIDTH, HEIGHT, BOARD_COLOR, LINE_COLOR, BLACK_STONE, WHITE_STONE,
                    INFO_BG_COLOR, ANALYSIS_BG_COLOR, INFO_TEXT_COLOR, HIGHLIGHT_COLOR,
                    HOVER_BLACK_COLOR, HOVER_WHITE_COLOR, BUTTON_COLOR, BUTTON_TEXT_COLOR,
                    MOVE_LIST_HIGHLIGHT_COLOR, EMPTY, BLACK, WHITE, GameState,
                    INFO_PANEL_RECT, ANALYSIS_PANEL_RECT) # Import necessary constants and GameState
from utils import format_time # Import helper for time formatting

# --- Drawing Functions ---

def draw_grid(screen):
    """Draws the Renju board grid lines and star points."""
    try:
        # Fill board background
        screen.fill(BOARD_COLOR) # Fill the entire screen first might be better in main loop? No, grid draws board BG.

        # Draw Grid Lines
        for i in range(BOARD_SIZE):
            # Vertical lines
            start_pos_v = (MARGIN + i * SQUARE_SIZE, MARGIN)
            end_pos_v = (MARGIN + i * SQUARE_SIZE, MARGIN + GRID_HEIGHT)
            pygame.draw.line(screen, LINE_COLOR, start_pos_v, end_pos_v)
            # Horizontal lines
            start_pos_h = (MARGIN, MARGIN + i * SQUARE_SIZE)
            end_pos_h = (MARGIN + GRID_WIDTH, MARGIN + i * SQUARE_SIZE)
            pygame.draw.line(screen, LINE_COLOR, start_pos_h, end_pos_h)

        # Draw Star Points (Tengen and corner stars)
        star_points_rc = [(3, 3), (3, 11), (11, 3), (11, 11), (7, 7)] # (row, col) indices
        star_radius = 5
        for r, c in star_points_rc:
            center_x = MARGIN + c * SQUARE_SIZE
            center_y = MARGIN + r * SQUARE_SIZE
            pygame.draw.circle(screen, LINE_COLOR, (center_x, center_y), star_radius)
    except Exception as e:
        print(f"Error drawing grid: {e}")


def draw_stones(screen, board, last_move, game_state):
    """Draws the stones currently on the board."""
    if game_state == GameState.PAUSED:
         # Optionally draw a semi-transparent overlay during pause?
         # For now, just don't draw stones if paused (or draw differently)
         # Let's draw them normally, pause state is indicated elsewhere.
         pass # Proceed to draw normally even if paused

    try:
        stone_radius = SQUARE_SIZE // 2 - 3 # Leave a small gap from the lines
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                player = board[r][c]
                if player != EMPTY:
                    center_x = MARGIN + c * SQUARE_SIZE
                    center_y = MARGIN + r * SQUARE_SIZE
                    stone_color = BLACK_STONE if player == BLACK else WHITE_STONE
                    pygame.draw.circle(screen, stone_color, (center_x, center_y), stone_radius)

        # Highlight the last move
        if last_move:
            r, c = last_move
            if 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE: # Ensure last move is valid
                center_x = MARGIN + c * SQUARE_SIZE
                center_y = MARGIN + r * SQUARE_SIZE
                # Draw a smaller circle or mark inside the last stone
                highlight_radius = stone_radius // 3
                pygame.draw.circle(screen, HIGHLIGHT_COLOR, (center_x, center_y), highlight_radius)
    except Exception as e:
        print(f"Error drawing stones: {e}")


def draw_hover_preview(screen, hover_pos, current_player, board):
    """Draws a semi-transparent preview of the stone if hovering over a valid empty spot."""
    if hover_pos is None:
        return # No hover position

    try:
        r, c = hover_pos
        # Check if the spot is valid and empty on the *current* game board
        if 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE and board[r][c] == EMPTY:
            center_x = MARGIN + c * SQUARE_SIZE
            center_y = MARGIN + r * SQUARE_SIZE
            stone_radius = SQUARE_SIZE // 2 - 3
            hover_color = HOVER_BLACK_COLOR if current_player == BLACK else HOVER_WHITE_COLOR

            # Create a temporary surface for transparency
            temp_surface = pygame.Surface((stone_radius * 2, stone_radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(temp_surface, hover_color, (stone_radius, stone_radius), stone_radius)
            screen.blit(temp_surface, (center_x - stone_radius, center_y - stone_radius))
    except Exception as e:
        print(f"Error drawing hover preview: {e}")


def draw_info_panel(screen, game, font_small, font_medium):
    """Draws the bottom panel with timers, status message, and buttons."""
    # Define button dimensions and positions dynamically
    panel_rect = INFO_PANEL_RECT
    left_padding = 15
    right_padding = panel_rect.width - 15 # Relative to panel width
    timer_y = panel_rect.top + 8
    btn_height = 28
    btn_width = 75
    btn_padding = 8
    btn_y = panel_rect.bottom - btn_height - 8 # Position buttons near the bottom of the panel

    button_area_top_y = btn_y - 4 # Estimate top edge of button area for status centering

    # Initialize return values
    button_rects = {'restart': None, 'pause': None, 'save': None, 'load': None}

    try:
        # Draw Panel Background
        pygame.draw.rect(screen, INFO_BG_COLOR, panel_rect)

        # Check if fonts are loaded
        if not font_small or not font_medium:
            print("Warning: Fonts not loaded for info panel.")
            return button_rects # Return empty rects if fonts failed

        timer_line_height = font_small.get_height()
        status_line_height = font_medium.get_height()

        # Calculate Y position for status message (attempt vertical centering)
        # Center between timer bottom and button top
        status_y = timer_y + (button_area_top_y - timer_y) // 2 - status_line_height // 2
        # status_y = max(status_y, timer_y + timer_line_height + 4) # Ensure it's below timers
        status_y = timer_y


        # --- Draw Timers (only if not in analysis mode) ---
        if game.game_state != GameState.ANALYSIS:
            try:
                black_time_str = format_time(game.timers[BLACK])
                white_time_str = format_time(game.timers[WHITE])
                b_surf = font_small.render(f"黑: {black_time_str}", True, INFO_TEXT_COLOR)
                w_surf = font_small.render(f"白: {white_time_str}", True, INFO_TEXT_COLOR)
                screen.blit(b_surf, (panel_rect.left + left_padding, timer_y))
                screen.blit(w_surf, (panel_rect.left + right_padding - w_surf.get_width(), timer_y))
            except Exception as e:
                print(f"Render Error: Timers - {e}")

        # --- Draw Status Message ---
        try:
            status_surf = font_medium.render(game.status_message, True, INFO_TEXT_COLOR)
            # Center the status message horizontally within the info panel
            status_rect = status_surf.get_rect(centerx=panel_rect.centerx, y=status_y)
            screen.blit(status_surf, status_rect)
        except Exception as e:
            print(f"Render Error: Status Message - {e}")

        # --- Draw Buttons ---
        total_button_width = btn_width * 4 + btn_padding * 3
        start_x = panel_rect.centerx - total_button_width // 2

        # Restart Button
        restart_rect = pygame.Rect(start_x, btn_y, btn_width, btn_height)
        button_rects['restart'] = restart_rect
        pygame.draw.rect(screen, BUTTON_COLOR, restart_rect, border_radius=5)
        restart_text = font_small.render("重新開始", True, BUTTON_TEXT_COLOR)
        screen.blit(restart_text, restart_text.get_rect(center=restart_rect.center))

        # Pause/Resume Button (Appearance/Text changes based on state)
        pause_rect = pygame.Rect(restart_rect.right + btn_padding, btn_y, btn_width, btn_height)
        button_rects['pause'] = pause_rect
        pause_text_str = "恢復" if game.game_state == GameState.PAUSED else "暫停"
        # Button is active only when playing or paused
        is_pause_active = game.game_state in [GameState.PLAYING, GameState.PAUSED]
        pause_btn_color = BUTTON_COLOR if is_pause_active else (160, 160, 160) # Greyed out if inactive
        pause_text_color = BUTTON_TEXT_COLOR if is_pause_active else (210, 210, 210)
        pygame.draw.rect(screen, pause_btn_color, pause_rect, border_radius=5)
        pause_text = font_small.render(pause_text_str, True, pause_text_color)
        screen.blit(pause_text, pause_text.get_rect(center=pause_rect.center))

        # Save Button
        save_rect = pygame.Rect(pause_rect.right + btn_padding, btn_y, btn_width, btn_height)
        button_rects['save'] = save_rect
        pygame.draw.rect(screen, BUTTON_COLOR, save_rect, border_radius=5)
        save_text = font_small.render("儲存棋譜", True, BUTTON_TEXT_COLOR)
        screen.blit(save_text, save_text.get_rect(center=save_rect.center))

        # Load Button
        load_rect = pygame.Rect(save_rect.right + btn_padding, btn_y, btn_width, btn_height)
        button_rects['load'] = load_rect
        pygame.draw.rect(screen, BUTTON_COLOR, load_rect, border_radius=5)
        load_text = font_small.render("載入棋譜", True, BUTTON_TEXT_COLOR)
        screen.blit(load_text, load_text.get_rect(center=load_rect.center))

    except Exception as e:
        print(f"Error drawing info panel: {e}")

    return button_rects # Return the dictionary of button rectangles


def draw_analysis_panel(screen, game, font_small, font_medium):
    """Draws the right-side panel for analysis mode controls and move list."""
    panel_rect = ANALYSIS_PANEL_RECT
    buttons = {} # Dictionary to store navigation button rects: {'first': Rect, 'prev': Rect, ...}

    try:
        # Draw Panel Background
        pygame.draw.rect(screen, ANALYSIS_BG_COLOR, panel_rect)

        # Check if fonts are loaded
        if not font_small or not font_medium:
            print("Warning: Fonts not loaded for analysis panel.")
            return buttons

        # --- Analysis Mode Content ---
        if game.game_state == GameState.ANALYSIS:
            # Define layout constants within analysis mode
            nav_button_area_top_padding = 15
            nav_button_area_height = 80 # Space allocated for nav buttons
            move_list_top_padding = 10
            list_bottom_padding = 10
            list_horizontal_padding = 10

            # Navigation Button Area
            nav_button_area_rect = pygame.Rect(
                panel_rect.left,
                panel_rect.top + nav_button_area_top_padding,
                panel_rect.width,
                nav_button_area_height
            )

            # Move List Area
            move_list_area_rect = pygame.Rect(
                panel_rect.left,
                nav_button_area_rect.bottom + move_list_top_padding,
                panel_rect.width,
                panel_rect.height - nav_button_area_rect.bottom - move_list_top_padding - list_bottom_padding
            )

            # --- Draw Navigation Buttons ---
            btn_w, btn_h = 70, 30
            h_space, v_space = 10, 10
            start_x = nav_button_area_rect.centerx - (btn_w * 2 + h_space) // 2
            current_y = nav_button_area_rect.top

            # Button Row 1: First, Previous
            try:
                first_rect = pygame.Rect(start_x, current_y, btn_w, btn_h)
                buttons['first'] = first_rect
                pygame.draw.rect(screen, BUTTON_COLOR, first_rect, border_radius=5)
                first_surf = font_small.render("<< 首步", True, BUTTON_TEXT_COLOR)
                screen.blit(first_surf, first_surf.get_rect(center=first_rect.center))

                prev_rect = pygame.Rect(first_rect.right + h_space, current_y, btn_w, btn_h)
                buttons['prev'] = prev_rect
                pygame.draw.rect(screen, BUTTON_COLOR, prev_rect, border_radius=5)
                prev_surf = font_small.render("< 上一步", True, BUTTON_TEXT_COLOR)
                screen.blit(prev_surf, prev_surf.get_rect(center=prev_rect.center))
            except Exception as e: print(f"Render Error: Analysis Nav Row 1 - {e}")

            current_y += btn_h + v_space # Move to next row

            # Button Row 2: Next, Last
            try:
                next_rect = pygame.Rect(start_x, current_y, btn_w, btn_h)
                buttons['next'] = next_rect
                pygame.draw.rect(screen, BUTTON_COLOR, next_rect, border_radius=5)
                next_surf = font_small.render("下一步 >", True, BUTTON_TEXT_COLOR)
                screen.blit(next_surf, next_surf.get_rect(center=next_rect.center))

                last_rect = pygame.Rect(next_rect.right + h_space, current_y, btn_w, btn_h)
                buttons['last'] = last_rect
                pygame.draw.rect(screen, BUTTON_COLOR, last_rect, border_radius=5)
                last_surf = font_small.render("末步 >>", True, BUTTON_TEXT_COLOR)
                screen.blit(last_surf, last_surf.get_rect(center=last_rect.center))
            except Exception as e: print(f"Render Error: Analysis Nav Row 2 - {e}")


            # --- Draw Move List ---
            list_display_area = move_list_area_rect.inflate(-list_horizontal_padding * 2, -10) # Inner area for text

            try:
                line_height = font_small.get_linesize() + 2 # Add a little spacing
                if line_height <= 0: # Avoid division by zero if font size is weird
                    return buttons

                max_lines_displayable = list_display_area.height // line_height
                if max_lines_displayable <= 0: return buttons # Cannot display if no space

                if game.move_log:
                    total_moves = len(game.move_log)
                    current_view_step = game.analysis_step # -1 to total_moves-1
                    start_index = 0 # First move index to display

                    # Basic scrolling: try to keep the current move centered
                    if total_moves > max_lines_displayable:
                        # Calculate ideal start index to center the current step
                        ideal_start = max(0, current_view_step - max_lines_displayable // 2)
                        # Adjust if centering pushes start index too far
                        start_index = min(ideal_start, total_moves - max_lines_displayable)
                        start_index = max(0, start_index) # Ensure start_index is not negative

                    for i in range(max_lines_displayable):
                        move_index = start_index + i
                        if move_index >= total_moves:
                            break # Stop if we've run out of moves to display

                        move_data = game.move_log[move_index]
                        player = move_data.get('player')
                        r, c = move_data.get('row', -1), move_data.get('col', -1)
                        time_taken = move_data.get('time')
                        pause_time = move_data.get('pause', 0.0)

                        player_char = "黑" if player == BLACK else "白" if player == WHITE else "?"
                        # Convert (r, c) to standard Go notation (e.g., A1, T15)
                        # Column: A-T (skipping I), Row: 1-15 (board bottom is 1)
                        col_char = chr(ord('A') + c) if 0 <= c < BOARD_SIZE else '?'
                        # if col_char >= 'I': col_char = chr(ord(col_char) + 1) # Skip 'I' if using Go standard
                        row_num = BOARD_SIZE - r if 0 <= r < BOARD_SIZE else '?'
                        coord_str = f"{col_char}{row_num}" if col_char != '?' and row_num != '?' else "(?)"

                        time_str = f"({time_taken:.1f}s)" if time_taken is not None else "(?)"
                        pause_str = f" [P:{pause_time:.1f}s]" if pause_time > 0.05 else "" # Show pause if significant

                        move_text = f"{move_index + 1}. {player_char}{coord_str} {time_str}{pause_str}"

                        is_current_step = (move_index == current_view_step)
                        text_color = MOVE_LIST_HIGHLIGHT_COLOR if is_current_step else INFO_TEXT_COLOR

                        move_surf = font_small.render(move_text, True, text_color)

                        # Truncate text if too wide for the display area
                        max_width = list_display_area.width
                        if move_surf.get_width() > max_width:
                            # Estimate how many chars fit
                             try:
                                 chars_fit = max(1, int(len(move_text) * max_width / move_surf.get_width()) - 2) # -2 for ".."
                                 move_surf = font_small.render(move_text[:chars_fit] + "..", True, text_color)
                             except: # Fallback if render fails
                                 move_surf = font_small.render("...", True, text_color)


                        text_y = list_display_area.top + i * line_height
                        screen.blit(move_surf, (list_display_area.left, text_y))

                else: # No moves in the log
                    no_log_surf = font_small.render("無棋譜記錄", True, INFO_TEXT_COLOR)
                    screen.blit(no_log_surf, no_log_surf.get_rect(center=list_display_area.center))

            except Exception as e:
                print(f"Error rendering move list: {e}")

        else:
             # --- Non-Analysis Mode Content (Optional: could display game title) ---
             # Example: Display "Renju Game" title when not in analysis
             try:
                 title_surf = font_medium.render("五子棋", True, INFO_TEXT_COLOR)
                 title_rect = title_surf.get_rect(centerx=panel_rect.centerx, centery=panel_rect.centery)
                 screen.blit(title_surf, title_rect)
             except Exception as e:
                 print(f"Render Error: Analysis Panel Title - {e}")


    except Exception as e:
        print(f"Error drawing analysis panel: {e}")

    return buttons # Return the dictionary of navigation button rectangles