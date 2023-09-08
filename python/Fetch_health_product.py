import requests
from urllib.parse import urlparse
import pandas as pd
from bs4 import BeautifulSoup
from openpyxl import Workbook
from product_finder import find_products
from product_finder import start_url

def write_to_excel(product_data, file_name):
    if product_data:
        wb = Workbook()
        ws = wb.active
        ws.append(["連結", "時間", "品名", "價格"])
        for product in product_data:
            ws.append(product)
        wb.save(file_name)

def load_excluded_links(filename):
    with open(filename, "r") as file:
        return [line.strip() for line in file.readlines()]

def get_domain(url):
    parsed_url = urlparse(url)
    domain = parsed_url.netloc
    return domain

def crawl_product_info(start_url, excluded_links, batch_size, file_name):
    domain = get_domain(start_url)
    queue = [start_url]
    visited_links = set()
    visited_products = set()
    product_data = []

    count = 0  # 計數器，用於判斷寫入產品資訊的時機

    while queue:
        url = queue.pop(0)
        visited_links.add(url)

        print("搜尋連結:", url)

        response = requests.get(url)
        soup = BeautifulSoup(response.content, "html.parser")

        products = find_products(soup)

        for product in products:
            product_link = url
            product_time = pd.Timestamp.now()
            product_name = product["品名"]
            product_price = product["價格"]

            if product_link not in visited_products:
                product_data.append([product_link, product_time, product_name, product_price])
                visited_products.add(product_link)

                count += 1
                if count >= batch_size:
                    write_to_excel(product_data, file_name)
                    # product_data = []
                    count = 0

        links = soup.find_all("a", href=True)
        for link in links:
            href = link["href"]
            if href.startswith("https"):
                absolute_link = href
            else:
                absolute_link = urlparse(url)._replace(path=href).geturl()

            parsed_link = urlparse(absolute_link)
            if (
                parsed_link.scheme
                and parsed_link.netloc == domain
                and absolute_link not in visited_links
                and absolute_link not in queue
                and not any(absolute_link.startswith(excluded_link) for excluded_link in excluded_links)
            ):
                queue.append(absolute_link)

    # 寫入剩餘的產品資訊到檔案
    write_to_excel(product_data, file_name)



# 開始爬蟲，從指定的起始網址開始
excluded_links_file = "excluded_links.txt"
excluded_links = load_excluded_links(excluded_links_file)
batch_size = 1  # 每次寫入的產品數量
print("載入的 excluded_links:")
for link in excluded_links:
    print(link)
file_name = "product_info.xlsx"
crawl_product_info(start_url(), excluded_links, batch_size, file_name)

