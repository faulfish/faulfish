# -*- coding: utf-8 -*-
import pygame
import sys
from config import BOARD_SIZE, SQUARE_SIZE, MARGIN, BOARD_AREA_WIDTH, BOARD_AREA_HEIGHT

# --- Helper Functions ---
def is_on_board(r, c):
    """Checks if the given row and column are within the board boundaries."""
    return 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE

def get_board_coords(screen_x, screen_y):
    """Converts screen coordinates (pixels) to board coordinates (row, col)."""
    # Check if click is roughly within the grid lines area
    if not (MARGIN // 2 < screen_x < BOARD_AREA_WIDTH - MARGIN // 2 and
            MARGIN // 2 < screen_y < BOARD_AREA_HEIGHT - MARGIN // 2):
        return None

    # Find the nearest intersection point (col, row)
    col = round((screen_x - MARGIN) / SQUARE_SIZE)
    row = round((screen_y - MARGIN) / SQUARE_SIZE)

    # Calculate the center of the nearest intersection
    center_x = MARGIN + col * SQUARE_SIZE
    center_y = MARGIN + row * SQUARE_SIZE

    # Check if the click is close enough to the intersection center
    click_radius_sq = (SQUARE_SIZE * 0.45) ** 2 # Allow clicking slightly off center
    if (screen_x - center_x)**2 + (screen_y - center_y)**2 <= click_radius_sq:
        # Ensure the calculated row and col are valid board positions
        if 0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE:
            return row, col
    return None # Click was not close enough to an intersection

def format_time(seconds):
    """Formats seconds into MM:SS string."""
    if seconds < 0:
        seconds = 0
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes:02d}:{secs:02d}"

def load_best_font(size, prefer_cjk=True):
    """Attempts to load a preferred CJK font, falling back to default."""
    # List of preferred fonts for CJK display
    preferred_fonts = ["SimHei", "Microsoft YaHei", "PingFang SC", "Noto Sans CJK SC", "WenQuanYi Micro Hei", "sans-serif"]
    try:
        font_name = None
        if prefer_cjk:
            # Try finding a preferred font first
            font_name = pygame.font.match_font(preferred_fonts)

        if font_name:
            # print(f"Using preferred font: {font_name} ({size}pt)") # Optional debug info
            return pygame.font.Font(font_name, size)
        else:
            # print(f"Preferred font not found, using default Pygame font ({size}pt)") # Optional debug info
            return pygame.font.Font(None, size) # Use Pygame's default font
    except Exception as e:
        print(f"Font loading error: {e}. Using default Pygame font.")
        try:
            # Final fallback
            return pygame.font.Font(None, size)
        except Exception as final_e:
            print(f"FATAL: Could not load even default font: {final_e}")
            pygame.quit()
            sys.exit() # Exit if even the default font fails