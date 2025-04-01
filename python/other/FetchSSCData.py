from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import pandas as pd

# 開始搜尋的初始URL
start_url = 'https://platform.securityscorecard.io/#/start'

# 使用Selenium開啟瀏覽器並自動登入
driver = webdriver.Chrome(service=Service('/usr/local/bin/chromedriver'))
driver.get(start_url)

# 填寫登入表單
username = driver.find_element(By.ID, 'username')  # 根據實際網頁元素的ID選擇器修改
password = driver.find_element(By.ID, 'password')  # 根據實際網頁元素的ID選擇器修改
username.send_keys('kelly.tc.chen@benq.com')  # 根據實際的用戶名修改
# passwordstr = getpass.getpass('請輸入密碼：')
passwordstr = 'qwQWQW1234!'
password.send_keys(passwordstr)  # 根據實際的密碼修改
# password.send_keys(Keys.RETURN)  # 按下Enter鍵提交表單
password.submit()  # 提交表單

# 等待出現'Good morning'
wait = WebDriverWait(driver, 10)  # 最多等待10秒
good_morning_element = wait.until(EC.presence_of_element_located((By.XPATH, "//h4[contains(text(), 'Good morning')]")))

# 印出'Good morning'的內容
print(good_morning_element.text)

url = 'https://platform.securityscorecard.io/#/portfolios/38513008-3f13-5fa3-a2ec-d853d743b51a/companies'
driver.get(url)

# 等待N秒
time.sleep(6)

# 使用BeautifulSoup解析網頁
soup = BeautifulSoup(driver.page_source, 'html.parser')

# 找到帶有 role="rowgroup" 的 tbody 元素
tbody_element = soup.find('tbody', {'role': 'rowgroup'})

# 找到所有 class 為 "ds-table-row" 的 tr 元素
tr_elements = tbody_element.find_all('tr', class_='ds-table-row')

# 迭代處理每個 tr 元素
for i, tr_element in enumerate(tr_elements):
    td_elements = tr_element.find_all('td')
    row_data = [td.text for td in td_elements]
    print(f"Row {i+1}: {row_data}")

# driver.quit()  # 關閉瀏覽器

