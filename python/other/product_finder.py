from bs4 import BeautifulSoup

def find_products(soup):
    product_containers = soup.find_all("div", class_="product_content")
    product_data = []

    for container in product_containers:
        # 取得產品名稱
        product_title = container.find("div", class_="product_title").text.strip()

        # 取得產品價格
        product_price = container.find("div", class_="product_price").text.strip()

        product_data.append({"品名": product_title, "價格": product_price})
        # 列印產品資訊和價格
        print("產品名稱:", product_title)
        print("價格:", product_price)
        print("--------------------")

    return product_data

def start_url():
    return "https://www.benqhealth.com/collections/%E6%98%8E%E5%9F%BA%E4%BD%B3%E4%B8%96%E9%81%94%E9%9B%86%E5%9C%98%E5%93%A1%E8%B3%BC%E5%B0%88%E5%8D%80?target=bo&target=blank"

'''
<button class="btn addToCart_mobile btn_quick_buy_mobile open_quick_buy_modal qk-btn qk-btn--primary qk-flex--1 qk-fs--title qk-text-truncate" data-handle="pcrservice" data-collection="" style="display: none;">
  立即購買</button>
'''
'''
<button class="btn btn_notice btn_notice_mobile hidden qk-btn qk-btn--lg qk-btn--primary qk-flex--1 qk-fs--title qk-pd--0" type="button" style="display: block;">已售完，貨到通知我</button>
'''