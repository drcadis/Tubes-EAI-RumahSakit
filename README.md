# Enterprise Application Integration (EAI) - Hospital System

Repositori ini berisi implementasi sistem **Enterprise Application Integration (EAI)** untuk simulasi Rumah Sakit, dengan menggunakan arsitektur microservices ter-containerize.

## Bagian 1: Sistem Registrasi (Telah Selesai)

Sistem Registrasi berfungsi sebagai pintu masuk utama pendaftaran pasien. Dibangun menggunakan **FastAPI** dan **PostgreSQL**, serta menggunakan **RabbitMQ** untuk mem-publish event secara asinkron ke sistem lain (seperti Rekam Medis dan Billing).

### Menjalankan Sistem Registrasi
Pastikan Docker telah terpasang, lalu jalankan perintah:
```bash
docker compose up -d --build
```
Ini akan menjalankan 3 layanan:
1. `db_registrasi` (PostgreSQL) di port `5432`
2. `rabbitmq` di port `5672` (AMQP) dan `15672` (UI)
3. `registrasi_app` (FastAPI) di port `8001`

### Endpoint API (Sistem Registrasi)
- **Swagger Docs:** `http://localhost:8001/docs`
- **POST /api/v1/patients:** Mendaftarkan pasien baru.
- **GET /api/v1/patients:** Melihat daftar pasien.

### Skema Data / Event Payload (Data Contract)
Setiap kali registrasi berhasil, sistem akan mengirimkan event JSON berikut ke RabbitMQ (Exchange: `hospital.events`, Routing Key: `patient.registered`):

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

*Catatan: Sistem Rekam Medis, Billing, dan Integration Layer akan di-push oleh anggota tim lainnya ke repositori ini.*
