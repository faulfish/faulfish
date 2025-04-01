import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from process_url import process_url, close_browser

# 開始搜尋的初始URL
start_url = 'https://www.benq.com/zh-tw/index.html'  # 替換為你要開始搜尋的初始URL

visited_urls = set()  # 記錄已經訪問過的URL，避免重複訪問
max_depth = 3  # 設定最大遞迴深度
product_counter = 1  # 產品編號計數器
max_price = 0.0

exclude_urls = [
    "https://www.benq.com/zh-tw/education",
    "https://www.benq.com/zh-tw/knowledge-center",
    "https://www.benq.com/zh-tw/news",
    "https://www.benq.com/zh-tw/support",
    "https://www.benq.com/zh-tw/business"
]

def crawl(url, depth=0):

    global product_counter
    global max_price

    # 檢查遞迴深度是否超過最大深度
    if depth > max_depth:
        return

    # 檢查是否已訪問過該URL，如果是則返回，避免重複訪問
    if url in visited_urls:
        return

    # 發送GET請求獲取網頁內容 
    try:
        response = requests.get(url)
    except requests.exceptions.InvalidSchema:
        return

    visited_urls.add(url)  # 將該URL標記為已訪問
    # print("搜尋網站:", url)  # 列印已搜尋的網站

    # 使用BeautifulSoup解析HTML
    soup = BeautifulSoup(response.text, 'html.parser')

    # 尋找具有指定 class 屬性的連結
    links = soup.find_all('a', class_='buy-button')

    # 處理每個連結
    for link in links:
        # 取得連結的絕對 URL
        absolute_url = urljoin(url, link['href'])
        product_counter, max_price = process_url(absolute_url, product_counter, max_price)

    # 遍歷網頁中的連結，並遞迴調用crawl函式進行深入搜尋
    links = soup.find_all('a')
    for link in links:
        next_url = link.get('href')
        if next_url:
            # 確保next_url是絕對URL，可以使用urljoin函式來處理相對URL
            next_url = urljoin(url, next_url)

            # 驗證URL的協議是否是HTTP或HTTPS且不在排除的URL列表中
            parsed_url = urlparse(next_url)
            if (
                parsed_url.scheme in ('http', 'https')
                and next_url.startswith("https://www.benq.com/zh-tw/")
                and next_url not in exclude_urls
            ):
                crawl(next_url, depth + 1)  # 遞迴調用並增加遞迴深度

crawl(start_url)
print("最高價格:", "$" + str(max_price))
close_browser()