# -*- coding: utf-8 -*-
import json
import os
import ast
from config import (BLACK, WHITE)

OPENING_BOOK_FILE = "opening_book.json"
SAVE_GAME_FILE = "renju_save.json"

# --- Opening Book I/O ---

def load_opening_book():
    """從 JSON 文件加載開局庫數據。"""
    default_book_data = { "((7, 7),)": [[7, 8], [6, 7], [6, 8]], } # JSON format
    mem_default_book = {} # In-memory format
    for k,v_lists in default_book_data.items(): mem_default_book[ast.literal_eval(k)]=[tuple(m) for m in v_lists]

    if os.path.exists(OPENING_BOOK_FILE):
        try:
            with open(OPENING_BOOK_FILE, 'r', encoding='utf-8') as f: data = json.load(f)
            book = {}
            for k_str, v_list_of_lists in data.items():
                try:
                    key_tuple = ast.literal_eval(k_str)
                    if isinstance(key_tuple, tuple) and \
                       all(isinstance(m, tuple) and len(m)==2 for m in key_tuple) and \
                       isinstance(v_list_of_lists, list) and \
                       all(isinstance(move, list) and len(move)==2 for move in v_list_of_lists):
                        book[key_tuple] = [tuple(move) for move in v_list_of_lists]
                    else: print(f"Warn: Invalid format in book. Key: {k_str}, Val: {v_list_of_lists}")
                except Exception as e: print(f"Warn: Error parsing key '{k_str}': {e}")
            print(f"Loaded {len(book)} entries (with move lists) from {OPENING_BOOK_FILE}")
            return book if book else mem_default_book
        except Exception as e:
            print(f"Error loading book: {e}. Using default.")
            return mem_default_book
    else:
        print(f"Book file '{OPENING_BOOK_FILE}' not found. Using default.");
        return mem_default_book

def save_opening_book_to_file(book_data):
     """將開局庫數據保存到 JSON 文件。"""
     try:
         serializable_book = {str(k): [list(move) for move in v_list] for k, v_list in book_data.items()}
         with open(OPENING_BOOK_FILE, 'w', encoding='utf-8') as f:
             json.dump(serializable_book, f, indent=4, ensure_ascii=False, sort_keys=True)
         print(f"Opening book saved to {OPENING_BOOK_FILE}")
     except Exception as e: print(f"Error saving opening book: {e}")

# --- 在模塊加載時執行加載，並將結果賦值給模塊級變量 ---
OPENING_BOOK = load_opening_book()
# --- 現在 OPENING_BOOK 可以在 game_io 模塊級別被導入 ---


# --- Game Save/Load ---

def save_game_data(move_log, player_types, filename=SAVE_GAME_FILE):
    """保存遊戲數據到文件。"""
    save_data = {
        "move_log": move_log,
        "player_black": player_types[BLACK],
        "player_white": player_types[WHITE]
    }
    try:
        with open(filename, 'w', encoding='utf-8') as f:
             json.dump(save_data, f, indent=4, ensure_ascii=False, sort_keys=True)
        print(f"Game data saved to {filename}")
        return True, f"棋譜已存檔至 {filename}"
    except Exception as e:
        print(f"Error saving game data to {filename}: {e}")
        return False, "存檔失敗!"

def load_game_data(filename=SAVE_GAME_FILE):
    """從文件加載遊戲數據。"""
    if not os.path.exists(filename):
        return None, None, f"找不到檔案: {filename}"
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            save_data = json.load(f)
        p_black = save_data.get("player_black", "human")
        p_white = save_data.get("player_white", "human")
        move_log = save_data.get("move_log", [])
        player_types = {BLACK: p_black, WHITE: p_white}
        return move_log, player_types, None
    except Exception as e:
        print(f"Error loading game data from {filename}: {e}")
        return None, None, "載入失敗!"