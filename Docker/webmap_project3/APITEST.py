import requests

base_url = 'http://localhost:5000/api/'

# 新增地點
def add_location(name, latitude, longitude, summary):
    add_location_url = base_url + 'add_location'
    new_location_data = {
        "name": name,
        "latitude": latitude,
        "longitude": longitude,
        "summary": summary
    }
    response = requests.post(add_location_url, json=new_location_data)
    return response.json()

# 更新地點
def update_location(index, name, latitude, longitude, summary):
    update_location_url = base_url + f'update_location/{index}'
    updated_location_data = {
        "name": name,
        "latitude": latitude,
        "longitude": longitude,
        "summary": summary
    }
    response = requests.put(update_location_url, json=updated_location_data)
    return response.json()

# 刪除地點
def delete_location(index):
    delete_location_url = base_url + f'delete_location/{index}'
    response = requests.delete(delete_location_url)
    return response.json()

# 查詢地點
def get_locations():
    get_locations_url = base_url + 'add_location'
    response = requests.get(get_locations_url)
    return response.json()

if __name__ == '__main__':
    # 新增地點
    new_location = add_location("New Location", 25.1234, 120.5678, "This is a new location")
    print("新增地點:", new_location)

    # 更新地點
    updated_location = update_location(0, "Updated Location", 35.6789, -80.2345, "This location has been updated")
    print("更新地點:", updated_location)

    # 查詢地點
    all_locations = get_locations()
    print("目前所有地點:", all_locations)

    # 刪除地點
    deleted_location = delete_location(0)
    print("刪除地點:", deleted_location)

    # 再次查詢地點
    all_locations = get_locations()
    print("目前所有地點:", all_locations)
