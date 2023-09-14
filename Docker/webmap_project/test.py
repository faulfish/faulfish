import http.client
import json

# API 路由的主機和端口
host = 'infomap.edbufmeuf4asgeaj.japaneast.azurecontainer.io'
port = 5000

# 要發送的地理位置資料
'''
location_data = {
    'location_name': '某個地點',
    'latitude': 25.0000,
    'longitude': 121.0000
}
'''
# 要發送的地理位置資料
location_data = {
    'location_name': '墨西哥城',
    'latitude': 19.4326,
    'longitude': -99.1332,
    'summary': '墨西哥的首都，人口眾多，擁有豐富的文化和歷史。'
}


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
