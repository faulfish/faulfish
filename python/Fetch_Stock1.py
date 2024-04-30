import requests
from bs4 import BeautifulSoup
import re
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.keys import Keys

# File name and path
file_name = 'Excel/stockdata.xlsx'

# Initialize Selenium webdriver
driver = webdriver.Chrome()

# Open the MOPS website
url = 'https://mops.twse.com.tw/mops/web/index'
driver.get(url)

# Click on the "股票查詢" button (id=co_id)
co_id_button = driver.find_element_by_id('co_id')
co_id_button.click()

# Type the stock code (2603) into the input field (id=co_id)
stock_code_input = driver.find_element_by_id('co_id')
stock_code_input.send_keys('2603')

# Press Enter to submit the stock code
stock_code_input.send_keys(Keys.ENTER)

# Wait for the data to load
time.sleep(5)

# Extract the stock data from the HTML
html = driver.page_source
soup = BeautifulSoup(html, 'html.parser')

# Parse the stock data
stock_data = []
for row in soup.find_all('tr', class_='m_tb01'):
    data = [cell.text.strip() for cell in row.find_all('td')]
    stock_data.append(data)

# Convert the stock data to a Pandas DataFrame
df = pd.DataFrame(stock_data, columns=['日期', '開盤', '最高', '最低', '收盤', '成交量', '成交金額'])

# Save the DataFrame to an Excel file
df.to_excel(file_name, index=False)

# Close the Selenium webdriver
driver.quit()
