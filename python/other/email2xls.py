import pandas as pd

# 讀取 HTML 檔案
df = pd.read_html('/Users/alan/Desktop/email2.htm')  # 替換為你的 HTML 檔案路徑或網址

# 如果 HTML 包含多個表格，請選擇目標表格
table_index = 2  # 表格索引，根據實際情況進行調整
table = df[table_index]

# 寫入 Excel 檔案
output_file = 'output2.xlsx'  # 輸出的 Excel 檔案名稱
table.to_excel(output_file, index=False)

print('轉換完成')
