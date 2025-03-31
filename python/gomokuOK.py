import pygame
import sys

# 棋盤大小
GRID_SIZE = 19
CELL_SIZE = 40
WIDTH = GRID_SIZE * CELL_SIZE
HEIGHT = GRID_SIZE * CELL_SIZE
PADDING = CELL_SIZE // 2
INFO_PANEL_WIDTH = 200  # 資訊面板寬度
TOTAL_WIDTH = WIDTH + INFO_PANEL_WIDTH

# 顏色
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREY = (128, 128, 128)
BROWN = (200, 150, 100)  # 棋盤顏色
RED = (255, 0, 0)
TRANSPARENT = (0, 0, 0, 0)

# 玩家
PLAYER_BLACK = 1
PLAYER_WHITE = 2

# 遊戲狀態
GAME_ONGOING = 0
GAME_OVER = 1

def init_board():
    """初始化棋盤"""
    board = [[0 for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
    return board

def draw_go_board(screen, board, move_history, hover_pos, current_player):
    """繪製圍棋棋盤和棋子"""
    screen.fill(BROWN)  # 設定背景顏色為棕色

    for row in range(GRID_SIZE):
        # 繪製水平線
        pygame.draw.line(screen, BLACK, (CELL_SIZE // 2, row * CELL_SIZE + CELL_SIZE // 2),
                         (WIDTH - CELL_SIZE // 2, row * CELL_SIZE + CELL_SIZE // 2), 2)

    for col in range(GRID_SIZE):
        # 繪製垂直線
        pygame.draw.line(screen, BLACK, (col * CELL_SIZE + CELL_SIZE // 2, CELL_SIZE // 2),
                         (col * CELL_SIZE + CELL_SIZE // 2, HEIGHT - CELL_SIZE // 2), 2)

    # 繪製星位 (Hoshi)
    hoshi_positions = [(3, 3), (3, 9), (3, 15),
                       (9, 3), (9, 9), (9, 15),
                       (15, 3), (15, 9), (15, 15)]
    for pos in hoshi_positions:
        pygame.draw.circle(screen, BLACK, (pos[1] * CELL_SIZE + CELL_SIZE // 2, pos[0] * CELL_SIZE + CELL_SIZE // 2), 5)

    # 繪製棋子
    for row in range(GRID_SIZE):
        for col in range(GRID_SIZE):
            if board[row][col] == PLAYER_BLACK:
                pygame.draw.circle(screen, BLACK, (col * CELL_SIZE + CELL_SIZE // 2, row * CELL_SIZE + CELL_SIZE // 2), CELL_SIZE // 2 - 5)
            elif board[row][col] == PLAYER_WHITE:
                pygame.draw.circle(screen, WHITE, (col * CELL_SIZE + CELL_SIZE // 2, row * CELL_SIZE + CELL_SIZE // 2), CELL_SIZE // 2 - 5)

    # 繪製半透明棋子 (hover效果)
    if hover_pos:
        row, col = hover_pos
        s = pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA)  # 建立一個 Surface 物件，帶有 alpha 通道
        stone_color = BLACK if current_player == PLAYER_BLACK else WHITE
        pygame.draw.circle(s, stone_color + (128,), (CELL_SIZE // 2, CELL_SIZE // 2), CELL_SIZE // 2 - 5)  # alpha 值為 128，半透明
        screen.blit(s, (col * CELL_SIZE, row * CELL_SIZE)) # 棋子左上角的座標

    # 繪製資訊面板
    pygame.draw.rect(screen, GREY, (WIDTH, 0, INFO_PANEL_WIDTH, HEIGHT))  # 灰色背景
    font = pygame.font.Font(None, 24)
    text_color = BLACK

    # 顯示棋譜
    text_y = 20
    for i, move in enumerate(move_history):
        player = "黑" if (i % 2 == 0) else "白"
        move_str = f"{i+1}. {player}: ({move[1]+1}, {move[0]+1})"  # 棋譜格式：1. 黑: (行列)
        text = font.render(move_str, True, text_color)
        text_rect = text.get_rect(topleft=(WIDTH + 10, text_y))
        screen.blit(text, text_rect)
        text_y += 25

def get_closest_position(x, y):
    """取得最近的有效落子位置"""
    col = round((x - CELL_SIZE // 2) / CELL_SIZE)
    row = round((y - CELL_SIZE // 2) / CELL_SIZE)

    if 0 <= row < GRID_SIZE and 0 <= col < GRID_SIZE:
        return row, col
    else:
        return None

def handle_click(event, board, current_player):
    """處理滑鼠點擊事件"""
    x, y = event.pos
    closest_pos = get_closest_position(x, y)

    if closest_pos:
        row, col = closest_pos
        if board[row][col] == 0:
            return True, row, col
        else:
            return False, None, None
    else:
        return False, None, None

def main():
    """主程式"""
    pygame.init()
    screen = pygame.display.set_mode((TOTAL_WIDTH, HEIGHT))  # 視窗寬度包含資訊面板
    pygame.display.set_caption("圍棋")

    board = init_board()
    current_player = PLAYER_BLACK
    game_state = GAME_ONGOING
    move_history = []  # 紀錄落子歷史
    hover_pos = None # 滑鼠停留的位置

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.MOUSEMOTION:
                # 獲取滑鼠位置並更新 hover_pos
                mouse_x, mouse_y = event.pos
                hover_pos = get_closest_position(mouse_x, mouse_y)

            if event.type == pygame.MOUSEBUTTONDOWN and game_state == GAME_ONGOING:
                success, row, col = handle_click(event, board, current_player)
                if success:
                    board[row][col] = current_player  # 放置棋子
                    move_history.append((row, col))  # 紀錄步數
                    current_player = PLAYER_WHITE if current_player == PLAYER_BLACK else PLAYER_BLACK  # 換玩家

        draw_go_board(screen, board, move_history, hover_pos, current_player)
        pygame.display.flip()

if __name__ == "__main__":
    main()