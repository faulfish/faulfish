import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# 設定Chrome驅動程式的路徑
chrome_driver_path = '/usr/local/bin/chromedriver'

# 初始化Chrome瀏覽器
driver = webdriver.Chrome(executable_path=chrome_driver_path)

# 設定目標網址
url = "https://www.ice.com/products/219/Brent-Crude-Futures/data?marketId=5430848"
driver.get(url)

# 使用WebDriverWait等待表格元素可見性
wait = WebDriverWait(driver, 10)
table = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "table-bigdata")))

if table:
    # 使用BeautifulSoup解析表格
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    row = soup.select_one("table.table-bigdata tbody tr")
    
    if row:
        cells = row.find_all("td")
        data = {
            "日期": cells[0].text.strip(),
            "價格": cells[1].text.strip(),
            "變化": cells[2].text.strip(),
            "成交量": cells[3].text.strip(),
        }
        
        print("從Table DOM中獲取的表格數據如下：")
        for key, value in data.items():
            print(f"{key}：{value}")
    else:
        print("沒有找到表格行")
else:
    print("沒有找到表格元素")

# 關閉瀏覽器
driver.quit()
