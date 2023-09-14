from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# 首頁，用於顯示地圖
@app.route('/')
def index():
    return render_template('index.html')

# API 路由，用於接收地理位置並返回摘要資訊
@app.route('/api/locations', methods=['POST'])
def add_location():
    data = request.get_json()
    # 在這裡處理地理位置資料，並獲取摘要資訊
    location_name = data.get('location_name')
    latitude = data.get('latitude')
    longitude = data.get('longitude')
    
    # 假設這裡從外部資料來源獲取地理位置摘要資訊
    summary_info = {
        'location_name': location_name,
        'latitude': latitude,
        'longitude': longitude,
        'summary': '這是一個美麗的地方。',
    }
    
    return jsonify(summary_info)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
