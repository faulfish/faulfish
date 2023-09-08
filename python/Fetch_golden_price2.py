import requests
from bs4 import BeautifulSoup
import re

url = 'https://rate.bot.com.tw/gold?Lang=zh-TW'

response = requests.get(url)
html = response.text

soup = BeautifulSoup(html, 'html.parser')

# 使用正則表達式模式尋找包含「賣出」或「買進」的表達式
pattern = re.compile('賣出|買進')

# 尋找包含'本行賣出'的 <td> 元素所在的 <table>
tables = soup.find_all(lambda tag: tag.name == 'table' and tag.find('td', string=pattern) is not None)

if len(tables) == 0:
    print('找不到符合條件的表格')
else:
    for table in tables:
        # print(table)
        # 獲取找到的 <table> 的 title
        title = table.get('title')
        if title is None:
            print('找不到表格的 title')
        else:
            print('表格的 title:', title)

        # 找到符合條件的 <td> 元素及其上一個和下一個 <td> 元素
        td_elements = table.find_all('td', string=pattern)
        for td in td_elements:
            prev_td = td.find_previous('td')
            next_td = td.find_next('td')
            if prev_td is not None and next_td is not None and prev_td.text.strip() not in ['', '-'] and next_td.text.strip() not in ['', '-']:
                print('符合條件的 <td> 元素:', td.get_text(strip=True))
                print('上一個 <td> 元素:', prev_td.get_text(strip=True))
                print('下一個 <td> 元素:', next_td.get_text(strip=True))
            # else:
                # print('找不到符合條件的相鄰 <td> 元素')

# 這段程式碼的作用是從指定的網址上獲取 HTML 內容，然後使用 BeautifulSoup 解析 HTML，找出符合特定條件的表格和表格內的資料。

# 程式碼的執行流程如下：

# 使用 requests 模組向指定的 URL 發送 GET 請求，獲取網頁的 HTML 內容。
# 使用 BeautifulSoup 將 HTML 內容轉換為可解析的物件。
# 使用正則表達式模式 pattern 尋找包含「賣出」或「買進」的表達式。
# 使用 find_all() 方法找出所有符合條件的 <table> 元素。
# 如果找到的表格數量為零，則輸出訊息表示找不到符合條件的表格；否則，進行後續處理。
# 對於每個找到的表格，首先獲取其 title 屬性，並輸出表格的標題。
# 使用 find_all() 方法找出符合條件的 <td> 元素。
# 對於每個找到的 <td> 元素，使用 find_previous() 和 find_next() 方法找到其上一個和下一個 <td> 元素。
# 如果上一個和下一個 <td> 元素都存在且它們的內容不是空值或 '-' 符號，則輸出相應的資訊，包括符合條件的 <td> 元素、上一個 <td> 元素和下一個 <td> 元素。
# 如果上一個或下一個 <td> 元素是空值或 '-' 符號，則不輸出資訊。
# 這段程式碼主要用於從指定網址的 HTML 中提取出特定表格的資料，並按照特定條件進行篩選和輸出。