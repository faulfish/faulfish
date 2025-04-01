import os
import requests
from flask import Flask, render_template, jsonify, request
from dotenv import load_dotenv
import json # 用於格式化打印 JSON

# 加載 .env 文件中的環境變數 (例如 NEWS_API_KEY)
load_dotenv()

# 初始化 Flask 應用
app = Flask(__name__)

# --- 配置和常量 ---
# 從環境變數讀取 API Key，如果找不到則使用佔位符 (會導致 401 錯誤)
NEWS_API_KEY = os.getenv('NEWS_API_KEY', 'YOUR_NEWS_API_KEY')
NEWS_API_ENDPOINT = 'https://newsapi.org/v2/top-headlines'

# --- 默認 API 查詢參數 ---
# 這個字典定義了 API 請求的預設值
# 也會被傳遞給前端模板，用於初始化表單
DEFAULT_PARAMS = {
    'country': 'us',      # 預設國家: 台灣
    'category': 'general',# 預設類別: 一般
    'pageSize': 20,       # 預設每頁新聞數量
    'sortBy': 'publishedAt' # 預設排序: 按發布時間 (通常比 popularity 更可靠)
                           # 可以改成 'popularity' 或 'relevancy'
}

# --- 路由定義 ---

@app.route('/')
def index():
    """
    主頁面路由。
    渲染 index.html 模板，並將 DEFAULT_PARAMS 傳遞給它，
    以便前端表單可以顯示預設值。
    """
    print("Rendering index page with default params.")
    return render_template('index.html', params=DEFAULT_PARAMS)

@app.route('/get_news')
def get_news():
    """
    API 端點，用於從 NewsAPI 獲取新聞數據。
    它會從前端的請求查詢字符串中獲取參數 (country, category 等)，
    如果前端沒有提供，則使用 DEFAULT_PARAMS 中的值。
    """
    # 檢查 API Key 是否已配置
    if NEWS_API_KEY == 'YOUR_NEWS_API_KEY':
         print("警告：未配置 NEWS_API_KEY。請在 .env 文件中設置 NEWS_API_KEY。正在返回模擬數據。")
         # 提供一些模擬數據，方便在沒有 API Key 的情況下測試前端
         mock_articles = [
             {'title': '模擬新聞標題 1', 'url': '#', 'description': '這是第一條模擬新聞的描述。', 'source': {'name': '模擬來源'}},
             {'title': '模擬新聞標題 2', 'url': '#', 'description': '這是第二條模擬新聞的描述。', 'source': {'name': '模擬來源'}},
             {'title': '模擬新聞標題 3', 'url': '#', 'description': '這是第三條模擬新聞的描述。', 'source': {'name': '模擬來源'}},
         ]
         return jsonify({'status': 'ok', 'articles': mock_articles})

    # 從前端請求的查詢字符串中獲取參數
    # request.args.get('參數名', 默認值)
    country = request.args.get('country', DEFAULT_PARAMS['country'])
    category = request.args.get('category', DEFAULT_PARAMS['category'])
    # 對 pageSize 做類型轉換和驗證，確保是數字
    try:
        page_size = int(request.args.get('pageSize', DEFAULT_PARAMS['pageSize']))
        if page_size < 1: page_size = 1
        if page_size > 100: page_size = 100 # NewsAPI 的 pageSize 上限是 100
    except ValueError:
        page_size = DEFAULT_PARAMS['pageSize'] # 如果轉換失敗，使用默認值

    sort_by = request.args.get('sortBy', DEFAULT_PARAMS['sortBy'])

    # 構建發送給 NewsAPI 的參數字典
    params = {
        'apiKey': NEWS_API_KEY,
        'country': country,
        'category': category,
        'pageSize': page_size,
        'sortBy': sort_by
    }

    # --- 調試輸出：打印將要發送的參數 ---
    print(f"\n--- Requesting NewsAPI with params: {params} ---")

    try:
        # 發送 GET 請求到 NewsAPI
        response = requests.get(NEWS_API_ENDPOINT, params=params, timeout=10) # 增加超時設置

        # --- 調試輸出：打印 NewsAPI 的響應狀態碼 ---
        print(f"--- NewsAPI Response Status Code: {response.status_code} ---")

        # 檢查請求是否成功 (狀態碼 2xx)
        response.raise_for_status() # 如果狀態碼不是 2xx，會拋出 HTTPError 異常

        # 解析返回的 JSON 數據
        news_data = response.json()

        # --- 調試輸出：打印從 NewsAPI 收到的原始數據 ---
        print("--- Raw NewsAPI Response Data ---")
        # 使用 json.dumps 格式化輸出，更易讀，並處理 unicode 字符
        print(json.dumps(news_data, indent=2, ensure_ascii=False))
        print("---------------------------------")

        # 檢查 NewsAPI 返回的業務狀態是否為 'ok'
        if news_data.get('status') == 'ok':
            articles_count = len(news_data.get('articles', []))
             # --- 調試輸出：打印找到的文章數量 ---
            print(f"--- Articles found: {articles_count} ---")
            # 將原始數據以 JSON 格式返回給前端
            return jsonify(news_data)
        else:
            # 如果 NewsAPI 返回的 status 不是 'ok' (例如 'error')
            error_message = news_data.get('message', 'Unknown error from NewsAPI')
            print(f"--- NewsAPI returned status '{news_data.get('status')}', message: {error_message} ---")
            # 向前端返回錯誤信息
            return jsonify({'status': 'error', 'message': f"NewsAPI Error: {error_message}"}), 500

    # 處理網絡請求錯誤 (例如連接超時、DNS 解析失敗)
    except requests.exceptions.Timeout:
        print(f"請求 NewsAPI 時發生超時錯誤 (Timeout)")
        return jsonify({'status': 'error', 'message': '無法連接到新聞服務: 請求超時'}), 504 # Gateway Timeout
    except requests.exceptions.RequestException as e:
        # requests 庫可能引發的其他請求相關錯誤
        print(f"請求 NewsAPI 時發生錯誤: {e}")
        # 通常返回 503 Service Unavailable
        return jsonify({'status': 'error', 'message': f'無法連接到新聞服務: {e}'}), 503
    # 處理其他所有可能的異常 (例如 JSON 解析錯誤、程式碼邏輯錯誤等)
    except Exception as e:
        print(f"處理新聞時發生未知錯誤: {e}")
        # 返回 500 Internal Server Error
        return jsonify({'status': 'error', 'message': f'伺服器內部錯誤: {e}'}), 500

# --- 運行應用 ---
if __name__ == '__main__':
    # debug=True 會在程式碼變動時自動重載伺服器，並提供更詳細的錯誤頁面
    # port=5001 指定服務器監聽的端口
    # host='0.0.0.0' 可以讓同一個局域網內的其他設備訪問，如果只需要本機訪問用 '127.0.0.1' 或不指定
    app.run(debug=True, port=5001)