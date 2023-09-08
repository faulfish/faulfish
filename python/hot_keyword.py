import os
import sys
import time
import re
from datetime import datetime
from bs4 import BeautifulSoup
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from openpyxl import load_workbook
from openpyxl.utils import get_column_letter
from chatgpt import chatgpt

# 使用Selenium開啟瀏覽器並自動登入//chromedriver//Google Chrome for Testing.app
# driver = webdriver.Chrome(service=Service('/usr/local/bin/chromedriver' ) )
chrome_driver_path = '/usr/local/bin/chromedriver'
driver = webdriver.Chrome(executable_path=chrome_driver_path)

# 引入 ANSI Escape Sequences 的顏色代碼
DARK_GREEN = '\033[31m'  # 红色
LIGHT_GREEN = '\033[92m'  # 绿色
RESET = '\033[0m'

def count_characters(text, max_length):
    chinese_count  = len(re.findall(r'[\u4e00-\u9fff]', text))
    japanese_count = len(re.findall(r'[\u3040-\u30FF]', text))
    korean_count   = len(re.findall(r'[\uAC00-\uD7AF]', text))
    english_count  = len(text) - chinese_count - japanese_count - korean_count
    orgASCSpace    = chinese_count * 2 + japanese_count * 2 + korean_count * 2 + english_count
    space_padding_count = max_length - orgASCSpace
    padding = ' ' * space_padding_count  # 使用半形空白字元
    return padding

def print_keywords(keywords):
    # 列印熱門關鍵字及相關資訊, 顯示每個變數的長度
    for index, (rank, keyword, query_count, detail) in enumerate(keywords):
        keyword_padding     = count_characters(keyword, 24);    # 使用半形空白字元
        query_count_padding = count_characters(query_count, 12); # 使用半形空白字元
        detail_padding      = count_characters(query_count, 20); # 使用半形空白字元

        # 交替顯示深綠色和淺綠色的行
        if int(index) % 2 == 0:
            print(DARK_GREEN  + f"{rank:<3}, {keyword}{keyword_padding}, {query_count}{query_count_padding}, {detail}{detail_padding}" + RESET)
        else:
            print(LIGHT_GREEN + f"{rank:<3}, {keyword}{keyword_padding}, {query_count}{query_count_padding}, {detail}{detail_padding}" + RESET)

def get_google_hot_keywords(geo="TW"):
    url = f"https://trends.google.com/trends/trendingsearches/daily?geo={geo}&hl=en-US" # 使用參數動態設定地理位置
    print(f"URL: {url}")
    driver.get(url)
    time.sleep(1)  # 等待網頁載入完全
    soup = BeautifulSoup(driver.page_source, "html.parser")
    keyword_elements = soup.find_all("div", class_="details")

    hot_keywords = []
    for element in keyword_elements:
        rank_element = element.find_previous_sibling("div", class_="index")
        rank = rank_element.text.strip() if rank_element else "N/A"

        keyword_element = element.find("div", class_="title")
        keyword = keyword_element.text.strip() if keyword_element else "N/A"
        keyword = keyword.strip()

        query_count_element = element.find("div", class_="details-bottom")
        query_count = query_count_element.text.strip() if query_count_element else "N/A"# 使用正則表達式提取 (5K+) searches 部分

        lines = query_count.strip().split("\n")
        filtered_lines = [line.strip() for line in lines if line.strip()]
        filtered_content = "\n".join(filtered_lines[:5])
        query_count = filtered_lines[4]
        query_count = query_count.strip()
        match = re.search(r"(\d+[A-Z]?\+?)", query_count)
        query_count = match.group(1) if match else "N/A"
        query_count_length = len(query_count)
        query_count_padding = ' ' * (5 - query_count_length)  # 使用半形空白字元
        query_count = query_count + query_count_padding + filtered_lines[3][:10]

        # Sample content and assistant messages
        content = "Please identify the category of the following content:"

        # Generate summary using ChatGPT API
        summary = chatgpt(filtered_lines[0][:50], content)
        org     = filtered_lines[0][:50];

        # List of categories to check for in the summary
        categories_to_bypass = ["scholarships", "career", "education", "entertainment", "sports", "politics", "food", "dining", "travel", "gossip", "pornography", "gaming", "games", "game", "social media", "promotion", "actor", "article", "animal", "general information", "domestic", "violence", "personal", "Celebrity", "TV show", "movie", "opinion", "current", "apologize", "抱歉", "sorry"]

        categories_to_keep   = ["AI", "Artificial", "biotech", "Finance", "financial", "technology", "business", "investment", "biography", "investing", "Stock"]

        # Check if the summary contains any of the specified categories
        should_bypass = any(category in summary.lower() for category in categories_to_bypass)
        should_keep = any(category in summary.lower() for category in categories_to_keep)

        # Append to hot_keywords only if the summary does not contain any specified category or contains the specified categories to keep
        if not should_bypass or should_keep:
            hot_keywords.append((rank, keyword, query_count, org))
        else:
            matching_categories = [category for category in categories_to_bypass if category in summary.lower()]
            # print(f"The {keyword} detail contains the following matching categories: {', '.join(matching_categories)}")
            # 在 print 語句中使用 DARK_GREEN 來顯示 keyword
            print(f"The {DARK_GREEN}{keyword}{RESET} detail contains the following matching categories: {', '.join(matching_categories)}")

    return hot_keywords

# 使用命令列參數取得地理位置列表
geo_locations = sys.argv[1:] if len(sys.argv) > 1 else ["TW"]  # 預設地理位置是台灣

# 建立空的 DataFrame 用於結合所有的結果
combined_df = pd.DataFrame()

# 呼叫函式取得每個地理位置的 Google 熱門關鍵字列表
for geo_location in geo_locations:
    keywords = get_google_hot_keywords(geo_location)
    print_keywords(keywords)

    # 將每個地理位置的結果加入合併的 DataFrame
    df = pd.DataFrame(keywords, columns=["Rank", "Keyword", "Count", "Detail"])
    combined_df = pd.concat([combined_df, df])

# 取得當前時間作為工作表名稱
now = datetime.now()
sheet_name = now.strftime("%Y-%m-%d %H-%M-%S")

# 寫入 Excel 檔案
output_file = "hot_keywords.xlsx"
if os.path.isfile(output_file):
    with pd.ExcelWriter(output_file, mode="a", engine="openpyxl") as writer:
        combined_df.to_excel(writer, sheet_name=sheet_name, index=False)
else:
    combined_df.to_excel(output_file, sheet_name=sheet_name, index=False)



