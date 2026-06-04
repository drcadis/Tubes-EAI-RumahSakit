import pika
import json
import os
import logging
import time
import threading

logger = logging.getLogger(__name__)

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")

# ─────────────────────────────────────────────
#  CONSUMER: Terima event dari Registrasi Service
#  Ketika pasien baru terdaftar, farmasi menyimpan
#  info pasien secara lokal untuk referensi resep.
# ─────────────────────────────────────────────

def handle_pasien_terdaftar(ch, method, properties, body):
    """
    Handler untuk event 'pasien.terdaftar' dari Registrasi Service.
    Ini contoh bagaimana farmasi bereaksi terhadap event dari sistem lain.
    """
    try:
        data = json.loads(body)
        logger.info(f"[CONSUMER] Event diterima: PASIEN_TERDAFTAR | data={data}")

        # Di sini kamu bisa simpan data pasien ke tabel lokal
        # atau hanya log untuk audit trail
        # Contoh: simpan ke cache/tabel pasien lokal
        # patient_id = data.get("data", {}).get("patient_id")
        # ... logika bisnis kamu

        # Acknowledge ke broker: pesan berhasil diproses
        ch.basic_ack(delivery_tag=method.delivery_tag)
        logger.info(f"[CONSUMER] Event berhasil diproses, ACK dikirim")

    except Exception as e:
        logger.error(f"[CONSUMER] Gagal proses event: {e}")
        # Nack = kembalikan pesan ke antrian (untuk retry)
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)


def start_consumer():
    """
    Jalankan consumer di thread terpisah agar tidak memblokir Flask.
    Consumer ini listen ke exchange 'registration_events'.
    """
    def _run():
        while True:
            try:
                params = pika.URLParameters(RABBITMQ_URL)
                connection = pika.BlockingConnection(params)
                channel = connection.channel()

                # Pastikan exchange ada
                channel.exchange_declare(
                    exchange='registration_events',
                    exchange_type='topic',
                    durable=True
                )

                # Buat antrian khusus untuk farmasi
                queue_name = os.getenv("PHARMACY_QUEUE", "pharmacy_registration_queue")
                channel.queue_declare(
                    queue=queue_name,
                    durable=True,       # antrian bertahan saat restart
                    arguments={
                        # Dead Letter Queue: pesan gagal dikirim ke sini
                        'x-dead-letter-exchange': 'dlx_exchange',
                        'x-dead-letter-routing-key': 'dead.pharmacy'
                    }
                )

                # Bind antrian ke exchange dengan routing key tertentu
                channel.queue_bind(
                    exchange='registration_events',
                    queue=queue_name,
                    routing_key='pasien.terdaftar'  # hanya event ini yang diterima
                )

                # Batasi 1 pesan sekaligus (fair dispatch)
                channel.basic_qos(prefetch_count=1)

                # Daftarkan handler
                channel.basic_consume(
                    queue=queue_name,
                    on_message_callback=handle_pasien_terdaftar
                )

                logger.info(f"[CONSUMER] Mulai listen di antrian: {queue_name}")
                channel.start_consuming()

            except Exception as e:
                logger.error(f"[CONSUMER] Koneksi terputus: {e}. Reconnect dalam 5 detik...")
                time.sleep(5)

    # Jalankan di background thread
    thread = threading.Thread(target=_run, daemon=True)
    thread.start()
    logger.info("[CONSUMER] Thread consumer dimulai")
