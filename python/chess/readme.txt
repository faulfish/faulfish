Python 象棋專案並提供安裝說明。

專案總結
這是一個使用 Python 和 Pygame 函式庫開發的圖形化中國象棋 (Xiangqi) 遊戲。它提供了以下主要功能：
圖形化介面: 使用 Pygame 繪製美觀的象棋棋盤、棋子以及用戶界面元素。

基本規則實現:
實現了所有棋子（帥/將、仕/士、相/象、傌/馬、俥/車、炮/砲、兵/卒）的標準移動規則。
包含過河限制（象、兵/卒）和九宮限制（帥/將、仕/士）。
實現了「絆馬腳」和「炮翻山」的規則。
檢測「將軍」(Check) 狀態。
判斷「將死」(Checkmate) 和「欠行」(Stalemate) 的遊戲結束條件。
實現了「王不見王」的規則。

雙人對弈: 支持兩位玩家在同一台電腦上輪流走子。

計時器: 為紅黑雙方提供獨立的倒數計時器，超時會判負。

狀態顯示: 在界面上顯示當前回合方、計時器以及遊戲狀態（如將軍、將死、和棋、超時等）。

棋譜儲存/載入:
可以將當前對局的完整行棋步驟 (Move Log) 儲存為 JSON 格式的文件。
可以載入之前儲存的 JSON 棋譜文件。

分析模式:
載入棋譜後會進入分析模式。
在右側面板顯示當前分析的步數、走法記錄和思考時間。
提供按鈕（或鍵盤快捷鍵 ← → Home End）來導航棋譜，查看任意一步的局面。
UI 佈局: 採用棋盤在左、分析信息/控制在右側面板的佈局，遊戲信息（計時器、狀態、存檔按鈕）則在非分析模式下顯示於棋盤下方。
字體處理: 嘗試載入指定的 Noto Sans SC 字體以獲得最佳視覺效果，並提供了系統備選字體機制以提高兼容性。
總之，這是一個功能相對完整的本地雙人象棋應用，包含了對弈、儲存和覆盤分析的核心功能。

安裝與執行方式
要執行此專案，您需要安裝 Python 和 Pygame 函式庫，並確保字體文件位置正確。

步驟：
安裝 Python 3:
如果您尚未安裝 Python，請前往 Python 官方網站 (https://www.python.org/downloads/) 下載並安裝最新穩定版的 Python 3 (建議 3.7 或更高版本)。
安裝時，請確保勾選 "Add Python to PATH" (或類似選項)，以便在命令提示字元/終端機中直接使用 python 和 pip 命令。

安裝 Pygame:
打開您的命令提示字元 (Windows) 或終端機 (macOS/Linux)。
執行以下命令來安裝 Pygame 函式庫：
pip install pygame
Use code with caution.
Bash
如果您使用虛擬環境 (如 venv)，請先啟用虛擬環境再執行 pip install pygame。

取得程式碼:
將上面提供的完整 Python 程式碼複製並儲存為一個 .py 文件（例如，xiangqi_game.py）。
取得字體文件 (重要):
程式碼預設需要 Noto Sans SC 字體才能正確顯示棋子上的中文文字。
您需要下載 Noto Sans SC Variable 字體文件 (NotoSansSC-VariableFont_wght.ttf)。可以從 Google Fonts 或其他可信來源下載。
在與您的 Python 腳本 (xiangqi_game.py) 相同的目錄下，創建一個名為 Noto Sans SC 的資料夾。
將下載的 NotoSansSC-VariableFont_wght.ttf 文件放入這個 Noto Sans SC 資料夾中。
目錄結構應如下：
your_project_folder/
├── xiangqi_game.py
└── Noto Sans SC/
    └── NotoSansSC-VariableFont_wght.ttf
Use code with caution.
如果找不到此字體，程式會嘗試使用系統備選字體（如 黑體、雅黑等），但棋子顯示效果可能不如預期。

執行遊戲:
打開命令提示字元或終端機。
使用 cd 命令進入您儲存 xiangqi_game.py 和 Noto Sans SC 資料夾的那個目錄。例如：
cd /path/to/your_project_folder/
Use code with caution.
Bash

執行以下命令來啟動遊戲：
python xiangqi_game.py
Use code with caution.
Bash
現在，您應該能看到象棋遊戲視窗並開始遊戲了。如果遇到 FileNotFoundError 或字體相關的警告/錯誤，請再次檢查步驟 4 中的字體文件夾名稱和文件位置是否完全正確。