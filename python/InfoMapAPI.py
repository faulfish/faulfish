import http.client
import json
import argparse

def send_location_data(location_data):
    # API 路由的主機和端口
    host = 'infomap.edbufmeuf4asgeaj.japaneast.azurecontainer.io'
    port = 5000

    # 將資料轉換為 JSON 格式
    data = json.dumps(location_data)

    # 發送 POST 請求
    conn = http.client.HTTPConnection(host, port)
    headers = {'Content-type': 'application/json'}
    conn.request('POST', '/api/locations', data, headers)

    # 取得回應
    response = conn.getresponse()

    # 檢查回應是否成功
    if response.status == 200:
        # 解析回應的 JSON 資料
        response_data = json.loads(response.read().decode())
        print('地理位置摘要資訊：')
        print(f'地點名稱：{response_data["location_name"]}')
        print(f'緯度：{response_data["latitude"]}')
        print(f'經度：{response_data["longitude"]}')
        print(f'摘要：{response_data["summary"]}')
    else:
        print('呼叫 API 失敗')

    # 關閉連線
    conn.close()

if __name__ == "__main__":
    # 建立命令列參數解析器
    parser = argparse.ArgumentParser(description='Send location data to API.')
    parser.add_argument('--name', type=str, help='Location name')
    parser.add_argument('--latitude', type=float, help='Latitude')
    parser.add_argument('--longitude', type=float, help='Longitude')
    parser.add_argument('--summary', type=str, help='Location summary')
    
    # 解析命令列參數
    args = parser.parse_args()

    # 要發送的地理位置資料
    location_data = {
        'location_name': args.name,
        'latitude': args.latitude,
        'longitude': args.longitude,
        'summary': args.summary
    }

    # 呼叫函數並傳入地理位置資料
    send_location_data(location_data)

# Call sample    
# python3 InfoMapAPI.py --name "墨西哥城ssss" --latitude 19.4326 --longitude -99.1332 --summary "dhdhsbdsb墨西哥的首都，人口眾多，擁有豐富的文化和歷史。"

