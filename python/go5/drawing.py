# -*- coding: utf-8 -*-
import pygame
from config import (BOARD_SIZE, SQUARE_SIZE, MARGIN, GRID_WIDTH, GRID_HEIGHT,
                    INFO_HEIGHT, ANALYSIS_WIDTH, BOARD_AREA_WIDTH, BOARD_AREA_HEIGHT,
                    WIDTH, HEIGHT, BOARD_COLOR, LINE_COLOR, BLACK_STONE, WHITE_STONE,
                    INFO_BG_COLOR, ANALYSIS_BG_COLOR, INFO_TEXT_COLOR, HIGHLIGHT_COLOR,
                    HOVER_BLACK_COLOR, HOVER_WHITE_COLOR, BUTTON_COLOR, BUTTON_TEXT_COLOR,
                    MOVE_LIST_HIGHLIGHT_COLOR, EMPTY, BLACK, WHITE, GameState,
                    INFO_PANEL_RECT, ANALYSIS_PANEL_RECT)
from utils import format_time

def draw_grid(screen):
    """繪製 Renju 棋盤格線和星位點。"""
    try:
        # 繪製棋盤區域背景色
        # 注意: 全螢幕背景通常在主迴圈的繪圖開始時填充
        # 但這裡繪製棋盤區域的背景可確保格線繪製在正確背景上
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
        star_points_rc = [(3, 3), (3, 11), (11, 3), (11, 11), (7, 7)] # (row, col) 索引
        star_radius = 5
        for r, c in star_points_rc:
            center_x = MARGIN + c * SQUARE_SIZE
            center_y = MARGIN + r * SQUARE_SIZE
            pygame.draw.circle(screen, LINE_COLOR, (center_x, center_y), star_radius)
    except Exception as e:
        print(f"繪製格線時出錯: {e}")


def draw_stones(screen, board, last_move, game_state):
    """繪製棋盤上目前的棋子。如果遊戲暫停則跳過繪製。"""
    try:
        stone_radius = SQUARE_SIZE // 2 - 3 # 留下與格線的小間隙
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                player = board[r][c]
                if player != EMPTY:
                    center_x = MARGIN + c * SQUARE_SIZE
                    center_y = MARGIN + r * SQUARE_SIZE
                    stone_color = BLACK_STONE if player == BLACK else WHITE_STONE
                    pygame.draw.circle(screen, stone_color, (center_x, center_y), stone_radius)

        # 高亮標示最後一步棋 (僅在非暫停狀態下繪製，因為暫停時會提前返回)
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

def draw_live_threes(screen, live_three_positions):
    """在棋盘上标记活三的位置。"""
    try:
        mark_radius = SQUARE_SIZE // 4
        for r, c, player in live_three_positions:
            center_x = MARGIN + c * SQUARE_SIZE
            center_y = MARGIN + r * SQUARE_SIZE
            mark_color = (255, 0, 0)  # 红色
            pygame.draw.circle(screen, mark_color, (center_x, center_y), mark_radius, 2)  # 繪製空心圓
            # print(f"繪製活三標記: ({r}, {c}), 顏色: {mark_color}, 圓心: ({center_x}, {center_y})")  # Log
    except Exception as e:
        print(f"繪製活三標記時出錯: {e}")
        
def draw_jump_live_threes(screen, jump_live_three_positions):
    """在棋盘上标记跳活三的位置。"""
    try:
        mark_radius = SQUARE_SIZE // 4
        for r, c, player in jump_live_three_positions:
            center_x = MARGIN + c * SQUARE_SIZE
            center_y = MARGIN + r * SQUARE_SIZE
            mark_color = (0, 0, 255)  # 蓝色
            pygame.draw.circle(screen, mark_color, (center_x - mark_radius, center_y - mark_radius, mark_radius * 2, mark_radius * 2), 2)  # 繪製空心正方形
            print(f"繪製跳活三標記: ({r}, {c}), 顏色: {mark_color}, 中心: ({center_x - mark_radius}, {center_y - mark_radius}), 尺寸: {mark_radius * 2}")  # Log
    except Exception as e:
        print(f"繪製跳活三標記時出錯: {e}")

def draw_live_fours(screen, live_four_positions):
    """在棋盘上标记活四的位置。"""
    try:
        mark_radius = SQUARE_SIZE // 4
        for r, c, player in live_four_positions:
            center_x = MARGIN + c * SQUARE_SIZE
            center_y = MARGIN + r * SQUARE_SIZE
            mark_color = (255, 0, 0)  # 红色
            pygame.draw.rect(screen, mark_color, (center_x, center_y), mark_radius, 2)  # 繪製空心圓
            # print(f"繪製活三標記: ({r}, {c}), 顏色: {mark_color}, 圓心: ({center_x}, {center_y})")  # Log
    except Exception as e:
        print(f"繪製活三標記時出錯: {e}")

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
        return # 沒有懸停位置

    try:
        r, c = hover_pos
        # 檢查該位置在 *傳入的* 棋盤上是否有效且為空
        # (可能是 game.board 或 game.analysis_board)
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
    # 動態定義按鈕尺寸和位置
    panel_rect = INFO_PANEL_RECT
    left_padding = 15
    right_padding = panel_rect.width - 15 # 相對於面板寬度
    timer_y = panel_rect.top + 8
    btn_height = 28
    btn_width = 75
    btn_padding = 8
    btn_y = panel_rect.bottom - btn_height - 8 # 將按鈕放置在面板底部附近

    button_area_top_y = btn_y - 4 # 估計按鈕區域的頂部邊緣，用於狀態訊息垂直居中

    # 初始化返回值 (儲存按鈕的 Rect 對象)
    button_rects = {'restart': None, 'pause': None, 'save': None, 'load': None}

    try:
        # 繪製面板背景
        pygame.draw.rect(screen, INFO_BG_COLOR, panel_rect)

        # 檢查字體是否已載入
        if not font_small or not font_medium:
            print("警告：資訊面板所需字體未載入。")
            # 可選擇在字體載入失敗時繪製基本文字
            return button_rects # 如果字體載入失敗，返回空的 Rect 字典

        timer_line_height = font_small.get_height()
        status_line_height = font_medium.get_height()

        # 計算狀態訊息的 Y 位置 (嘗試垂直居中)
        # 在計時器底部和按鈕頂部之間居中
        status_y = timer_y + (button_area_top_y - timer_y) // 2 - status_line_height // 2
        # 確保狀態訊息在計時器下方
        # status_y = max(status_y, timer_y + timer_line_height + 4)
        status_y = timer_y


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
            # 使用 game 物件中的 status_message
            status_surf = font_medium.render(game.status_message, True, INFO_TEXT_COLOR)
            # 在資訊面板內水平居中狀態訊息
            status_rect = status_surf.get_rect(centerx=panel_rect.centerx, y=status_y)
            screen.blit(status_surf, status_rect)
        except Exception as e:
            print(f"渲染錯誤：狀態訊息 - {e}")

        # --- 繪製按鈕 ---
        total_button_width = btn_width * 4 + btn_padding * 3
        start_x = panel_rect.centerx - total_button_width // 2

        # 重新開始按鈕
        try:
            restart_rect = pygame.Rect(start_x, btn_y, btn_width, btn_height)
            button_rects['restart'] = restart_rect
            pygame.draw.rect(screen, BUTTON_COLOR, restart_rect, border_radius=5)
            restart_text = font_small.render("重新開始", True, BUTTON_TEXT_COLOR)
            screen.blit(restart_text, restart_text.get_rect(center=restart_rect.center))
        except Exception as e: print(f"渲染錯誤：重新開始按鈕 - {e}")

        # 暫停/恢復按鈕 (外觀/文字根據狀態改變)
        try:
            # restart_rect 需要先成功創建
            pause_rect = pygame.Rect(restart_rect.right + btn_padding, btn_y, btn_width, btn_height)
            button_rects['pause'] = pause_rect
            pause_text_str = "恢復" if game.game_state == GameState.PAUSED else "暫停"
            # 按鈕僅在遊戲進行中或暫停時啟用
            is_pause_active = game.game_state in [GameState.PLAYING, GameState.PAUSED]
            pause_btn_color = BUTTON_COLOR if is_pause_active else (160, 160, 160) # 未啟用時變灰
            pause_text_color = BUTTON_TEXT_COLOR if is_pause_active else (210, 210, 210)
            pygame.draw.rect(screen, pause_btn_color, pause_rect, border_radius=5)
            pause_text = font_small.render(pause_text_str, True, pause_text_color)
            screen.blit(pause_text, pause_text.get_rect(center=pause_rect.center))
        except Exception as e: print(f"渲染錯誤：暫停按鈕 - {e}")

        # 儲存按鈕
        try:
            # pause_rect 需要先成功創建
            save_rect = pygame.Rect(pause_rect.right + btn_padding, btn_y, btn_width, btn_height)
            button_rects['save'] = save_rect
            pygame.draw.rect(screen, BUTTON_COLOR, save_rect, border_radius=5)
            save_text = font_small.render("儲存棋譜", True, BUTTON_TEXT_COLOR)
            screen.blit(save_text, save_text.get_rect(center=save_rect.center))
        except Exception as e: print(f"渲染錯誤：儲存按鈕 - {e}")

        # 載入按鈕
        try:
            # save_rect 需要先成功創建
            load_rect = pygame.Rect(save_rect.right + btn_padding, btn_y, btn_width, btn_height)
            button_rects['load'] = load_rect
            pygame.draw.rect(screen, BUTTON_COLOR, load_rect, border_radius=5)
            load_text = font_small.render("載入棋譜", True, BUTTON_TEXT_COLOR)
            screen.blit(load_text, load_text.get_rect(center=load_rect.center))
        except Exception as e: print(f"渲染錯誤：載入按鈕 - {e}")

    except Exception as e:
        print(f"繪製資訊面板時出錯: {e}")

    # 返回包含按鈕 Rect 對象的字典，用於事件處理
    return button_rects


def draw_analysis_panel(screen, game, font_small, font_medium):
    """繪製右側的分析面板，用於分析模式控制和著法列表。"""
    panel_rect = ANALYSIS_PANEL_RECT
    # 儲存導航按鈕 Rect 的字典: {'first': Rect, 'prev': Rect, ...}
    buttons = {}

    try:
        # 繪製面板背景
        pygame.draw.rect(screen, ANALYSIS_BG_COLOR, panel_rect)

        # 檢查字體是否已載入
        if not font_small or not font_medium:
            print("警告：分析面板所需字體未載入。")
            return buttons # 返回空字典

        # --- 分析模式內容 ---
        if game.game_state == GameState.ANALYSIS:
            # 在分析模式內部定義佈局常數
            nav_button_area_top_padding = 15
            nav_button_area_height = 80 # 為導航按鈕分配的空間
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
            # 將 4 個按鈕塊在 nav_button_area_rect 內水平居中
            total_nav_btn_width = btn_w * 2 + h_space
            start_x = nav_button_area_rect.centerx - total_nav_btn_width // 2
            current_y = nav_button_area_rect.top # 從區域頂部開始繪製按鈕

            # 按鈕第 1 行: 首步, 上一步
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
            except Exception as e: print(f"渲染錯誤：分析導航第 1 行 - {e}")

            current_y += btn_h + v_space # 移動到下一行位置

            # 按鈕第 2 行: 下一步, 末步
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
            except Exception as e: print(f"渲染錯誤：分析導航第 2 行 - {e}")


            # --- 繪製著法列表 ---
            # 定義內邊距內的實際可繪製區域
            list_display_area = move_list_area_rect.inflate(-list_horizontal_padding * 2, -10) # 略微縮小尺寸以留出邊距

            try:
                line_height = font_small.get_linesize() + 2 # 在行之間添加一點垂直間距
                if line_height <= 0: # 如果字體大小奇怪，避免除以零
                    print("警告：著法列表字體的行高無效。")
                    return buttons

                max_lines_displayable = list_display_area.height // line_height
                if max_lines_displayable <= 0:
                     # print("警告：沒有足夠的空間顯示著法列表。") # 可選警告
                    return buttons # 如果沒有空間則無法顯示

                if game.move_log:
                    total_moves = len(game.move_log)
                     # -1 代表第一步之前的狀態
                    current_view_step = game.analysis_step
                    # 列表窗口中顯示的第一個著法的索引 (0-based)
                    start_index = 0

                    # --- 滾動邏輯 ---
                    # 嘗試保持當前選定的著法 (current_view_step) 可見，最好居中。
                    if total_moves > max_lines_displayable:
                        # 計算使當前步驟居中的理想起始索引
                        # 如果 current_view_step 為 -1，居中應將第 1 步顯示在頂部或靠近頂部。
                        # 將 -1 視為目標是顯示第 0 步。
                        target_view_pos = max(0, current_view_step)
                        ideal_start = target_view_pos - (max_lines_displayable // 2)

                        # 將起始索引限制在 0 和最後可能的起始索引
                        max_start_index = total_moves - max_lines_displayable
                        start_index = max(0, min(ideal_start, max_start_index))


                    # --- 渲染循環 ---
                    for i in range(max_lines_displayable):
                        # game.move_log 中的實際索引
                        move_index = start_index + i
                        if move_index >= total_moves:
                            break # 如果窗口中要顯示的著法已用完，則停止

                        move_data = game.move_log[move_index]
                        player = move_data.get('player')
                        r, c = move_data.get('row', -1), move_data.get('col', -1)
                        time_taken = move_data.get('time')
                        pause_time = move_data.get('pause', 0.0)

                        player_char = "黑" if player == BLACK else "白" if player == WHITE else "?"

                        # 將 (r, c) 轉換為標準棋盤表示法 (例如 A15, H8, T1)
                        # 列: A-T (跳過 I 很常見，但這裡可能不需要), 行: 1-15 (棋盤頂部為 1)
                        col_char = chr(ord('A') + c) if 0 <= c < BOARD_SIZE else '?'
                        # row_num = BOARD_SIZE - r if 0 <= r < BOARD_SIZE else '?' # 從底部 1 開始
                        row_num = r + 1 if 0 <= r < BOARD_SIZE else '?' # 從頂部 1 開始 (更常見)

                        coord_str = f"{col_char}{row_num}" if col_char != '?' and row_num != '?' else "(?)"

                        time_str = f"({time_taken:.1f}s)" if time_taken is not None else "(?)"
                        # 如果暫停時間顯著，則顯示
                        pause_str = f" [P:{pause_time:.1f}s]" if pause_time > 0.05 else ""

                        # 格式: "1. 黑H8 (5.2s)" 或 "12. 白T1 (10.0s) [P:3.1s]"
                        move_text = f"{move_index + 1}. {player_char}{coord_str} {time_str}{pause_str}"

                        # 決定文字顏色 (如果這是當前查看的步驟，則高亮)
                        is_current_step = (move_index == current_view_step)
                        text_color = MOVE_LIST_HIGHLIGHT_COLOR if is_current_step else INFO_TEXT_COLOR

                        # 渲染文字表面
                        move_surf = font_small.render(move_text, True, text_color)

                        # 如果文字對於顯示區域來說太寬，則截斷
                        max_width = list_display_area.width
                        if move_surf.get_width() > max_width:
                             # 簡單的省略號截斷
                             original_width = move_surf.get_width()
                             try:
                                 # 根據寬度比例估算保留的字符數
                                 # -2 作為 ".." 的安全邊際
                                 chars_to_keep = max(1, int(len(move_text) * (max_width / original_width)) - 2)
                                 truncated_text = move_text[:chars_to_keep] + ".."
                                 move_surf = font_small.render(truncated_text, True, text_color)
                                 # 再次檢查截斷後的寬度，雖然現在不太可能超標
                                 if move_surf.get_width() > max_width:
                                     # 如果計算有誤，使用省略號作為後備
                                     move_surf = font_small.render("...", True, text_color)
                             except Exception as trunc_err: # 捕獲截斷期間潛在的渲染錯誤
                                 print(f"警告：截斷著法列表文本時出錯: {trunc_err}")
                                 move_surf = font_small.render("...", True, text_color) # 後備

                        # 計算 blit 文字表面的位置
                        text_y = list_display_area.top + i * line_height
                        screen.blit(move_surf, (list_display_area.left, text_y))

                else: # 棋譜中沒有著法
                    no_log_surf = font_small.render("無棋譜記錄", True, INFO_TEXT_COLOR)
                    screen.blit(no_log_surf, no_log_surf.get_rect(center=list_display_area.center))

            except Exception as e:
                print(f"渲染著法列表時出錯: {e}")

        # --- 非分析模式內容 (可選：顯示遊戲標題或留空) ---
        try:
            # 範例：在面板中央顯示遊戲標題
            title_surf = font_medium.render("五子棋", True, INFO_TEXT_COLOR)
            title_rect = title_surf.get_rect(center=panel_rect.center)
            screen.blit(title_surf, title_rect)
        except Exception as e:
            print(f"渲染錯誤：分析面板佔位符內容 - {e}")

    except Exception as e:
        print(f"繪製分析面板時出錯: {e}")

    # 返回導航按鈕 Rect 的字典 (即使為空)
    return buttons