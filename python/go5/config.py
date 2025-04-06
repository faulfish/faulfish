# -*- coding: utf-8 -*-
import pygame
from enum import Enum, auto

# --- Enums ---
class GameState(Enum):
    PLAYING = auto()
    PAUSED = auto()
    BLACK_WINS = auto()
    WHITE_WINS = auto()
    DRAW = auto()
    ANALYSIS = auto()

# --- Constants ---
BOARD_SIZE = 15
SQUARE_SIZE = 40
MARGIN = 30
GRID_WIDTH = (BOARD_SIZE - 1) * SQUARE_SIZE
GRID_HEIGHT = (BOARD_SIZE - 1) * SQUARE_SIZE
INFO_HEIGHT = 80
ANALYSIS_WIDTH = 180
BOARD_AREA_WIDTH = GRID_WIDTH + 2 * MARGIN
BOARD_AREA_HEIGHT = GRID_HEIGHT + 2 * MARGIN
WIDTH = BOARD_AREA_WIDTH + ANALYSIS_WIDTH
HEIGHT = BOARD_AREA_HEIGHT + INFO_HEIGHT

# Colors
BOARD_COLOR = (210, 180, 140)
LINE_COLOR = (50, 50, 50)
BLACK_STONE = (10, 10, 10)
WHITE_STONE = (245, 245, 245)
INFO_BG_COLOR = (200, 200, 200)
ANALYSIS_BG_COLOR = (215, 215, 215)
INFO_TEXT_COLOR = (0, 0, 0)
HIGHLIGHT_COLOR = (255, 0, 0)
HOVER_BLACK_COLOR = (10, 10, 10, 120)
HOVER_WHITE_COLOR = (245, 245, 245, 120)
BUTTON_COLOR = (100, 100, 180)
BUTTON_TEXT_COLOR = (255, 255, 255)
MOVE_LIST_HIGHLIGHT_COLOR = (0, 0, 200)
MARKER_COLOR_CURRENT_PLAYER = (0, 150, 255)  # 例如：亮藍色，表示當前玩家的機會
MARKER_COLOR_OPPONENT = (255, 100, 100)  # 例如：亮紅色，表示對手的威脅
WINNING_MOVE_HIGHLIGHT_COLOR = (255, 215, 0) # 例如：金色，標示致勝點

# Players & Game Elements
EMPTY = 0
BLACK = 1
WHITE = 2
EDGE = -1 # Used internally for edge detection in checks

# Directions for checking lines
DIRECTIONS = [(0, 1), (1, 0), (1, 1), (1, -1)] # Horizontal, Vertical, Diag\, Diag/

# Game Settings
DEFAULT_TIME_LIMIT = 10 * 60 # Default time limit in seconds (10 minutes)

# Pygame specific (consider if utils is better place, but they relate to dimensions)
INFO_PANEL_RECT = pygame.Rect(0, BOARD_AREA_HEIGHT, WIDTH - ANALYSIS_WIDTH, INFO_HEIGHT)
ANALYSIS_PANEL_RECT = pygame.Rect(BOARD_AREA_WIDTH, 0, ANALYSIS_WIDTH, HEIGHT)