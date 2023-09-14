from flask import Flask, request, jsonify, render_template
import os
import json

app = Flask(__name__)

data_path = os.path.join(os.path.dirname(__file__), 'static', 'file.json')

def read_data():
    with open(data_path, 'r') as f:
        data = json.load(f)
    return data

def write_data(data):
    with open(data_path, 'w') as f:
        json.dump(data, f)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/add_location', methods=['GET'])
def get_locations():
    data = read_data()
    return jsonify(data)

@app.route('/api/add_location', methods=['POST'])
def add_location():
    data = read_data()
    new_location = request.json
    data.append(new_location)
    write_data(data)

    # 設定地圖中心座標和縮放層級為新增地點的位置
    # set_map_center(new_location['latitude'], new_location['longitude'], 8)

    return jsonify({'message': 'Location added successfully'})

@app.route('/api/update_location/<int:index>', methods=['PUT'])
def update_location(index):
    data = read_data()
    updated_location = request.json
    data[index] = updated_location
    write_data(data)

    # 設定地圖中心座標和縮放層級為更新地點的位置
    # set_map_center(updated_location['latitude'], updated_location['longitude'], 8)

    return jsonify({'message': 'Location updated successfully'})

@app.route('/api/delete_location/<int:index>', methods=['DELETE'])
def delete_location(index):
    data = read_data()
    del data[index]
    write_data(data)
    return jsonify({'message': 'Location deleted successfully'})


# 新增 API 端點用於設定地圖中心座標和縮放層級
@app.route('/api/set_map_center', methods=['POST'])
def set_map_center():
    map_center_data = request.json
    # 此處假設您有某種方式來將地圖中心座標和縮放層級應用到地圖上，您可以根據實際情況修改此處的程式碼
    # 這裡只是一個範例，您可以根據地圖函式庫的API來實現
    # 以下僅為示範程式碼
    map_center = {
        "latitude": map_center_data['latitude'],
        "longitude": map_center_data['longitude'],
        "zoom": map_center_data['zoom']
    }
    # 在這裡將 map_center 資料應用到地圖上，假設您有個名為 apply_map_center 的函式可以實現此功能
    # apply_map_center(map_center['latitude'], map_center['longitude'], map_center['zoom'])
    return jsonify({'message': 'Map center set successfully'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
