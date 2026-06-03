import pika
import json
import os
import uuid
from datetime import datetime

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost/")
EXCHANGE_NAME = os.getenv("EXCHANGE_NAME", "hospital.events")

def get_rabbitmq_channel():
    parameters = pika.URLParameters(RABBITMQ_URL)
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()
    # Deklarasi exchange bertipe topic
    channel.exchange_declare(exchange=EXCHANGE_NAME, exchange_type='topic', durable=True)
    return connection, channel

def publish_patient_registered(patient_data: dict):
    """
    Publish event PATIENT_REGISTERED ke RabbitMQ
    """
    try:
        connection, channel = get_rabbitmq_channel()
        
        event_payload = {
            "event_id": f"evt_{uuid.uuid4().hex[:12]}",
            "event_timestamp": datetime.utcnow().isoformat() + "Z",
            "event_type": "PATIENT_REGISTERED",
            "data": patient_data
        }

        # Konversi ke JSON string
        message_body = json.dumps(event_payload)
        
        # Publish ke exchange
        routing_key = "patient.registered"
        channel.basic_publish(
            exchange=EXCHANGE_NAME,
            routing_key=routing_key,
            body=message_body,
            properties=pika.BasicProperties(
                delivery_mode=2,  # make message persistent
                content_type='application/json'
            )
        )
        print(f" [x] Sent {routing_key}:{message_body}")
        connection.close()
        return True
    except Exception as e:
        print(f"Failed to publish to RabbitMQ: {e}")
        return False
