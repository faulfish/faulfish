import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from selenium import webdriver
from selenium.webdriver.chrome.service import Service

visited_urls = set()  # 記錄已經訪問過的URL，避免重複訪問

# 使用Selenium開啟瀏覽器並自動登入
driver = webdriver.Chrome(service=Service('/usr/local/bin/chromedriver'))

def process_url(absolute_url, product_counter, max_price):
    # 檢查是否已訪問過該URL，如果是則跳過此次迴圈
    if absolute_url in visited_urls:
        return product_counter, max_price

    visited_urls.add(absolute_url)  # 將該URL標記為已訪問
    print('連結:', absolute_url)

    # 發送GET請求獲取網頁內容
    try:
        response = requests.get(absolute_url)
    except requests.exceptions.InvalidSchema:
        # 跳過無效的URL協議
        return product_counter, max_price

    # 如果該網頁符合條件，則尋找產品名和價格
    if response.status_code == 200 and "information-area" in response.text:
        driver.get(absolute_url)
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        product_name = soup.find('h1').text.strip()

        price_element = soup.find('p', class_='price')
        if price_element is not None:
            price = price_element.text.strip()
            print("產品:", product_counter, " ", product_name)
            print("價格:", price)
            product_counter += 1  # 編號+1

            # 預處理價格字串，去除非數字字元
            # price_value = float(''.join(filter(str.isdigit, price)))
            # 預處理價格字串，去除非數字和小數點字元
            price_value = float(''.join(filter(lambda x: x.isdigit() or x == '.', price)))

            if price_value > max_price:
                max_price = price_value
        else:
            print("無法找到價格")
    
    return product_counter, max_price

# 關閉瀏覽器
def close_browser():
    driver.quit()

# 示例用法
# product_counter = 1
# max_price = 0.0

# product_counter, max_price = process_url("https://example.com/product1", product_counter, max_price)
# product_counter, max_price = process_url("https://example.com/product2", product_counter, max_price)

# 列印最貴的項目
# print("最貴的項目：")
# print("產品編號:", product_counter-1)
# print("最高價格:", "$" + str(max_price))

# close_browser()
