import pandas as pd
from openpyxl import Workbook

# 讀取Excel文件
df = pd.read_excel('PAD Report.xlsx')

# 選擇要統計的欄位
column_to_count = 'Owner'  # 修改為你要統計的欄位名稱

# 計算每個項目出現的次數
counts = df[column_to_count].value_counts().reset_index()
counts.columns = ['項目', '出現次數']

# 建立新的Excel工作簿
wb = Workbook()
ws = wb.active

# 將統計結果寫入新的工作表
ws.append(counts.columns.tolist())  # 寫入欄位名稱
for row in counts.itertuples(index=False):
    ws.append(row)

# 儲存Excel文件
wb.save('result.xlsx')
