import pika
import json
import os
import time

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
SOURCE_EXCHANGE = os.getenv("SOURCE_EXCHANGE", "hospital.events")
SOURCE_ROUTING_KEY = os.getenv("SOURCE_ROUTING_KEY", "patient.registered")

TARGET_EXCHANGE = os.getenv("TARGET_EXCHANGE", "registration_events")
TARGET_ROUTING_KEY = os.getenv("TARGET_ROUTING_KEY", "pasien.terdaftar")

def get_connection():
    while True:
        try:
            params = pika.URLParameters(RABBITMQ_URL)
            connection = pika.BlockingConnection(params)
            return connection
        except Exception as e:
            print(f"[{time.strftime('%X')}] Integration Layer - Menunggu RabbitMQ... {e}")
            time.sleep(5)

def translate_and_forward(channel, msg_body):
    try:
        # 1. Parse Event dari Registrasi (Inggris)
        event_registrasi = json.loads(msg_body)
        data_registrasi = event_registrasi.get("data", {})
        
        # 2. Transformasi (Mapping ke bahasa Indonesia untuk Farmasi)
        data_farmasi = {
            "patient_id": data_registrasi.get("patient_id", ""),
            "nama_pasien": data_registrasi.get("full_name", ""),
            "tanggal_lahir": data_registrasi.get("date_of_birth", ""),
            "jenis_kelamin": data_registrasi.get("gender", "")
        }
        
        # 3. Bentuk Payload Event Baru
        event_farmasi = {
            "event_type": "PASIEN_TERDAFTAR",
            "source": "integration-layer",
            "data": data_farmasi
        }
        
        # 4. Publish ke Exchange Farmasi
        channel.exchange_declare(exchange=TARGET_EXCHANGE, exchange_type='topic', durable=True)
        channel.basic_publish(
            exchange=TARGET_EXCHANGE,
            routing_key=TARGET_ROUTING_KEY,
            body=json.dumps(event_farmasi),
            properties=pika.BasicProperties(
                delivery_mode=2, # persisten
                content_type='application/json'
            )
        )
        print(f" [V] Pesan Diterjemahkan & Diteruskan ke {TARGET_EXCHANGE}:{TARGET_ROUTING_KEY}")
    except Exception as e:
        print(f" [X] Gagal melakukan transformasi: {e}")

def main():
    print("Memulai Integration Layer (Message Translator)...")
    connection = get_connection()
    channel = connection.channel()
    
    # Setup source queue
    channel.exchange_declare(exchange=SOURCE_EXCHANGE, exchange_type='topic', durable=True)
    queue_name = 'integration.translator.queue'
    channel.queue_declare(queue=queue_name, durable=True)
    channel.queue_bind(exchange=SOURCE_EXCHANGE, queue=queue_name, routing_key=SOURCE_ROUTING_KEY)
    
    def callback(ch, method, properties, body):
        print(f" [->] Menerima event: {method.routing_key}")
        translate_and_forward(channel, body)
        ch.basic_ack(delivery_tag=method.delivery_tag)
        
    # Konsumsi pesan
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue=queue_name, on_message_callback=callback)
    
    print(" [*] Menunggu event registrasi. Tekan CTRL+C untuk keluar.")
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        channel.stop_consuming()
    finally:
        connection.close()

if __name__ == '__main__':
    main()
