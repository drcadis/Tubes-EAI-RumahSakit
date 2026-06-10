# Pharmacy Service — Panduan Lengkap

## Struktur File yang Sudah Dibuat

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

## Penjelasan Tiap File

### `models.py` — Struktur Database
Mendefinisikan 3 tabel MySQL:
- **Obat**: stok obat (kode, nama, stok, harga)
- **Resep**: data resep pasien
- **DetailResep**: item obat di dalam satu resep

### `routes.py` — API Endpoints

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

### `publisher.py` — Kirim Event ke RabbitMQ
Pharmacy service MENGIRIM 2 jenis event:
- `resep.selesai` → dikonsumsi Billing Service (buat tagihan otomatis)
- `stok.menipis` → notifikasi ke admin

### `consumer.py` — Terima Event dari RabbitMQ
Pharmacy service MENERIMA event:
- `pasien.terdaftar` dari Registration Service

---

## Alur End-to-End (Yang Wajib Didemonstrasikan)

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

## Cara Menjalankan

### 1. Pindahkan docker-compose.yml ke root project

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

### 2. Salin file .env
```bash
cp .env.example .env
```

### 3. Jalankan semua service
```bash
docker compose up --build
```

### 4. Test Pharmacy Service
```bash
# Cek service hidup
curl http://localhost/api/pharmacy/health

# Lihat daftar obat
curl http://localhost/api/pharmacy/obat

# Buat resep baru
curl -X POST http://localhost/api/pharmacy/resep \
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
curl -X PATCH http://localhost/api/pharmacy/resep/RES-20240601-XXXXXX/selesai
```

### 5. Monitor RabbitMQ
Buka browser: http://localhost:15672
- Username: admin
- Password: admin123

---

## EIP Patterns yang Diterapkan di Service Ini

| Pattern | Di mana? |
|---------|---------|
| **Message Channel** | Exchange `pharmacy_events` dan `registration_events` di RabbitMQ |
| **Message Translator** | `consumer.py` parse JSON dari broker, transform ke object Python |
| **Publish-Subscribe** | Event `resep.selesai` bisa dikonsumsi banyak subscriber (Billing, dll) |
| **Dead Letter Queue** | Konfigurasi `x-dead-letter-exchange` di `consumer.py` |
| **Content-Based Router** | `routing_key` di publisher menentukan siapa yang terima event |
