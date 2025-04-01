Python 象棋遊戲 - 功能總結

這個程式提供了一個功能相對完善的象棋遊戲體驗，包含以下主要特點：

基本象棋規則：
實現了所有棋子（帥/將、仕/士、相/象、俥/車、傌/馬、炮/砲、兵/卒）的標準移動和吃子規則。
包含特殊規則：象/相不能過河、兵/卒過河後才能橫走、馬/傌會被蹩腿（卡腳）、炮/砲需要隔一個棋子才能吃子。
正確的九宮格移動限制（帥/將、仕/士）。
將軍（Check）檢測。
將死（Checkmate）和欠行（Stalemate / 逼和）判定。
將帥不可直接照面規則。

圖形化使用者介面 (GUI)：
使用 Pygame 函式庫建立圖形介面。
繪製標準的 9x10 象棋棋盤，包含楚河漢界、九宮格線、兵/卒和炮/砲的起始點標記。
使用中文字符顯示棋子，並區分紅黑雙方顏色。
棋子選中時有高亮提示，可走位置有標記提示。

遊戲流程控制：
輪流走棋機制。
下方資訊面板顯示當前回合方、將軍狀態、計時器、遊戲結果（將死、欠行、超時）。
點擊棋子選取，再次點擊合法位置移動。

計時器：
為紅黑雙方提供獨立的倒數計時器。
超時會判定對方獲勝。

棋譜儲存與載入：
可以將當前對局的完整移動步驟（包含用時）儲存到 JSON 格式的檔案 (xiangqi_save.json)。
可以從 JSON 檔案載入棋譜，進入「分析模式」。

分析模式：
載入棋譜後自動進入。
右側面板顯示棋譜列表，包含步數、走子方、標準中文記譜法（如：炮二平五）以及該步的思考時間。
當前檢視的棋步在列表中會高亮顯示。
右側面板頂部提供「首步」、「上一步」、「下一步」、「末步」按鈕，方便檢視棋局過程。
棋盤會同步顯示所選棋步的局面。
列表會自動滾動以嘗試將當前棋步保持在可見範圍內。

新對局功能：
下方資訊面板始終提供「新對局」按鈕，點擊後可立即重設棋盤，開始一盤新棋。
字體支援：
優先使用指定的 Noto Sans SC 字體以獲得最佳顯示效果。
若找不到指定字體，會嘗試使用系統中的備選字體（如 SimHei, Microsoft YaHei 等），但顯示效果可能不同。
包含字體載入的錯誤處理和提示。
安裝與執行說明

要執行這個象棋遊戲，您需要：
安裝 Python 3：
如果您的電腦尚未安裝 Python 3（建議 3.7 或更新版本），請前往 Python 官方網站 (https://www.python.org/downloads/) 下載並安裝適合您作業系統的版本。
安裝時，建議勾選 "Add Python to PATH"（將 Python 加入環境變數）選項，這樣後續在終端機執行指令會比較方便。
取得遊戲程式碼：
將上面提供的完整 Python 程式碼複製並儲存為一個 .py 檔案，例如命名為 xiangqi_game.py。
安裝 Pygame 函式庫：
開啟您的終端機（Terminal）或命令提示字元（Command Prompt）。
Windows：搜尋 "cmd" 或 "PowerShell"。
macOS：搜尋 "Terminal"。
Linux：通常是 Ctrl+Alt+T 或在應用程式選單中尋找。
在終端機中輸入以下指令並按 Enter 執行，以安裝 Pygame：
pip install pygame
Use code with caution.
Bash
如果您同時安裝了 Python 2 和 Python 3，可能需要使用 pip3：
pip3 install pygame
Use code with caution.
Bash
等待安裝完成。

下載並放置字體檔案（強烈建議）：
為了獲得最佳的中文棋子顯示效果，程式碼預設會尋找 NotoSansSC-VariableFont_wght.ttf 字體。
您可以前往 Google Fonts (https://fonts.google.com/noto/specimen/Noto+Sans+SC) 或其他可靠來源下載 Noto Sans SC (思源黑體 SC) 字體。通常下載後會是一個 ZIP 檔案，解壓縮後找到 Variable Font 或類似名稱資料夾下的 NotoSansSC-VariableFont_wght.ttf 檔案。
關鍵步驟： 在您儲存 xiangqi_game.py 檔案的相同目錄下，建立一個名為 Noto Sans SC 的新資料夾。
將下載的 NotoSansSC-VariableFont_wght.ttf 字體檔案放入這個 Noto Sans SC 資料夾內。
最終的目錄結構應如下所示：
your_game_directory/
├── xiangqi_game.py
└── Noto Sans SC/
    └── NotoSansSC-VariableFont_wght.ttf
Use code with caution.

備註： 如果您不放置此字體，程式會嘗試使用系統中的備選字體（如 SimHei, Microsoft YaHei 等），但棋子的顯示樣式可能不如預期。

執行遊戲：
開啟終端機（或命令提示字元）。
使用 cd 指令切換到您儲存 xiangqi_game.py 檔案的目錄。例如：
cd path/to/your_game_directory
Use code with caution.
Bash
(請將 path/to/your_game_directory 替換為實際路徑)
輸入以下指令執行遊戲：
python xiangqi_game.py
Use code with caution.
Bash
或者，如果需要指定 Python 3：
python3 xiangqi_game.py
Use code with caution.
Bash
如果一切順利，象棋遊戲的視窗應該會出現。
現在您可以開始享受這個 Python 象棋遊戲了！