# -*- coding: utf-8 -*-
import pygame
import sys
import os # 導入 os 模組來檢查檔案是否存在

# --- 常數設定 ---
WIDTH = 600
HEIGHT = 600
LINE_WIDTH = 15
BOARD_ROWS = 3
BOARD_COLS = 3
SQUARE_SIZE = WIDTH // BOARD_COLS
CIRCLE_RADIUS = SQUARE_SIZE // 3
CIRCLE_WIDTH = 15
CROSS_WIDTH = 25
SPACE = SQUARE_SIZE // 4 # X 的線條距離邊緣的距離

# 顏色 (RGB)
BG_COLOR = (28, 170, 156) # 背景色 (青綠色)
LINE_COLOR = (23, 145, 135) # 線條色 (深青綠色)
CIRCLE_COLOR = (239, 231, 200) # O 的顏色 (米白色)
CROSS_COLOR = (66, 66, 66)   # X 的顏色 (深灰色)
MESSAGE_COLOR = (255, 255, 0) # 結束訊息顏色 (黃色)
WIN_LINE_COLOR_X = (80, 80, 80) # X 獲勝線顏色
WIN_LINE_COLOR_O = (255, 255, 255) # O 獲勝線顏色

# --- Pygame 初始化 ---
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption('井字遊戲 (Tic-Tac-Toe) - 按 R 重新開始')
screen.fill(BG_COLOR)

# --- 字體設定 (使用同梱的字體檔案) ---
# !!! 重要：請將下面的字體檔名換成你實際下載並放在腳本旁邊的檔名 !!!
# font_filename = "NotoSansSC-Regular.otf"
# 原來的:
# font_filename = "NotoSansSC-Regular.otf" # 或者你之前的設定

# 修改為指向子目錄中的檔案:
font_filename = "Noto Sans SC/NotoSansSC-VariableFont_wght.ttf"
# 檢查字體檔案是否存在於腳本所在的目錄
font_path = os.path.join(os.path.dirname(__file__), font_filename) if '__file__' in locals() else font_filename

large_font_size = 65 # 主要訊息字體大小
small_font_size = 35 # 提示訊息字體大小

try:
    if not os.path.exists(font_path):
        raise pygame.error(f"字體檔案 '{font_filename}' 不在腳本目錄中！")
    font = pygame.font.Font(font_path, large_font_size)
    small_font = pygame.font.Font(font_path, small_font_size)
    print(f"提示：成功從檔案 '{font_filename}' 載入字體。")
except pygame.error as e:
    print(f"錯誤：無法載入字體檔案 '{font_filename}' ({e})。")
    print("請確保：")
    print(f"1. 你已經下載了字體檔案 (例如 NotoSansSC-Regular.otf)。")
    print(f"2. 將字體檔案放在與 Python 腳本相同的目錄下。")
    print(f"3. 上方的 'font_filename' 變數與你的字體檔名完全一致。")
    print("將使用 Pygame 預設字體，中文將無法顯示。")
    font = pygame.font.Font(None, large_font_size) # 回退到預設字體
    small_font = pygame.font.Font(None, small_font_size)
except Exception as e: # 捕捉其他可能的錯誤
     print(f"載入字體時發生預期外的錯誤：{e}")
     font = pygame.font.Font(None, large_font_size)
     small_font = pygame.font.Font(None, small_font_size)


# --- 遊戲變數 ---
board = [[0 for _ in range(BOARD_COLS)] for _ in range(BOARD_ROWS)]
player = 1 # 1 for X, 2 for O
game_over = False
winner = 0 # 0: no winner, 1: X wins, 2: O wins, 3: Draw

# --- 繪圖函數 ---

def draw_lines():
    """繪製遊戲板的格線"""
    pygame.draw.line(screen, LINE_COLOR, (SQUARE_SIZE, 0), (SQUARE_SIZE, HEIGHT), LINE_WIDTH)
    pygame.draw.line(screen, LINE_COLOR, (2 * SQUARE_SIZE, 0), (2 * SQUARE_SIZE, HEIGHT), LINE_WIDTH)
    pygame.draw.line(screen, LINE_COLOR, (0, SQUARE_SIZE), (WIDTH, SQUARE_SIZE), LINE_WIDTH)
    pygame.draw.line(screen, LINE_COLOR, (0, 2 * SQUARE_SIZE), (WIDTH, 2 * SQUARE_SIZE), LINE_WIDTH)

def draw_figures():
    """根據 board 狀態繪製 O 和 X"""
    for row in range(BOARD_ROWS):
        for col in range(BOARD_COLS):
            if board[row][col] == 2: # 玩家 O
                center_x = col * SQUARE_SIZE + SQUARE_SIZE // 2
                center_y = row * SQUARE_SIZE + SQUARE_SIZE // 2
                pygame.draw.circle(screen, CIRCLE_COLOR, (center_x, center_y), CIRCLE_RADIUS, CIRCLE_WIDTH)
            elif board[row][col] == 1: # 玩家 X
                start_desc = (col * SQUARE_SIZE + SPACE, row * SQUARE_SIZE + SPACE)
                end_desc = (col * SQUARE_SIZE + SQUARE_SIZE - SPACE, row * SQUARE_SIZE + SQUARE_SIZE - SPACE)
                pygame.draw.line(screen, CROSS_COLOR, start_desc, end_desc, CROSS_WIDTH)
                start_asc = (col * SQUARE_SIZE + SPACE, row * SQUARE_SIZE + SQUARE_SIZE - SPACE)
                end_asc = (col * SQUARE_SIZE + SQUARE_SIZE - SPACE, row * SQUARE_SIZE + SPACE)
                pygame.draw.line(screen, CROSS_COLOR, start_asc, end_asc, CROSS_WIDTH)

def mark_square(row, col, player_num):
    """在 board 上標記玩家的選擇"""
    if board[row][col] == 0:
        board[row][col] = player_num
        return True
    return False

def available_square(row, col):
    """檢查格子是否可用"""
    return board[row][col] == 0

def is_board_full():
    """檢查遊戲板是否已滿"""
    for row in range(BOARD_ROWS):
        for col in range(BOARD_COLS):
            if board[row][col] == 0:
                return False
    return True

# --- 遊戲邏輯函數 ---

def check_win(player_num):
    """檢查指定玩家是否獲勝"""
    win_color = WIN_LINE_COLOR_X if player_num == 1 else WIN_LINE_COLOR_O
    # 檢查垂直
    for col in range(BOARD_COLS):
        if board[0][col] == player_num and board[1][col] == player_num and board[2][col] == player_num:
            draw_vertical_winning_line(col, win_color)
            return True
    # 檢查水平
    for row in range(BOARD_ROWS):
        if board[row][0] == player_num and board[row][1] == player_num and board[row][2] == player_num:
            draw_horizontal_winning_line(row, win_color)
            return True
    # 檢查斜線 \
    if board[0][0] == player_num and board[1][1] == player_num and board[2][2] == player_num:
        draw_desc_diagonal(win_color)
        return True
    # 檢查斜線 /
    if board[0][2] == player_num and board[1][1] == player_num and board[2][0] == player_num:
        draw_asc_diagonal(win_color)
        return True
    return False

# --- 繪製勝利線條函數 ---

def draw_vertical_winning_line(col, color):
    posX = col * SQUARE_SIZE + SQUARE_SIZE // 2
    pygame.draw.line(screen, color, (posX, 15), (posX, HEIGHT - 15), LINE_WIDTH // 2 + 1)

def draw_horizontal_winning_line(row, color):
    posY = row * SQUARE_SIZE + SQUARE_SIZE // 2
    pygame.draw.line(screen, color, (15, posY), (WIDTH - 15, posY), LINE_WIDTH // 2 + 1)

def draw_asc_diagonal(color):
    pygame.draw.line(screen, color, (WIDTH - 15, 15), (15, HEIGHT - 15), LINE_WIDTH // 2 + 2)

def draw_desc_diagonal(color):
    pygame.draw.line(screen, color, (15, 15), (WIDTH - 15, HEIGHT - 15), LINE_WIDTH // 2 + 2)

# --- 重置遊戲函數 ---
def restart_game():
    global board, player, game_over, winner
    screen.fill(BG_COLOR)
    draw_lines()
    board = [[0 for _ in range(BOARD_COLS)] for _ in range(BOARD_ROWS)]
    player = 1
    game_over = False
    winner = 0

# --- 顯示訊息函數 ---
def display_message(message, y_offset=0, msg_font=font, msg_color=MESSAGE_COLOR, background_alpha=128):
    """在屏幕中央顯示帶有半透明背景的訊息"""
    # 確保傳入的 font 物件是有效的
    if not isinstance(msg_font, pygame.font.Font):
        print("警告：傳入 display_message 的字體無效，使用預設字體。")
        msg_font = pygame.font.Font(None, 30) # 提供一個備用的小字體

    try:
        text = msg_font.render(message, True, msg_color)
        text_rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + y_offset))

        bg_width = text_rect.width + 40
        bg_height = text_rect.height + 20
        bg_left = text_rect.left - 20
        bg_top = text_rect.top - 10

        overlay = pygame.Surface((bg_width, bg_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, background_alpha))

        screen.blit(overlay, (bg_left, bg_top))
        screen.blit(text, text_rect)
    except Exception as e:
        print(f"渲染訊息 '{message}' 時發生錯誤: {e}")


# --- 主遊戲循環 ---
draw_lines() # 初始繪製格線

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.MOUSEBUTTONDOWN and not game_over:
            mouseX = event.pos[0]
            mouseY = event.pos[1]
            clicked_row = int(mouseY // SQUARE_SIZE)
            clicked_col = int(mouseX // SQUARE_SIZE)

            if 0 <= clicked_row < BOARD_ROWS and 0 <= clicked_col < BOARD_COLS:
                if available_square(clicked_row, clicked_col):
                    mark_square(clicked_row, clicked_col, player)
                    draw_figures() # 在檢查勝負前先畫出棋子
                    if check_win(player):
                        game_over = True
                        winner = player
                    elif is_board_full():
                        game_over = True
                        winner = 3
                    else:
                        player = 2 if player == 1 else 1

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                print("遊戲已重置。")
                restart_game()

    # --- 遊戲結束訊息顯示 ---
    if game_over:
        if winner == 1:
            display_message("玩家 X 獲勝!", y_offset=-40, msg_font=font)
        elif winner == 2:
            display_message("玩家 O 獲勝!", y_offset=-40, msg_font=font)
        elif winner == 3:
            display_message("平局!", y_offset=-40, msg_font=font)

        display_message("按 R 鍵重新開始", y_offset=40, msg_font=small_font)

    # --- 更新畫面顯示 ---
    pygame.display.update()

# --- 退出 Pygame ---
pygame.quit()
sys.exit()