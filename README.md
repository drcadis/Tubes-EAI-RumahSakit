# Tubes-EAI-RumahSakit

Repositori ini berisi implementasi sistem Enterprise Application Integration (EAI) untuk simulasi Rumah Sakit, dengan menggunakan arsitektur microservices ter-containerize.

---

## Sistem yang Diintegrasikan

| Sistem | Framework | Database | Port | Status |
|---|---|---|---|---|
| Registrasi | FastAPI | PostgreSQL | 8001 | ✅ Selesai |
| Farmasi | Flask | MySQL | 8002 | 🔧 In Progress |
| Billing/Asuransi | Express.js | MongoDB | 8003 | ✅ Selesai |

---

## Bagian 1: Sistem Registrasi

Sistem Registrasi berfungsi sebagai pintu masuk utama pendaftaran pasien. Dibangun menggunakan FastAPI dan PostgreSQL, serta menggunakan RabbitMQ untuk mem-publish event secara asinkron ke sistem lain.

### Menjalankan Sistem Registrasi

```bash
docker compose up -d --build
```

Ini akan menjalankan 3 layanan:
1. `db_registrasi` (PostgreSQL) di port `5432`
2. `rabbitmq` di port `5672` (AMQP) dan `15672` (UI)
3. `registrasi_app` (FastAPI) di port `8001`

### Endpoint API

- Swagger Docs: `http://localhost:8001/docs`
- `POST /api/v1/patients` — Mendaftarkan pasien baru
- `GET /api/v1/patients` — Melihat daftar pasien

### Event yang Dipublish

Exchange: `hospital.events` | Routing Key: `patient.registered`

```json
{
  "event_id": "evt_987654321",
  "event_timestamp": "2026-06-03T19:45:00Z",
  "event_type": "PATIENT_REGISTERED",
  "data": {
    "patient_id": "REG-20260603-0001",
    "nik": "3201012345678901",
    "full_name": "Budi Santoso",
    "date_of_birth": "1990-05-15",
    "gender": "L",
    "contact_number": "081234567890",
    "address": "Jl. Merdeka No. 45, Jakarta",
    "blood_type": "O",
    "registration_type": "UMUM"
  }
}
```

---

## Bagian 2: Sistem Farmasi

*Dokumentasi menyusul.*

---

## Bagian 3: Sistem Billing/Asuransi

Sistem Billing berfungsi menerima event dari Registrasi dan Farmasi, lalu membuat tagihan secara otomatis untuk pasien.

### Menjalankan Sistem Billing

```bash
cd apps/billing
docker compose up -d --build
```

Ini akan menjalankan 3 layanan:
1. `mongo_billing` (MongoDB) di port `27017`
2. `rabbitmq` di port `5672` (AMQP) dan `15672` (UI)
3. `billing` (Express.js) di port `8003`

### Endpoint API

- `GET /health` — Cek status service
- `GET /api/v1/invoices` — Melihat semua tagihan
- `GET /api/v1/invoices/:patient_id` — Melihat tagihan berdasarkan patient_id
- `PATCH /api/v1/invoices/:patient_id/pay` — Update status tagihan menjadi PAID

### Event yang Dikonsumsi

Exchange: `hospital.events` | Routing Key: `patient.registered`

```json
{
  "event_id": "evt_987654321",
  "event_timestamp": "2026-06-03T19:45:00Z",
  "event_type": "PATIENT_REGISTERED",
  "data": {
    "patient_id": "REG-20260603-0001",
    "full_name": "Budi Santoso",
    "registration_type": "UMUM"
  }
}
```

### Event yang Akan Dikonsumsi (Menunggu Farmasi)

Exchange: `hospital.events` | Routing Key: `prescription.dispensed`

```json
{
  "event_type": "PRESCRIPTION_DISPENSED",
  "data": {
    "patient_id": "REG-20260603-0001",
    "medicines": [
      { "name": "Paracetamol", "price": 25000 }
    ],
    "total_price": 25000
  }
}
```