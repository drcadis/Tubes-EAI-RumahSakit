import pika
import json
import os
import logging
import time

logger = logging.getLogger(__name__)

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")


def get_connection():
    """Buat koneksi ke RabbitMQ dengan retry otomatis (jika broker belum siap)"""
    for attempt in range(5):
        try:
            params = pika.URLParameters(RABBITMQ_URL)
            connection = pika.BlockingConnection(params)
            logger.info("Berhasil konek ke RabbitMQ")
            return connection
        except Exception as e:
            logger.warning(f"Gagal konek RabbitMQ (percobaan {attempt+1}/5): {e}")
            time.sleep(3)
    raise Exception("Tidak bisa konek ke RabbitMQ setelah 5 percobaan")


def publish_event(exchange: str, routing_key: str, payload: dict):
    """
    Kirim event ke RabbitMQ.
    
    Exchange  : nama exchange (misal: 'pharmacy_events')
    routing_key: kunci routing (misal: 'resep.selesai')
    payload   : data yang dikirim (dict, akan di-convert ke JSON)
    """
    try:
        connection = get_connection()
        channel = connection.channel()

        # Pastikan exchange ada (idempotent)
        channel.exchange_declare(
            exchange=exchange,
            exchange_type='topic',   # topic = routing key bisa pakai wildcard
            durable=True             # bertahan saat broker restart
        )

        message = json.dumps(payload)

        channel.basic_publish(
            exchange=exchange,
            routing_key=routing_key,
            body=message,
            properties=pika.BasicProperties(
                delivery_mode=2,     # 2 = persistent message (tidak hilang saat restart)
                content_type='application/json'
            )
        )

        logger.info(f"Event terkirim | exchange={exchange} | key={routing_key} | data={message}")
        connection.close()

    except Exception as e:
        logger.error(f"Gagal publish event: {e}")
        raise


def publish_resep_selesai(resep_data: dict):
    """
    Event khusus: resep selesai diproses.
    Event ini akan dikonsumsi oleh Billing Service untuk membuat tagihan.
    """
    publish_event(
        exchange="pharmacy_events",
        routing_key="resep.selesai",
        payload={
            "event_type": "RESEP_SELESAI",
            "source": "pharmacy-service",
            "data": resep_data
        }
    )


def publish_stok_menipis(obat_data: dict):
    """
    Event khusus: stok obat hampir habis.
    Event ini bisa dikonsumsi oleh sistem pengadaan (notifikasi admin).
    """
    publish_event(
        exchange="pharmacy_events",
        routing_key="stok.menipis",
        payload={
            "event_type": "STOK_MENIPIS",
            "source": "pharmacy-service",
            "data": obat_data
        }
    )
