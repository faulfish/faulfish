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

# 開始搜尋的初始URL
start_url = 'https://store.benq.com/tw-buy-staff/'

# 使用Selenium開啟瀏覽器並自動登入
driver = webdriver.Chrome(service=Service('/usr/local/bin/chromedriver'))
driver.get(start_url)

# 填寫登入表單
username = driver.find_element(By.ID, 'email')  # 根據實際網頁元素的ID選擇器修改
password = driver.find_element(By.ID, 'pass')  # 根據實際網頁元素的ID選擇器修改
username.send_keys('alan.tu@benq.com')  # 根據實際的用戶名修改
passwordstr = getpass.getpass('請輸入密碼：')
password.send_keys(passwordstr)  # 根據實際的密碼修改
password.send_keys(Keys.RETURN)  # 按下Enter鍵提交表單

# 等待登入完成
WebDriverWait(driver, 10).until(EC.url_contains('/tw-buy-staff'))

visited_urls = set()  # 記錄已經訪問過的URL，避免重複訪問
max_depth = 3  # 設定最大遞迴深度

def crawl(url, depth=0):
    # 檢查遞迴深度是否超過最大深度
    if depth > max_depth:
        return

    # 檢查是否已訪問過該URL，如果是則返回，避免重複訪問
    if url in visited_urls:
        return

    driver.get(url)

    visited_urls.add(url)  # 將該URL標記為已訪問
    print("搜尋網站:", url)  # 列印已搜尋的網站

    # 使用BeautifulSoup解析HTML
    soup = BeautifulSoup(driver.page_source, 'html.parser')

    product_info_main = soup.find('div', class_='product-info-main')
    if product_info_main:
        #print(product_info_main)
        product_name = soup.find('span', itemprop='name').text.strip()
        price = soup.find('span', class_='price').text.strip()
        print("產品名:", product_name)
        print("價格:", price)
    #else:
    #    print("未找到具有 class='product-info-main' 的元素")


    # 遍歷網頁中的連結，並遞迴調用crawl函式進行深入搜尋
    links = soup.find_all('a')
    for link in links:
        next_url = link.get('href')
        if next_url:
            # 確保next_url是絕對URL，可以使用urljoin函式來處理相對URL
            next_url = urljoin(url, next_url)

            # 驗證URL的協議是否是HTTP或HTTPS且不以指定的開頭開始
            parsed_url = urlparse(next_url)
            if (
                parsed_url.scheme in ('http', 'https')
                and next_url.startswith("https://store.benq.com/tw-buy-staff")
                and not next_url.startswith("https://store.benq.com/tw-buy-staff/customer")
                and not next_url.startswith("https://store.benq.com/tw-buy-staff/member")
                and not next_url.startswith("https://store.benq.com/tw-buy-staff/newsletter")
                and not next_url.startswith("https://store.benq.com/tw-buy-staff/sales")
                and not next_url.startswith("https://store.benq.com/tw-buy-staff/checkout")
                and not next_url.startswith("https://store.benq.com/tw-buy-staff/trackorder")
                and not next_url.startswith("https://store.benq.com/tw-buy-staff/#")
                and "logout" not in next_url #避免按到登出
            ):
                crawl(next_url, depth + 1)  # 遞迴調用並增加遞迴深度


# 開始遞迴深入搜尋
crawl(start_url)

driver.quit()  # 關閉瀏覽器

