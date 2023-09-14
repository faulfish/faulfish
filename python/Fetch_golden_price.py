import requests
from bs4 import BeautifulSoup
import re
import pandas as pd

# 檔案名稱和路徑
file_name = 'Excel/data.xlsx'

url = 'https://rate.bot.com.tw/gold?Lang=zh-TW'
response = requests.get(url)
html = response.text
soup = BeautifulSoup(html, 'html.parser')

# 找到掛牌時間
time_div = soup.find('div', class_='pull-left trailer text-info')
time_text = time_div.text.strip().split('：')[1].strip()
print(f'掛牌時間：{time_text}')

# 找到黃金價格資料表格
pattern = re.compile('黃金牌價')
table = soup.find('table', {'title': pattern})
if table is None:
    print('找不到符合條件的表格')
else:
    # 定義要找的資料標題
    titles = ['買進', '賣出']
    data_values = []

    for title in titles:
        pattern = re.compile(title)
        data_row = table.find('td', string=pattern)
        if data_row is None:
            print('找不到符合條件的資料')
            print(table)
        else:
            next_td = data_row.find_next('td')
            value = next_td.get_text(strip=True)
            data_values.append(value)
            print(f'{title}: {value}')

    # 讀取 Excel 檔案
    try:
        existing_df = pd.read_excel(file_name, sheet_name="gold_prices")
    except FileNotFoundError:
        existing_df = pd.DataFrame(columns=['掛牌時間', '買進', '賣出'])

    # 檢查掛牌時間是否已存在
    if time_text in existing_df['掛牌時間'].values:
        print('該筆資料已存在')
    else:
        # 新增一筆資料
        new_row = {'掛牌時間': time_text, '買進': data_values[0], '賣出': data_values[1]}
        df = pd.concat([existing_df, pd.DataFrame([new_row])], ignore_index=True)


        # 儲存更新後的檔案
        df.to_excel(file_name, sheet_name="gold_prices", index=False)
        print('資料已成功寫入 Excel 檔案')
