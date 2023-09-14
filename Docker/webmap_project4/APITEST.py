import requests
import argparse
import json

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
    locations = response.json()
    formatted_locations = json.dumps(locations, indent=2, ensure_ascii=False)
    print(formatted_locations)
    return locations

def set_map_center(latitude, longitude, zoom):
    set_map_center_url = base_url + 'set_map_center'
    map_center_data = {
        "latitude": latitude,
        "longitude": longitude,
        "zoom": zoom
    }
    response = requests.post(set_map_center_url, json=map_center_data)
    if response.status_code == 200:
        print("地圖中心設定成功")
    else:
        print("地圖中心設定失敗")

def main():
    parser = argparse.ArgumentParser(description='Manage locations with InfoMapAPI')
    parser.add_argument('--add', action='store_true', help='Add a new location')
    parser.add_argument('--update', type=int, help='Update a location by index')
    parser.add_argument('--delete', type=int, help='Delete a location by index')
    parser.add_argument('--name', help='Location name')
    parser.add_argument('--latitude', type=float, help='Location latitude')
    parser.add_argument('--longitude', type=float, help='Location longitude')
    parser.add_argument('--summary', help='Location summary')
    parser.add_argument('--set_map_center', action='store_true', help='Set map center')
    parser.add_argument('--map_latitude', type=float, help='Map center latitude')
    parser.add_argument('--map_longitude', type=float, help='Map center longitude')
    parser.add_argument('--map_zoom', type=int, help='Map zoom level')
    args = parser.parse_args()

    if args.add:
        new_location = add_location(args.name, args.latitude, args.longitude, args.summary)
        print("新增地點:", new_location)
    elif args.update is not None:
        updated_location = update_location(args.update, args.name, args.latitude, args.longitude, args.summary)
        print("更新地點:", updated_location)
    elif args.delete is not None:
        deleted_location = delete_location(args.delete)
        print("刪除地點:", deleted_location)
    elif args.set_map_center:
        set_map_center(args.map_latitude, args.map_longitude, args.map_zoom)
    else:
        all_locations = get_locations()
        # print("目前所有地點:", all_locations)

if __name__ == '__main__':
    main()


# python3 APITEST.py --add --name "New Location" --latitude 25.1234 --longitude 120.5678 --summary "This is a new location"
# python3 APITEST.py --update 0 --name "Updated Location" --latitude 35.6789 --longitude -80.2345 --summary "This location has been updated"
# python3 APITEST.py --update 0 --name "Updated Location" --latitude 35.6789 --longitude -80.2345 --summary "This location has been updated"
# python3 APITEST.py
# python3 APITEST.py --set_map_center --map_latitude 25.0 --map_longitude 120.0 --map_zoom 6

