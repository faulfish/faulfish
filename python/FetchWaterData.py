import os
import pandas as pd
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time


# 使用Selenium開啟瀏覽器並自動登入//chromedriver//Google Chrome for Testing.app
# driver = webdriver.Chrome(service=Service('/usr/local/bin/chromedriver' ) )
chrome_driver_path = '/usr/local/bin/chromedriver'
driver = webdriver.Chrome(executable_path=chrome_driver_path)

url = 'https://water.taiwanstat.com/'
driver.get(url)

# 等待渲染完成
wait = WebDriverWait(driver, 10)
wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'reservoir')))

# 等待N秒
time.sleep(2)

soup = BeautifulSoup(driver.page_source, 'html.parser')
reservoirs = soup.find_all(class_="reservoir")

# 建立空的資料框架
df = pd.DataFrame(columns=['Name', 'Liquid', 'Volume', 'State', 'LastUpdate'])

for reservoir in reservoirs:
    name = reservoir.find(class_="name").text.strip()

    liquid_fill_text = reservoir.find(class_="liquidFillGaugeText") or reservoir.find("text", class_="liquidFillGaugeText")
    if liquid_fill_text is not None:
        text = liquid_fill_text.text.strip()
        print("Liquid:", text)
    else:
        text = "N/A"

    volumn = reservoir.find(class_="volumn").text.strip()

    state_element = reservoir.find(class_="state blue")
    if state_element is not None:
        state = state_element.text.strip()
    else:
        state = "N/A"

    update_at = reservoir.find(class_="updateAt").text.strip()
    print("update_at:", update_at)

    # 將水庫資料加入資料框架
    new_data = pd.DataFrame({'Name': name, 'Liquid': text, 'Volume': volumn, 'State': state, 'LastUpdate': update_at}, index=[0])
    df = pd.concat([df, new_data], ignore_index=True)

# 檢查檔案是否存在
file_path = 'reservoir_data.xlsx'
if os.path.exists(file_path):
    # 讀取現有的 Excel 檔案
    existing_data = pd.read_excel(file_path)
    # 合併現有資料和新資料
    df = pd.concat([existing_data, df], ignore_index=True)
    # 去重，保留最後一筆
    df = df.drop_duplicates(subset=['Name', 'LastUpdate'], keep='last')

# 寫入 Excel 檔案
df.to_excel(file_path, index=False)
