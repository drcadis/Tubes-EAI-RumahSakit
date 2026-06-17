# Tubes-EAI-RumahSakit

# Enterprise Application Integration (EAI) - Hospital System

Repositori ini berisi implementasi sistem **Enterprise Application Integration (EAI)** untuk simulasi Rumah Sakit, dengan menggunakan arsitektur microservices ter-containerize.

---

## Sistem yang Diintegrasikan

| Sistem | Framework | Database | Port | Status |
|---|---|---|---|---|
| **Registrasi** | FastAPI | PostgreSQL | 8001 | ✅ Selesai |
| **Farmasi** | Flask | MySQL | 5001 | ✅ Selesai |
| **Billing/Asuransi** | Express.js | MongoDB | 8003 | ✅ Selesai |
| **Dashboard UI** | Nginx (Static HTML) | - | 8080 | ✅ Selesai |
| **RabbitMQ** | Message Broker | - | 5672 / 15672 | ✅ Selesai |

---

## Cara Menjalankan Sistem

Seluruh sistem (semua microservices, database, dan message broker) telah dikonfigurasi dalam satu file `docker-compose.yml` di root direktori.

Pastikan Docker telah terpasang dan berjalan, lalu jalankan perintah berikut di root direktori proyek (`Tubes_Eai`):

```bash
docker-compose up -d --build
```

Ini akan menjalankan semua container yang dibutuhkan. Anda dapat mengakses layanan melalui port berikut:
- **EAI Dashboard**: `http://localhost:8080`
- **RabbitMQ Dashboard**: `http://localhost:15672` (username: `guest`, password: `guest`)
- **Registrasi API (Swagger)**: `http://localhost:8001/docs`

---

## Alur Integrasi (End-to-End)

Proyek ini menerapkan beberapa EIP (Enterprise Integration Patterns) seperti *Message Channel*, *Publish-Subscribe*, dan *Message Translator*.

1. **Registrasi Pasien**
   - Pasien mendaftar melalui Registration Service.
   - Event `patient.registered` diterbitkan ke RabbitMQ (Exchange: `hospital.events`).
2. **Distribusi Event**
   - **Billing Service** menerima event `patient.registered` dan otomatis membuat tagihan awal/data pasien.
   - **Integration Layer** menerjemahkan event ini menjadi `pasien.terdaftar` untuk dikonsumsi oleh sistem Farmasi (Exchange: `registration_events`).
3. **Proses Farmasi**
   - Dokter membuat resep. Jika resep diselesaikan, stok obat otomatis berkurang.
   - Event `resep.selesai` diterbitkan ke RabbitMQ (Exchange: `pharmacy_events`).
4. **Pembaharuan Tagihan**
   - **Billing Service** menerima event `resep.selesai` dan memperbarui total tagihan pasien secara otomatis.

---

## Rincian Microservices

### 1. Sistem Registrasi (Port 8001)
Berfungsi sebagai pintu masuk utama pendaftaran pasien.
- **POST /api/v1/patients:** Mendaftarkan pasien baru (memicu event `patient.registered`).
- **GET /api/v1/patients:** Melihat daftar pasien.

**Event Payload (`patient.registered`):**
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

### 2. Sistem Farmasi (Port 5001)
Mengelola stok obat dan resep pasien.
- **GET /api/pharmacy/obat:** Daftar semua obat.
- **POST /api/pharmacy/resep:** Buat resep baru (mengurangi stok).
- **PATCH /api/pharmacy/resep/{nomor}/selesai:** Menyelesaikan resep (memicu event `resep.selesai`).

### 3. Sistem Billing/Asuransi (Port 8003)
Menerima event dari Registrasi dan Farmasi untuk membuat/memperbarui tagihan.
- **GET /api/v1/invoices:** Melihat semua tagihan.
- **GET /api/v1/invoices/:patient_id:** Melihat tagihan berdasarkan ID pasien.
- **PATCH /api/v1/invoices/:patient_id/pay:** Update status tagihan menjadi `PAID`.

---

## Pola Enterprise Integration (EIP) yang Diterapkan

Sistem ini dirancang menggunakan beberapa arsitektur *Enterprise Integration Patterns* utama:

| Pola EIP | Implementasi pada Sistem |
|---|---|
| **Publish-Subscribe Channel** | Saat event seperti `patient.registered` atau `resep.selesai` dikirimkan, event tersebut tidak ditujukan ke satu layanan spesifik. Berbagai layanan lain (seperti *Billing* atau *Integration Layer*) berlangganan dan dapat mengkonsumsinya secara independen tanpa membebani layanan asal (Registrasi/Farmasi). |
| **Message Channel** | Penggunaan pertukaran pesan asinkron melalui RabbitMQ (Exchange: `hospital.events`, `pharmacy_events`, `registration_events`) berfungsi sebagai Message Channel yang menghubungkan berbagai aplikasi yang berbeda. |
| **Message Translator** | Terdapat *Integration Layer* yang berfungsi menangkap event asli (misal `patient.registered` dari *hospital.events*), memformat atau menerjemahkannya jika perlu, lalu meneruskannya kembali dengan *routing key* atau tipe yang berbeda (misal `pasien.terdaftar` ke *registration_events*) agar kompatibel dengan sistem Farmasi. |
| **Content-Based Router (via Routing Key)** | RabbitMQ bertindak merutekan pesan ke antrian yang tepat berdasarkan *Routing Key* yang disematkan pada event tersebut. Hanya antrian (queue) yang di-*bind* dengan key yang cocok yang akan menerima pesannya. |
