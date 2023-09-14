import pika

# RabbitMQ連接設定
rabbitmq_host = 'localhost'
rabbitmq_port = 5672

def create_topic_exchange(channel, exchange_name):
    channel.exchange_declare(exchange=exchange_name, exchange_type='topic')

def bind_queue_to_topic_exchange(channel, queue_name, exchange_name, routing_key):
    queue_declare_ok = channel.queue_declare(queue=queue_name, durable=True)  # 設置佇列為持久化的
    if queue_declare_ok.method.message_count == 0:
        channel.queue_bind(exchange=exchange_name, queue=queue_name, routing_key=routing_key)

def send_message_to_topic_exchange(channel, exchange_name, routing_key, message):
    channel.basic_publish(
        exchange=exchange_name,
        routing_key=routing_key,
        body=message,
        properties=pika.BasicProperties(
            delivery_mode=2,  # 設置消息為持久化的
        )
    )

def receive_message_from_queue(channel, queue_name):
    method_frame, header_frame, body = channel.basic_get(queue=queue_name, auto_ack=False)  # 將auto_ack設為False，以便消費者手動確認
    if method_frame:
        channel.basic_ack(delivery_tag=method_frame.delivery_tag)  # 消費者確認
        return body.decode('utf-8')
    else:
        return None

def main():
    # 建立RabbitMQ連線
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=rabbitmq_host, port=rabbitmq_port))
    channel = connection.channel()

    # 建立主題交換及綁定佇列
    exchange_name = 'topic_exchange'
    create_topic_exchange(channel, exchange_name)

    # 針對不同主題綁定佇列
    travel_queue = 'travel_queue'
    weather_queue = 'weather_queue'
    taipei_queue = 'taipei_queue'
    bind_queue_to_topic_exchange(channel, travel_queue, exchange_name, 'travel.*')
    bind_queue_to_topic_exchange(channel, weather_queue, exchange_name, 'weather.*')
    bind_queue_to_topic_exchange(channel, taipei_queue, exchange_name, 'taipei.*')

    # 發送消息到主題交換
    message_travel = 'Hello, this is a travel message!'
    message_weather = 'Hello, this is a weather message!'
    message_taipei = 'Hello, this is a taipei message!'
    send_message_to_topic_exchange(channel, exchange_name, 'travel.destination1', message_travel)
    send_message_to_topic_exchange(channel, exchange_name, 'weather.temperature', message_weather)
    send_message_to_topic_exchange(channel, exchange_name, 'taipei.location1', message_taipei)

    # 接收消息
    received_travel = receive_message_from_queue(channel, travel_queue)
    received_weather = receive_message_from_queue(channel, weather_queue)
    received_taipei = receive_message_from_queue(channel, taipei_queue)

    print('Received travel message:', received_travel)
    print('Received weather message:', received_weather)
    print('Received taipei message:', received_taipei)

    # 關閉連線
    connection.close()

if __name__ == '__main__':
    main()
