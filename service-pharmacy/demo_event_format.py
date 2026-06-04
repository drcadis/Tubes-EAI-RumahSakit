"""
Demo: menghasilkan format event RabbitMQ untuk Pharmacy Service.
Menjalankan: python demo_event_format.py
"""
import json
from datetime import datetime, timezone

# ── Data contoh (struktur sama dengan Resep.to_dict() / Obat.to_dict()) ──

RESEP_SAMPLE = {
    "id": 1,
    "nomor_resep": "RES-20240601-ABC123",
    "patient_id": "REG-001",
    "nama_pasien": "Budi Santoso",
    "dokter": "dr. Andi",
    "diagnosis": "Demam tifoid",
    "status": "selesai",
    "total_harga": 150000.0,
    "detail_resep": [
        {
            "id": 1,
            "resep_id": 1,
            "kode_obat": "OBT001",
            "nama_obat": "Paracetamol 500mg",
            "jumlah": 10,
            "aturan_pakai": "3x sehari sesudah makan",
            "harga_satuan": 500.0,
            "subtotal": 5000.0,
        }
    ],
    "created_at": datetime.now(timezone.utc).isoformat(),
    "updated_at": datetime.now(timezone.utc).isoformat(),
}

OBAT_SAMPLE = {
    "id": 1,
    "kode_obat": "OBT001",
    "nama_obat": "Paracetamol 500mg",
    "stok": 5,
    "satuan": "tablet",
    "harga": 500.0,
    "created_at": datetime.now(timezone.utc).isoformat(),
    "updated_at": datetime.now(timezone.utc).isoformat(),
}

PASIEN_TERDAFTAR_SAMPLE = {
    "event_type": "PASIEN_TERDAFTAR",
    "source": "registration-service",
    "data": {
        "patient_id": "REG-001",
        "nama_pasien": "Budi Santoso",
        "tanggal_lahir": "1990-05-15",
        "jenis_kelamin": "L",
    },
}


def build_pharmacy_outbound_events():
    """Format yang dikirim pharmacy-service (publisher.py)."""
    return [
        {
            "label": "Event 1: Resep selesai -> Billing",
            "exchange": "pharmacy_events",
            "exchange_type": "topic",
            "routing_key": "resep.selesai",
            "payload": {
                "event_type": "RESEP_SELESAI",
                "source": "pharmacy-service",
                "data": RESEP_SAMPLE,
            },
        },
        {
            "label": "Event 2: Stok menipis -> Pengadaan/Admin",
            "exchange": "pharmacy_events",
            "exchange_type": "topic",
            "routing_key": "stok.menipis",
            "payload": {
                "event_type": "STOK_MENIPIS",
                "source": "pharmacy-service",
                "data": OBAT_SAMPLE,
            },
        },
    ]


def build_pharmacy_inbound_event():
    """Format yang diterima pharmacy-service (consumer.py)."""
    return {
        "label": "Event masuk: Pasien terdaftar <- Registration",
        "exchange": "registration_events",
        "exchange_type": "topic",
        "routing_key": "pasien.terdaftar",
        "queue": "pharmacy_registration_queue",
        "payload": PASIEN_TERDAFTAR_SAMPLE,
    }


def main():
    print("=" * 60)
    print(" FORMAT EVENT - PHARMACY SERVICE (RabbitMQ / JSON )")
    print("=" * 60)

    for ev in build_pharmacy_outbound_events():
        print(f"\n### {ev['label']}")
        print(f"Exchange     : {ev['exchange']} ({ev['exchange_type']})")
        print(f"Routing Key  : {ev['routing_key']}")
        print("Body (JSON)  :")
        print(json.dumps(ev["payload"], indent=2, ensure_ascii=False))

    inbound = build_pharmacy_inbound_event()
    print(f"\n### {inbound['label']}")
    print(f"Exchange     : {inbound['exchange']} ({inbound['exchange_type']})")
    print(f"Routing Key  : {inbound['routing_key']}")
    print(f"Queue        : {inbound['queue']}")
    print("Body (JSON)  :")
    print(json.dumps(inbound["payload"], indent=2, ensure_ascii=False))

    print("\n" + "=" * 60)
    print(" Trigger API: PATCH /api/pharmacy/resep/{nomor}/selesai")
    print(" Trigger API: POST  /api/pharmacy/resep (stok <= minimum)")
    print("=" * 60)


if __name__ == "__main__":
    main()
