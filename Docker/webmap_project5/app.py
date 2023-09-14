from flask import Flask, request, jsonify
import pika
import json

app = Flask(__name__)

# RabbitMQ連接設定
rabbitmq_host = 'localhost'
rabbitmq_port = 5672
rabbitmq_queue = 'anonymous_data_queue'

def send_to_rabbitmq(data):
    # 使用上下文管理器處理RabbitMQ連線
    with pika.BlockingConnection(pika.ConnectionParameters(host=rabbitmq_host, port=rabbitmq_port)) as connection:
        channel = connection.channel()

        # 建立Queue
        channel.queue_declare(queue=rabbitmq_queue)

        # 發布匿名資料到RabbitMQ
        channel.basic_publish(exchange='', routing_key=rabbitmq_queue, body=data)

@app.route('/api/data', methods=['POST'])
def collect_data():
    try:
        data = request.get_json()  # 從POST請求中獲取JSON格式的匿名資料
        print(data)
        if data is None:
            return jsonify({'message': 'Invalid JSON data'}), 400

        # 轉發資料到 RabbitMQ
        data_json = json.dumps(data)
        send_to_rabbitmq(data_json)

        # 生成回應
        response_data = generate_response(data)

        # 回應JSON格式的回應
        return jsonify(response_data), 200

    except Exception as e:
        return jsonify({'message': str(e)}), 500

def generate_response(data):
    # 在這裡根據收到的匿名資料生成回應
    # 假設回應是一個包含原始資料的字典
    response_data = {'message': 'Data collected successfully', 'data': data}
    return response_data

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
