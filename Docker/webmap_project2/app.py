import logging
from flask import Flask, request, jsonify, render_template
import json

app = Flask(__name__)

# 設定 log 訊息寫入到檔案
logging.basicConfig(filename='app.log', level=logging.INFO)

# 首頁，用於顯示地圖
@app.route('/')
def index():
    # 寫入 log 訊息，確認檔案位置
    logging.info(f"file.json location: {file_path}")

    return render_template('index.html')

# 儲存地點資訊的檔案路徑
file_path = "static/file.json"

# 初始化地點資訊列表
locations = []

@app.route('/api/locations', methods=['POST'])
def add_location():
    data = request.get_json()

    # 從請求中獲取地點資訊
    location_name = data.get('location_name')
    latitude = data.get('latitude')
    longitude = data.get('longitude')
    summary = data.get('summary')

    # 建立新的地點物件
    new_location = {
        'location_name': location_name,
        'latitude': latitude,
        'longitude': longitude,
        'summary': summary
    }

    # 將新的地點加入地點資訊列表
    locations.append(new_location)

    # 將地點資訊列表寫入檔案
    with open(file_path, 'w') as file:
        json.dump(locations, file)

    # 寫入 log 訊息，確認檔案位置
    # logging.info(f"file.json location: {file_path}")

    return jsonify(new_location), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
