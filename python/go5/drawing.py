# -*- coding: utf-8 -*-
import pygame
from config import (BOARD_SIZE, SQUARE_SIZE, MARGIN, GRID_WIDTH, GRID_HEIGHT,
                    INFO_HEIGHT, ANALYSIS_WIDTH, BOARD_AREA_WIDTH, BOARD_AREA_HEIGHT,
                    WIDTH, HEIGHT, BOARD_COLOR, LINE_COLOR, BLACK_STONE, WHITE_STONE,
                    INFO_BG_COLOR, ANALYSIS_BG_COLOR, INFO_TEXT_COLOR, HIGHLIGHT_COLOR,
                    HOVER_BLACK_COLOR, HOVER_WHITE_COLOR, BUTTON_COLOR, BUTTON_TEXT_COLOR,
                    MOVE_LIST_HIGHLIGHT_COLOR, EMPTY, BLACK, WHITE, GameState,
                    INFO_PANEL_RECT, ANALYSIS_PANEL_RECT,MARKER_COLOR_CURRENT_PLAYER,MARKER_COLOR_OPPONENT,WINNING_MOVE_HIGHLIGHT_COLOR)
from utils import format_time

def draw_grid(screen):
    """繪製 Renju 棋盤格線和星位點。"""
    try:
        # 繪製棋盤區域背景色
        board_rect = pygame.Rect(0, 0, BOARD_AREA_WIDTH, BOARD_AREA_HEIGHT)
        pygame.draw.rect(screen, BOARD_COLOR, board_rect)

        # 繪製格線
        for i in range(BOARD_SIZE):
            # 垂直線
            start_pos_v = (MARGIN + i * SQUARE_SIZE, MARGIN)
            end_pos_v = (MARGIN + i * SQUARE_SIZE, MARGIN + GRID_HEIGHT)
            pygame.draw.line(screen, LINE_COLOR, start_pos_v, end_pos_v)
            # 水平線
            start_pos_h = (MARGIN, MARGIN + i * SQUARE_SIZE)
            end_pos_h = (MARGIN + GRID_WIDTH, MARGIN + i * SQUARE_SIZE)
            pygame.draw.line(screen, LINE_COLOR, start_pos_h, end_pos_h)

        # 繪製星位點 (天元和角落星位)
        star_points_rc = [(3, 3), (3, 11), (11, 3), (11, 11), (7, 7)]  # (row, col) 索引
        star_radius = 5
        for r, c in star_points_rc:
            center_x = MARGIN + c * SQUARE_SIZE
            center_y = MARGIN + r * SQUARE_SIZE
            pygame.draw.circle(screen, LINE_COLOR, (center_x, center_y), star_radius)
    except Exception as e:
        print(f"繪製格線時出錯: {e}")


def draw_stones(screen, board, last_move, game_state):
    """繪製棋盤上目前的棋子。"""
    try:
        if game_state != GameState.PAUSED:
            stone_radius = SQUARE_SIZE // 2 - 3  # 留下與格線的小間隙
            for r in range(BOARD_SIZE):
                for c in range(BOARD_SIZE):
                    player = board[r][c]
                    if player != EMPTY:
                        center_x = MARGIN + c * SQUARE_SIZE
                        center_y = MARGIN + r * SQUARE_SIZE
                        stone_color = BLACK_STONE if player == BLACK else WHITE_STONE
                        pygame.draw.circle(screen, stone_color, (center_x, center_y), stone_radius)

            # 高亮標示最後一步棋
            if last_move:
                r, c = last_move
                # 在繪製高亮前確保 last_move 座標有效
                if 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE:
                    center_x = MARGIN + c * SQUARE_SIZE
                    center_y = MARGIN + r * SQUARE_SIZE
                    highlight_radius = stone_radius // 3
                    pygame.draw.circle(screen, HIGHLIGHT_COLOR, (center_x, center_y), highlight_radius)
    except Exception as e:
        print(f"繪製棋子時出錯: {e}")


def draw_live_threes(screen, live_three_positions, current_player):
    """在棋盘上标记下一手活三的位置。"""
    _draw_pattern_marks(screen, live_three_positions, current_player, "circle", True)  # 紅色，空心圓

def draw_jump_live_threes(screen, jump_live_three_positions, current_player):
    """在棋盘上标记下一手跳活三的位置。"""
    _draw_pattern_marks(screen, jump_live_three_positions, current_player, "circle")  # 藍色，空心圓

def draw_live_fours(screen, live_four_positions, current_player):
    """在棋盘上标记下一手活四的位置。"""
    _draw_pattern_marks(screen, live_four_positions, current_player, "square")  # 紅色，空心正方形

def draw_jump_fours(screen, jump_four_positions, current_player):
    """在棋盘上标记下一手跳四的位置。"""
    _draw_pattern_marks(screen, jump_four_positions, current_player, "square")  # 藍色，空心正方形

def draw_live_fives(screen, live_five_positions, current_player):
    """在棋盘上标记下一手五連的位置。"""
    _draw_pattern_marks(screen, live_five_positions, current_player, "triangle", True)  # 藍色，實心三角形

def _draw_pattern_marks(screen, positions_dict, current_player, shape="circle", filled=False):
    """在棋盤上繪製指定樣式標記的輔助函式，顏色區分當前玩家和對手。

    Args:
        screen: pygame 的 screen 物件，用於繪製。
        positions_dict: 包含要繪製標記的位置的字典 {player: [(r, c, p, type), ...]}.
        current_player: 當前輪到誰下棋 (BLACK 或 WHITE).
        shape: 標記的形狀 ("circle", "square", "triangle").
        filled: 是否繪製實心標記。
    """
    mark_radius = SQUARE_SIZE // 4
    mark_thickness = 0 if filled else 2

    if not isinstance(positions_dict, dict):
        # 維持之前的警告，以防萬一
        print(f"警告: _draw_pattern_marks 預期收到字典，但收到了 {type(positions_dict)}。")
        return

    for player_key, player_specific_positions in positions_dict.items():
        # 根據這個威脅屬於誰，選擇顏色
        marker_color = MARKER_COLOR_CURRENT_PLAYER if player_key == current_player else MARKER_COLOR_OPPONENT

        for r, c, player, pattern_type in player_specific_positions:
            try:
                center_x = MARGIN + c * SQUARE_SIZE
                center_y = MARGIN + r * SQUARE_SIZE

                # 使用選擇的 marker_color 進行繪製
                if shape == "circle":
                    pygame.draw.circle(screen, marker_color, (center_x, center_y), mark_radius, mark_thickness)
                elif shape == "square":
                    pygame.draw.rect(screen, marker_color, (center_x - mark_radius, center_y - mark_radius,
                                                         mark_radius * 2, mark_radius * 2), mark_thickness)
                elif shape == "triangle":
                    point1 = (center_x, center_y - mark_radius)
                    point2 = (center_x - mark_radius, center_y + mark_radius)
                    point3 = (center_x + mark_radius, center_y + mark_radius)
                    points = [point1, point2, point3]
                    pygame.draw.polygon(screen, marker_color, points, mark_thickness)
                else:
                    print(f"警告: 未知的標記形狀: {shape}")

            except Exception as e:
                print(f"繪製 {shape} 標記在 ({r},{c}) 時出錯: {e}")

def draw_winning_move_highlight(screen, winning_positions_list):
    """用特殊的雙圈標記標示立即致勝的位置。

    Args:
        screen: pygame screen 物件。
        winning_positions_list: 包含 (r, c, player, pattern_type) 元組的列表，
                                這些是當前玩家可以下子獲勝的位置。
    """
    outer_radius = SQUARE_SIZE // 3  # 外圈半徑稍大
    inner_radius = SQUARE_SIZE // 5  # 內圈半徑
    line_thickness = 2              # 圈的線寬

    if not winning_positions_list:
        return

    # winning_positions_list 預期是特定玩家的列表
    for r, c, player, pattern_type in winning_positions_list:
        try:
            center_x = MARGIN + c * SQUARE_SIZE
            center_y = MARGIN + r * SQUARE_SIZE

            # 繪製外圈
            pygame.draw.circle(screen, WINNING_MOVE_HIGHLIGHT_COLOR, (center_x, center_y), outer_radius, line_thickness)
            # 繪製內圈
            pygame.draw.circle(screen, WINNING_MOVE_HIGHLIGHT_COLOR, (center_x, center_y), inner_radius, line_thickness)

        except Exception as e:
            print(f"繪製致勝點標記在 ({r},{c}) 時出錯: {e}")

# --- 如何調用（示例，假設在主繪圖循環或 draw_analysis_info 函數中） ---
# 假設 analysis_handler 已經更新
# live_threes = analysis_handler.get_live_three_positions() # 這裡不傳 player，得到包含黑白雙方的字典
# fours = analysis_handler.get_four_positions()
# ... 等等

# if show_analysis: # 假設有一個控制是否顯示分析的變數
#     _draw_pattern_marks(screen, live_threes, (0, 0, 255), "circle")  # 用藍色圓圈標記所有活三潛力點
#     _draw_pattern_marks(screen, fours, (255, 0, 0), "square")      # 用紅色方塊標記所有四潛力點
#     # ... 為其他棋型調用 ...

def draw_influence_map(screen, influence_map, font):
    """在棋盘上绘制影响力的值。"""
    try:
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                value = influence_map[r][c]
                text_surface = font.render(str(value), True, (128, 128, 128))  # 使用灰色
                text_rect = text_surface.get_rect(center=(MARGIN + c * SQUARE_SIZE, MARGIN + r * SQUARE_SIZE))
                screen.blit(text_surface, text_rect)
    except Exception as e:
        print(f"繪製影響力地圖時出錯: {e}")


def draw_hover_preview(screen, hover_pos, current_player, board):
    """如果滑鼠懸停在有效的空位置上，則繪製半透明的預覽棋子。"""
    if hover_pos is None:
        return  # 沒有懸停位置

    try:
        r, c = hover_pos
        if 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE and board[r][c] == EMPTY:
            center_x = MARGIN + c * SQUARE_SIZE
            center_y = MARGIN + r * SQUARE_SIZE
            stone_radius = SQUARE_SIZE // 2 - 3
            hover_color = HOVER_BLACK_COLOR if current_player == BLACK else HOVER_WHITE_COLOR

            # 創建一個臨時表面以實現透明度
            temp_surface = pygame.Surface((stone_radius * 2, stone_radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(temp_surface, hover_color, (stone_radius, stone_radius), stone_radius)
            screen.blit(temp_surface, (center_x - stone_radius, center_y - stone_radius))
    except Exception as e:
        print(f"繪製懸停預覽時出錯: {e}")


def draw_info_panel(screen, game, font_small, font_medium):
    """繪製底部的資訊面板，包含計時器、狀態訊息和按鈕。"""
    button_rects = {'restart': None, 'pause': None, 'save': None, 'load': None}  # 初始化返回值

    try:
        # 動態定義按鈕尺寸和位置
        panel_rect = INFO_PANEL_RECT
        left_padding = 15
        right_padding = panel_rect.width - 15  # 相對於面板寬度
        timer_y = panel_rect.top + 8
        btn_height = 28
        btn_width = 75
        btn_padding = 8
        btn_y = panel_rect.bottom - btn_height - 8  # 將按鈕放置在面板底部附近
        button_area_top_y = btn_y - 4  # 估計按鈕區域的頂部邊緣，用於狀態訊息垂直居中


        # 繪製面板背景
        pygame.draw.rect(screen, INFO_BG_COLOR, panel_rect)

        # 檢查字體是否已載入
        if not font_small or not font_medium:
            print("警告：資訊面板所需字體未載入。")
            return button_rects  # 如果字體載入失敗，返回空的 Rect 字典

        timer_line_height = font_small.get_height()
        status_line_height = font_medium.get_height()

        # 計算狀態訊息的 Y 位置 (嘗試垂直居中)
        status_y = timer_y + (button_area_top_y - timer_y) // 2 - status_line_height // 2
        status_y = timer_y  # 確保狀態訊息在計時器下方


        # --- 繪製計時器 (僅在非分析模式下) ---
        if game.game_state != GameState.ANALYSIS:
            try:
                black_time_str = format_time(game.timers[BLACK])
                white_time_str = format_time(game.timers[WHITE])
                b_surf = font_small.render(f"黑: {black_time_str}", True, INFO_TEXT_COLOR)
                w_surf = font_small.render(f"白: {white_time_str}", True, INFO_TEXT_COLOR)
                screen.blit(b_surf, (panel_rect.left + left_padding, timer_y))
                screen.blit(w_surf, (panel_rect.left + right_padding - w_surf.get_width(), timer_y))
            except Exception as e:
                print(f"渲染錯誤：計時器 - {e}")

        # --- 繪製狀態訊息 ---
        try:
            status_surf = font_medium.render(game.status_message, True, INFO_TEXT_COLOR)
            status_rect = status_surf.get_rect(centerx=panel_rect.centerx, y=status_y)  # 水平居中
            screen.blit(status_surf, status_rect)
        except Exception as e:
            print(f"渲染錯誤：狀態訊息 - {e}")

        # --- 繪製按鈕 ---
        total_button_width = btn_width * 4 + btn_padding * 3
        start_x = panel_rect.centerx - total_button_width // 2

        # 重新開始按鈕
        restart_rect = pygame.Rect(start_x, btn_y, btn_width, btn_height)
        button_rects['restart'] = restart_rect
        pygame.draw.rect(screen, BUTTON_COLOR, restart_rect, border_radius=5)
        restart_text = font_small.render("重新開始", True, BUTTON_TEXT_COLOR)
        screen.blit(restart_text, restart_text.get_rect(center=restart_rect.center))

        # 暫停/恢復按鈕 (外觀/文字根據狀態改變)
        pause_rect = pygame.Rect(restart_rect.right + btn_padding, btn_y, btn_width, btn_height)
        button_rects['pause'] = pause_rect
        pause_text_str = "恢復" if game.game_state == GameState.PAUSED else "暫停"
        is_pause_active = game.game_state in [GameState.PLAYING, GameState.PAUSED]
        pause_btn_color = BUTTON_COLOR if is_pause_active else (160, 160, 160)  # 未啟用時變灰
        pause_text_color = BUTTON_TEXT_COLOR if is_pause_active else (210, 210, 210)
        pygame.draw.rect(screen, pause_btn_color, pause_rect, border_radius=5)
        pause_text = font_small.render(pause_text_str, True, pause_text_color)
        screen.blit(pause_text, pause_text.get_rect(center=pause_rect.center))

        # 儲存按鈕
        save_rect = pygame.Rect(pause_rect.right + btn_padding, btn_y, btn_width, btn_height)
        button_rects['save'] = save_rect
        pygame.draw.rect(screen, BUTTON_COLOR, save_rect, border_radius=5)
        save_text = font_small.render("儲存棋譜", True, BUTTON_TEXT_COLOR)
        screen.blit(save_text, save_text.get_rect(center=save_rect.center))

        # 載入按鈕
        load_rect = pygame.Rect(save_rect.right + btn_padding, btn_y, btn_width, btn_height)
        button_rects['load'] = load_rect
        pygame.draw.rect(screen, BUTTON_COLOR, load_rect, border_radius=5)
        load_text = font_small.render("載入棋譜", True, BUTTON_TEXT_COLOR)
        screen.blit(load_text, load_text.get_rect(center=load_rect.center))

    except Exception as e:
        print(f"繪製資訊面板時出錯: {e}")

    return button_rects  # 返回包含按鈕 Rect 對象的字典，用於事件處理


def draw_analysis_panel(screen, game, font_small, font_medium):
    """繪製右側的分析面板，用於分析模式控制和著法列表。"""
    buttons = {}  # 儲存導航按鈕 Rect 的字典: {'first': Rect, 'prev': Rect, ...}
    panel_rect = ANALYSIS_PANEL_RECT

    try:
        # 繪製面板背景
        pygame.draw.rect(screen, ANALYSIS_BG_COLOR, panel_rect)

        # 檢查字體是否已載入
        if not font_small or not font_medium:
            print("警告：分析面板所需字體未載入。")
            return buttons  # 返回空字典

        # --- 分析模式內容 ---
        if game.game_state == GameState.ANALYSIS:
            # 在分析模式內部定義佈局常數
            nav_button_area_top_padding = 15
            nav_button_area_height = 80  # 為導航按鈕分配的空間
            move_list_top_padding = 10
            list_bottom_padding = 10
            list_horizontal_padding = 10

            # 導航按鈕區域
            nav_button_area_rect = pygame.Rect(
                panel_rect.left,
                panel_rect.top + nav_button_area_top_padding,
                panel_rect.width,
                nav_button_area_height
            )

            # 著法列表區域
            move_list_area_rect = pygame.Rect(
                panel_rect.left,
                nav_button_area_rect.bottom + move_list_top_padding,
                panel_rect.width,
                panel_rect.height - nav_button_area_rect.bottom - move_list_top_padding - list_bottom_padding
            )

            # --- 繪製導航按鈕 ---
            btn_w, btn_h = 70, 30
            h_space, v_space = 10, 10
            total_nav_btn_width = btn_w * 2 + h_space  # 將 4 個按鈕塊在 nav_button_area_rect 內水平居中
            start_x = nav_button_area_rect.centerx - total_nav_btn_width // 2
            current_y = nav_button_area_rect.top  # 從區域頂部開始繪製按鈕

            # 按鈕第 1 行: 首步, 上一步
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

            current_y += btn_h + v_space  # 移動到下一行位置

            # 按鈕第 2 行: 下一步, 末步
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

            # --- 繪製著法列表 ---
            list_display_area = move_list_area_rect.inflate(-list_horizontal_padding * 2, -10)  # 實際可繪製區域
            line_height = font_small.get_linesize() + 2  # 在行之間添加一點垂直間距
            if line_height <= 0:
                print("警告：著法列表字體的行高無效。")
                return buttons

            max_lines_displayable = list_display_area.height // line_height
            if max_lines_displayable <= 0:
                return buttons  # 如果沒有空間則無法顯示

            if game.move_log:
                total_moves = len(game.move_log)
                current_view_step = game.analysis_step  # -1 代表第一步之前的狀態
                start_index = 0  # 列表窗口中顯示的第一個著法的索引 (0-based)

                # --- 滾動邏輯 ---
                if total_moves > max_lines_displayable:
                    target_view_pos = max(0, current_view_step)  # 嘗試保持當前選定的著法 (current_view_step) 可見，最好居中。
                    ideal_start = target_view_pos - (max_lines_displayable // 2)  # 計算使當前步驟居中的理想起始索引
                    max_start_index = total_moves - max_lines_displayable  # 將起始索引限制在 0 和最後可能的起始索引
                    start_index = max(0, min(ideal_start, max_start_index))


                # --- 渲染循環 ---
                for i in range(max_lines_displayable):
                    move_index = start_index + i  # game.move_log 中的實際索引
                    if move_index >= total_moves:
                        break  # 如果窗口中要顯示的著法已用完，則停止

                    move_data = game.move_log[move_index]
                    player = move_data.get('player')
                    r, c = move_data.get('row', -1), move_data.get('col', -1)
                    time_taken = move_data.get('time')
                    pause_time = move_data.get('pause', 0.0)

                    player_char = "黑" if player == BLACK else "白" if player == WHITE else "?"

                    # 將 (r, c) 轉換為標準棋盤表示法 (例如 A15, H8, T1)
                    col_char = chr(ord('A') + c) if 0 <= c < BOARD_SIZE else '?'
                    row_num = r + 1 if 0 <= r < BOARD_SIZE else '?'  # 從頂部 1 開始 (更常見)
                    coord_str = f"{col_char}{row_num}" if col_char != '?' and row_num != '?' else "(?)"
                    time_str = f"({time_taken:.1f}s)" if time_taken is not None else "(?)"
                    pause_str = f" [P:{pause_time:.1f}s]" if pause_time > 0.05 else ""  # 如果暫停時間顯著，則顯示

                    # 格式: "1. 黑H8 (5.2s)" 或 "12. 白T1 (10.0s) [P:3.1s]"
                    move_text = f"{move_index + 1}. {player_char}{coord_str} {time_str}{pause_str}"

                    is_current_step = (move_index == current_view_step)  # 決定文字顏色 (如果這是當前查看的步驟，則高亮)
                    text_color = MOVE_LIST_HIGHLIGHT_COLOR if is_current_step else INFO_TEXT_COLOR

                    move_surf = font_small.render(move_text, True, text_color)  # 渲染文字表面

                    # 如果文字對於顯示區域來說太寬，則截斷
                    max_width = list_display_area.width
                    if move_surf.get_width() > max_width:
                        original_width = move_surf.get_width()
                        try:  # 簡單的省略號截斷
                            chars_to_keep = max(1, int(len(move_text) * (max_width / original_width)) - 2)  # 根據寬度比例估算保留的字符數
                            truncated_text = move_text[:chars_to_keep] + ".."
                            move_surf = font_small.render(truncated_text, True, text_color)
                            if move_surf.get_width() > max_width:  # 再次檢查截斷後的寬度，雖然現在不太可能超標
                                move_surf = font_small.render("...", True, text_color)  # 如果計算有誤，使用省略號作為後備
                        except Exception as trunc_err:  # 捕獲截斷期間潛在的渲染錯誤
                            print(f"警告：截斷著法列表文本時出錯: {trunc_err}")
                            move_surf = font_small.render("...", True, text_color)  # 後備

                    text_y = list_display_area.top + i * line_height  # 計算 blit 文字表面的位置
                    screen.blit(move_surf, (list_display_area.left, text_y))

            else:  # 棋譜中沒有著法
                no_log_surf = font_small.render("無棋譜記錄", True, INFO_TEXT_COLOR)
                screen.blit(no_log_surf, no_log_surf.get_rect(center=list_display_area.center))

        # --- 非分析模式內容 (可選：顯示遊戲標題或留空) ---
        else:
            try:
                title_surf = font_medium.render("五子棋", True, INFO_TEXT_COLOR)  # 範例：在面板中央顯示遊戲標題
                title_rect = title_surf.get_rect(center=panel_rect.center)
                screen.blit(title_surf, title_rect)
            except Exception as e:
                print(f"渲染錯誤：分析面板佔位符內容 - {e}")

    except Exception as e:
        print(f"繪製分析面板時出錯: {e}")

    return buttons  # 返回導航按鈕 Rect 的字典 (即使為空)