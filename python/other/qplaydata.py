from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import requests
import getpass
import time

# 開始搜尋的初始URL
start_url = 'https://qplay.benq.com/qplay/public/auth/login'

# 使用Selenium開啟瀏覽器並自動登入
driver = webdriver.Chrome(service=Service('/usr/local/bin/chromedriver'))
driver.get(start_url)

# 填寫登入表單
username = driver.find_element(By.ID, 'loginid')  # 根據實際網頁元素的ID選擇器修改
password = driver.find_element(By.ID, 'cipher')  # 根據實際網頁元素的ID選擇器修改
username.send_keys('alan.tu')  # 根據實際的用戶名修改
passwordstr = getpass.getpass('請輸入密碼：')
password.send_keys(passwordstr)  # 根據實際的密碼修改
# password.send_keys(Keys.RETURN)  # 按下Enter鍵提交表單

# 按下 "Sign In" 按鈕
sign_in_button = driver.find_element(By.ID, 'signIn')  # 根據實際網頁元素的ID選擇器修改
sign_in_button.click()

# 等待登入完成
WebDriverWait(driver, 10).until(EC.url_contains('/public/accountMaintain'))

url = 'https://qplay.benq.com/qplay/public/accountMaintain'
driver.get(url)

# 等待10秒
# time.sleep(10)

# 使用等待機制等待特定元素的出現
wait = WebDriverWait(driver, 10)
switchright = wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'switch-right')))


# 使用BeautifulSoup解析HTML
soup = BeautifulSoup(driver.page_source, 'html.parser')
pageinfo = soup.find('span', class_='pagination-info')
if pageinfo is not None:
    pageinfostr = pageinfo.text.strip()
    print("pageinfo:", pageinfostr)
else:
    print("無法找到pageinfo")

driver.quit()  # 關閉瀏覽器
