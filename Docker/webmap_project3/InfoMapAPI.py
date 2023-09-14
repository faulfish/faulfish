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
    return jsonify({'message': 'Location added successfully'})

@app.route('/api/update_location/<int:index>', methods=['PUT'])
def update_location(index):
    data = read_data()
    updated_location = request.json
    data[index] = updated_location
    write_data(data)
    return jsonify({'message': 'Location updated successfully'})

@app.route('/api/delete_location/<int:index>', methods=['DELETE'])
def delete_location(index):
    data = read_data()
    del data[index]
    write_data(data)
    return jsonify({'message': 'Location deleted successfully'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
