import requests

# API端點URL
url = 'http://localhost:5000/api/data'

# 假設要傳送的匿名資料為一個字典
data = {'name': 'John', 'age': 30, 'gender': 'male'}

# 發送HTTP POST請求
response = requests.post(url, json=data)

# 檢查回應的HTTP狀態碼
if response.status_code == 200:
    print('200:', response.json())  # Get the response content as JSON
    print('Anonymous data sent and published successfully.')
else:
    print('Error:', response.json())  # Get the response content as JSON

