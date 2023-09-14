import pika
import threading
import time

# RabbitMQ連接設定
rabbitmq_host = 'localhost'
rabbitmq_port = 5672
exchange_name = 'topic_exchange'

# 使用者輸入的頻道
subscribed_channels = set()

def on_message(channel, method_frame, header_frame, body):
    # 處理接收到的訊息
    print(f"Received message: {body.decode('utf-8')}")
    channel.basic_ack(delivery_tag=method_frame.delivery_tag)

def bind_queue_to_topic_exchange(channel, queue_name, routing_key):
    # 建立Queue
    channel.queue_declare(queue=queue_name, durable=True)

    # 將Queue綁定到Topic Exchange，指定routing_key來過濾訊息
    channel.queue_bind(exchange=exchange_name, queue=queue_name, routing_key=routing_key)

def subscribe_to_channels():
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=rabbitmq_host, port=rabbitmq_port))
    channel = connection.channel()
    
    # 建立Topic Exchange
    channel.exchange_declare(exchange=exchange_name, exchange_type='topic')

    while True:
        if subscribed_channels:
            for channel_name in subscribed_channels:
                queue_name = f'{channel_name}_queue'
                bind_queue_to_topic_exchange(channel, queue_name, f'{channel_name}.*')
                channel.basic_consume(queue=queue_name, on_message_callback=on_message)

            try:
                channel.start_consuming()
            except KeyboardInterrupt:
                channel.stop_consuming()
                break

def publish_message(channel_name, message):
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=rabbitmq_host, port=rabbitmq_port))
    channel = connection.channel()

    # 建立Topic Exchange
    channel.exchange_declare(exchange=exchange_name, exchange_type='topic')

    # 發布訊息到Topic Exchange，指定routing_key來指定頻道
    channel.basic_publish(exchange=exchange_name, routing_key=f'{channel_name}.message', body=message)

    connection.close()

if __name__ == '__main__':
    print("Available channels: travel, taipei, weather")
    while True:
        command = input("Enter command (subscribe, publish, exit): ")
        if command == 'subscribe':
            channel_name = input("Enter channel to subscribe: ")
            subscribed_channels.add(channel_name)
            print(f"Subscribed to channel: {channel_name}")
        elif command == 'publish':
            channel_name = input("Enter channel to publish: ")
            message = input("Enter message to publish: ")
            publish_message(channel_name, message)
        elif command == 'exit':
            break
        else:
            print("Invalid command")

    # 訂閱線程
    subscribe_thread = threading.Thread(target=subscribe_to_channels)
    subscribe_thread.start()
