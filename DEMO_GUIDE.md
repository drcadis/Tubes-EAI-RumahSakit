# 📺 Skenario & Panduan Video Demo - Hospital EAI System

Panduan ini berisi skenario perekaman video demo berdurasi **7-10 menit** yang dirancang khusus untuk memperlihatkan bahwa semua poin penilaian dari instruksi Tugas Besar (UAS) telah terpenuhi.

---

## 📋 Persiapan Sebelum Merekam

1. **Bersihkan Data Lama:** Buka terminal di root project dan jalankan `docker-compose down -v` agar database kosong dan video mendemonstrasikan sistem dari nol.
2. **Gladi Bersih:** Praktikkan pindah-pindah tab browser terlebih dahulu agar video berjalan lancar.
3. **Buka Tab Browser yang Dibutuhkan:**
   - Swagger Registrasi: `http://localhost:8001/docs`
   - Swagger Farmasi: `http://localhost:5001/apidocs`
   - Swagger Billing: `http://localhost:8003/api-docs` *(Sesuaikan bila perlu)*
   - RabbitMQ UI: `http://localhost:15672` (Username: `guest`, Password: `guest`)

---

## 🎬 Skenario Rekaman Video (Target 7 Menit)

### Scene 1: Pengenalan & Arsitektur (⏱️ 0:00 - 1:00)
- **Visual:** Tampilkan README.md utama atau diagram arsitektur.
- **Audio/Narasi:** 
  > "Halo, kami dari [Nama Kelompok]. Ini adalah proyek Enterprise Application Integration (EAI) kami dengan tema Sistem Rumah Sakit. Kami mengintegrasikan 3 aplikasi terpisah: **Registrasi** (FastAPI/PostgreSQL), **Farmasi** (Flask/MySQL), dan **Billing/Asuransi** (Express.js/MongoDB). Arsitektur kami menggunakan komunikasi asinkron melalui **RabbitMQ** sebagai Message Broker."

### Scene 2: Menjalankan Sistem (Containerization) (⏱️ 1:00 - 2:00)
- **Visual:** Terminal di root folder project. Ketik perintah docker.
- **Aksi:** Jalankan `docker-compose up -d --build`. Tunjukkan hasilnya menggunakan `docker-compose ps`.
- **Audio/Narasi:** 
  > "Setiap service memiliki Dockerfile masing-masing dan diorkestrasi menggunakan Docker Compose. Hanya dengan satu perintah, seluruh microservices, database, dan RabbitMQ langsung menyala di network yang sama tanpa ada aplikasi yang memanggil database milik aplikasi lain secara langsung (Zero direct DB access)."

### Scene 3: Registrasi Pasien (End-to-End Alur 1) (⏱️ 2:00 - 3:30)
- **Visual:** Buka Swagger Registrasi (`http://localhost:8001/docs`).
- **Aksi:** Lakukan `POST /api/v1/patients`. Masukkan JSON pasien (Nama: Budi Santoso, NIK, dll). Tekan **Execute**.
- **Audio/Narasi:** 
  > "Sekarang kita mulai alur integrasinya. Pasien Budi mendaftar melalui API Registrasi. Saat berhasil disimpan ke database PostgreSQL, Registrasi tidak melakukan panggilan REST API ke service lain. Ia sepenuhnya *loosely-coupled* dan hanya mem-publish event `patient.registered` ke RabbitMQ."

### Scene 4: Bukti Pola EIP - Message Translator (⏱️ 3:30 - 4:30)
- **Visual:** Buka RabbitMQ Management UI (`http://localhost:15672`). Tunjukkan Exchange `hospital.events` dan queue yang ada.
- **Audio/Narasi:** 
  > "Di sinilah letak penerapan Enterprise Integration Patterns (EIP). Registrasi mem-publish payload menggunakan field bahasa Inggris (seperti `full_name`). Namun sistem Farmasi kami dirancang memakai bahasa Indonesia. Oleh karena itu, kami menyertakan komponen **Integration Layer** yang bertindak sebagai **Message Translator**. Layanan ini menerjemahkan field JSON tersebut secara *on-the-fly* untuk dikonsumsi sistem lain. Ini adalah penanganan heterogenitas pada level skema data."

### Scene 5: Auto Invoice di Billing Service (⏱️ 4:30 - 5:30)
- **Visual:** Buka Swagger Billing. Lakukan request `GET /api/v1/invoices` atau cek tagihan.
- **Aksi:** Tunjukkan bahwa invoice atas nama Budi muncul dan berstatus `UNPAID` tanpa ada klik apapun di billing.
- **Audio/Narasi:** 
  > "Sebagai implementasi **Publish-Subscribe** dan **Message Endpoint**, Billing Service secara otomatis mendengarkan event Registrasi. Bisa dilihat, tanpa intervensi manual, sistem Billing langsung membuatkan Invoice berstatus UNPAID untuk pasien Budi."

### Scene 6: Integrasi Farmasi & Pembaruan Tagihan (⏱️ 5:30 - 6:30)
- **Visual:** Buka Swagger Farmasi (`http://localhost:5001/apidocs`). 
- **Aksi:** Lakukan pendaftaran resep atau *patch* selesaikan resep untuk Budi. Kemudian, kembali ke Swagger Billing dan refresh tagihan Budi.
- **Audio/Narasi:** 
  > "Langkah selanjutnya, Budi mengambil obat di Farmasi. Saat Resep diproses dan selesai, Farmasi mem-publish event asinkron ke broker. Secara real-time, jika kita me-refresh tagihan di sistem Billing, otomatis harga obat sudah diakumulasi ke dalam tagihan Budi. Tiga sistem yang tadinya silo kini terhubung dengan otomatis."

### Scene 7: Kejutan Transformasi XML (⏱️ 6:30 - 7:30)
- **Visual:** Tunjukkan potongan kode pada file `apps/billing/src/publishers/invoicePublisher.js` atau tunjukkan log terminal Billing.
- **Audio/Narasi:**
  > "Untuk sepenuhnya mendemonstrasikan heterogenitas pertukaran format data pada level Enterprise, Billing Service kami akan menerbitkan event baru setelah invoice diperbarui. Sebelum dikirim, sistem kami mentransformasi objek JSON menjadi format **XML** (menggunakan pustaka xml2js), lalu mem-publish event tersebut dengan tipe application/xml ke dalam RabbitMQ. Ini menegaskan kemampuan sistem kami menangani format payload lintas sistem. Sekian demo dari kelompok kami, terima kasih!"

---

## 📝 Rekap Checklist Penilaian yang Ditunjukkan di Video:
- ✅ **Minimal 3 Aplikasi (Heterogen)**: Ditunjukkan (FastAPI, Flask, Express.js / Postgres, MySQL, MongoDB).
- ✅ **Mekanisme Integrasi**: Ditunjukkan (Integrasi Asinkron via antrian RabbitMQ).
- ✅ **Containerization**: Ditunjukkan (Saat melakukan perintah `docker-compose up`).
- ✅ **Alur End-to-End**: Ditunjukkan (Registrasi Event -> Update Invoice Farmasi -> Update Tagihan Billing).
- ✅ **Pola EIP (Minimal 3)**: Message Channel (RabbitMQ), Message Endpoint (Node Consumer), Publish-Subscribe, dan Message Translator.
- ✅ **Transformasi Data/Heterogenitas**: 
  1. Transformasi skema/field (Integration layer menerjemahkan Inggris ke Indonesia). 
  2. Transformasi Format (Billing mem-publish payload dalam format XML).
