import requests
from bs4 import BeautifulSoup
import re
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# File name and path
file_name = 'Excel/stockdata.xlsx'

# Initialize Selenium webdriver
driver = webdriver.Chrome()

# Open the MOPS website
url = 'https://mops.twse.com.tw/mops/web/index'
driver.get(url)

# Wait for the "co_id" button to be present
wait = WebDriverWait(driver, 10)
co_id_button = wait.until(EC.presence_of_element_located((By.ID, 'co_id')))

# Click on the "股票查詢" button (id=co_id)
co_id_button = driver.find_element(By.ID, 'co_id')
co_id_button.click()

# Type the stock code (2603) into the input field (id=co_id)
stock_code_input = driver.find_element(By.ID, 'co_id')
stock_code_input.send_keys('2603')

# Press Enter to submit the stock code
stock_code_input.send_keys(Keys.ENTER)

# Wait for the data to load
time.sleep(5)

# Extract the stock data from the HTML
html = driver.page_source
soup = BeautifulSoup(html, 'html.parser')

# Parse the stock data (your existing code)

# Convert the stock data to a Pandas DataFrame (your existing code)

# Save the DataFrame to an Excel file (your existing code)

# Close the Selenium webdriver
driver.quit()
