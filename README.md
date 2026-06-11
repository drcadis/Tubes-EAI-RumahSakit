# Tubes-EAI-RumahSakit

# Enterprise Application Integration (EAI) - Hospital System

Repositori ini berisi implementasi sistem **Enterprise Application Integration (EAI)** untuk simulasi Rumah Sakit, dengan menggunakan arsitektur microservices ter-containerize.

## Bagian 1: Sistem Registrasi (Telah Selesai)

Sistem Registrasi berfungsi sebagai pintu masuk utama pendaftaran pasien. Dibangun menggunakan **FastAPI** dan **PostgreSQL**, serta menggunakan **RabbitMQ** untuk mem-publish event secara asinkron ke sistem lain (seperti Rekam Medis dan Billing).

### Menjalankan Sistem Registrasi
Pastikan Docker telah terpasang, lalu jalankan perintah:
```bash
docker compose up -d --build
```

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

### Endpoint API (Sistem Registrasi)
- **Swagger Docs:** `http://localhost:8001/docs`
- **POST /api/v1/patients:** Mendaftarkan pasien baru.
- **GET /api/v1/patients:** Melihat daftar pasien.

### Skema Data / Event Payload (Data Contract)
Setiap kali registrasi berhasil, sistem akan mengirimkan event JSON berikut ke RabbitMQ (Exchange: `hospital.events`, Routing Key: `patient.registered`):

### Endpoint API

- Swagger Docs: `http://localhost:8001/docs`
- `POST /api/v1/patients` — Mendaftarkan pasien baru
- `GET /api/v1/patients` — Melihat daftar pasien

### Event yang Dipublish

Exchange: `hospital.events` | Routing Key: `patient.registered`
>>>>>>> origin/feat/billing-service

```json
{
  "event_id": "evt_987654321",
  "event_timestamp": "2026-06-03T19:45:00Z",
  "event_type": "PATIENT_REGISTERED",gi
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

## Bagian 2: Sistem Farmasi

### Struktur File yang Sudah Dibuat

```
pharmacy-service/
├── app/
│   ├── __init__.py       # File kosong penanda ini adalah package Python
│   ├── models.py         # Definisi tabel database (Obat, Resep, DetailResep)
│   ├── routes.py         # Semua endpoint API
│   ├── publisher.py      # Kirim event ke RabbitMQ
│   ├── consumer.py       # Terima event dari RabbitMQ
│   └── factory.py        # Inisialisasi Flask app
├── main.py               # Entry point (titik masuk aplikasi)
├── requirements.txt      # Daftar library Python
├── Dockerfile            # Cara build image Docker
│
├── docker-compose.yml    # ← FILE INI DI ROOT PROJECT (bukan di dalam pharmacy-service)
├── .env.example          # Template konfigurasi environment variable
└── nginx/
    └── nginx.conf        # Konfigurasi API Gateway
```

---

### Penjelasan Tiap File

**`models.py` — Struktur Database**
Mendefinisikan 3 tabel MySQL:
- **Obat**: stok obat (kode, nama, stok, harga)
- **Resep**: data resep pasien
- **DetailResep**: item obat di dalam satu resep

**`routes.py` — API Endpoints**

| Method | URL | Fungsi |
|--------|-----|--------|
| GET | `/api/pharmacy/health` | Cek service hidup |
| GET | `/api/pharmacy/obat` | Daftar semua obat |
| GET | `/api/pharmacy/obat/{kode}` | Detail satu obat |
| POST | `/api/pharmacy/obat` | Tambah obat baru |
| PATCH | `/api/pharmacy/obat/{kode}/stok` | Update stok |
| GET | `/api/pharmacy/resep` | Daftar semua resep |
| GET | `/api/pharmacy/resep/{nomor}` | Detail satu resep |
| POST | `/api/pharmacy/resep` | Buat resep baru |
| PATCH | `/api/pharmacy/resep/{nomor}/selesai` | Selesaikan resep ← **Event trigger!** |

**`publisher.py` — Kirim Event ke RabbitMQ**
Pharmacy service MENGIRIM 2 jenis event:
- `resep.selesai` → dikonsumsi Billing Service (buat tagihan otomatis)
- `stok.menipis` → notifikasi ke admin

**`consumer.py` — Terima Event dari RabbitMQ**
Pharmacy service MENERIMA event:
- `pasien.terdaftar` dari Registration Service

---

### Alur End-to-End (Yang Wajib Didemonstrasikan)

```
[1] Pasien daftar di Registration Service
         ↓ (event: pasien.terdaftar)
    [RabbitMQ exchange: registration_events]
         ↓
[2] Pharmacy Service terima event (consumer.py)
    → Simpan info pasien untuk referensi resep

[3] Dokter buat resep via POST /api/pharmacy/resep
    → Stok obat berkurang otomatis

[4] Resep diselesaikan via PATCH /api/pharmacy/resep/{nomor}/selesai
         ↓ (event: resep.selesai)
    [RabbitMQ exchange: pharmacy_events]
         ↓
[5] Billing Service terima event → buat tagihan otomatis
```

---

### Cara Menjalankan

**1. Pindahkan docker-compose.yml ke root project**

Struktur folder project kamu seharusnya:
```
hospital-integration/          ← ROOT PROJECT
├── docker-compose.yml         ← pindahkan ke sini
├── .env                       ← salin dari .env.example
├── nginx/
│   └── nginx.conf
├── registration-service/      ← sudah kamu buat
├── pharmacy-service/          ← yang baru dibuat
├── medical-service/           ← belum dibuat
└── integration-layer/         ← belum dibuat
```

**2. Salin file .env**
```bash
cp .env.example .env
```

**3. Jalankan semua service**
```bash
docker compose up --build
```

**4. Test Pharmacy Service**
```bash
# Cek service hidup
curl http://localhost:5001/api/pharmacy/health

# Lihat daftar obat
curl http://localhost:5001/api/pharmacy/obat

# Buat resep baru
curl -X POST http://localhost:5001/api/pharmacy/resep \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": "REG-001",
    "nama_pasien": "Budi Santoso",
    "dokter": "dr. Andi",
    "diagnosis": "Demam tifoid",
    "obat_list": [
      {
        "kode_obat": "OBT001",
        "jumlah": 10,
        "aturan_pakai": "3x sehari sesudah makan"
      }
    ]
  }'

# Selesaikan resep (ini yang trigger event ke Billing)
curl -X PATCH http://localhost:5001/api/pharmacy/resep/RES-20240601-XXXXXX/selesai
```

**5. Monitor RabbitMQ**
Buka browser: http://localhost:15672
- Username: guest
- Password: guest

---

### EIP Patterns yang Diterapkan di Service Ini

| Pattern | Di mana? |
|---------|---------|
| **Message Channel** | Exchange `pharmacy_events` dan `registration_events` di RabbitMQ |
| **Message Translator** | `consumer.py` parse JSON dari broker, transform ke object Python |
| **Publish-Subscribe** | Event `resep.selesai` bisa dikonsumsi banyak subscriber (Billing, dll) |
| **Dead Letter Queue** | Konfigurasi `x-dead-letter-exchange` di `consumer.py` |
| **Content-Based Router** | `routing_key` di publisher menentukan siapa yang terima event |

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
