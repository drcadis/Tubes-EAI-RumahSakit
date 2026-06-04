"""
Konfigurasi Swagger (OpenAPI 2.0) untuk Pharmacy Service.
File ini berisi template dan spec lengkap semua endpoint API.

Diakses di: http://localhost:5001/apidocs
atau lewat gateway: http://localhost/api/pharmacy/apidocs
"""

# ── Template dasar Swagger ─────────────────────────────────────────────────
SWAGGER_TEMPLATE = {
    "swagger": "2.0",
    "info": {
        "title": "Pharmacy Service API",
        "description": """
## 🏥 API Layanan Farmasi — Sistem Integrasi Rumah Sakit

Service ini mengelola:
- **Stok Obat**: tambah, lihat, update stok
- **Resep**: buat resep pasien, proses, dan selesaikan

### Integrasi dengan Sistem Lain
- Menerima event `pasien.terdaftar` dari **Registrasi Service** via RabbitMQ
- Mengirim event `resep.selesai` ke **Billing Service** via RabbitMQ
- Mengirim event `stok.menipis` ke sistem pengadaan via RabbitMQ

### EIP Patterns yang Diterapkan
- **Message Channel**: exchange `pharmacy_events` di RabbitMQ
- **Publish-Subscribe**: event resep.selesai dapat dikonsumsi banyak subscriber
- **Dead Letter Queue**: pesan gagal masuk ke antrian DLX
        """,
        "version": "1.0.0",
        "contact": {
            "name": "Tim Integrasi Rumah Sakit"
        }
    },
    "basePath": "/api/pharmacy",
    "schemes": ["http"],
    "consumes": ["application/json"],
    "produces": ["application/json"],

    # ── Definisi model/skema data (dipakai ulang di banyak endpoint) ────────
    "definitions": {

        "Obat": {
            "type": "object",
            "properties": {
                "id":         {"type": "integer", "example": 1},
                "kode_obat":  {"type": "string",  "example": "OBT001"},
                "nama_obat":  {"type": "string",  "example": "Paracetamol 500mg"},
                "stok":       {"type": "integer", "example": 200},
                "satuan":     {"type": "string",  "example": "tablet"},
                "harga":      {"type": "number",  "example": 500.0},
                "created_at": {"type": "string",  "example": "2024-06-01T10:00:00"},
                "updated_at": {"type": "string",  "example": "2024-06-01T10:00:00"}
            }
        },

        "ObatInput": {
            "type": "object",
            "required": ["kode_obat", "nama_obat", "stok", "harga"],
            "properties": {
                "kode_obat": {"type": "string",  "example": "OBT007"},
                "nama_obat": {"type": "string",  "example": "Ibuprofen 400mg"},
                "stok":      {"type": "integer", "example": 100},
                "satuan":    {"type": "string",  "example": "tablet", "default": "tablet"},
                "harga":     {"type": "number",  "example": 1500.0}
            }
        },

        "UpdateStokInput": {
            "type": "object",
            "required": ["jumlah", "operasi"],
            "properties": {
                "jumlah":  {"type": "integer", "example": 50},
                "operasi": {
                    "type": "string",
                    "enum": ["tambah", "kurangi"],
                    "example": "tambah"
                }
            }
        },

        "DetailResepInput": {
            "type": "object",
            "required": ["kode_obat", "jumlah"],
            "properties": {
                "kode_obat":   {"type": "string",  "example": "OBT001"},
                "jumlah":      {"type": "integer", "example": 10},
                "aturan_pakai":{"type": "string",  "example": "3x sehari sesudah makan"}
            }
        },

        "ResepInput": {
            "type": "object",
            "required": ["patient_id", "nama_pasien", "dokter", "obat_list"],
            "properties": {
                "patient_id":  {"type": "string", "example": "REG-20240601-ABC123"},
                "nama_pasien": {"type": "string", "example": "Budi Santoso"},
                "dokter":      {"type": "string", "example": "dr. Andi Wijaya, Sp.PD"},
                "diagnosis":   {"type": "string", "example": "Demam tifoid"},
                "obat_list": {
                    "type": "array",
                    "items": {"$ref": "#/definitions/DetailResepInput"}
                }
            }
        },

        "DetailResep": {
            "type": "object",
            "properties": {
                "id":           {"type": "integer", "example": 1},
                "resep_id":     {"type": "integer", "example": 1},
                "kode_obat":    {"type": "string",  "example": "OBT001"},
                "nama_obat":    {"type": "string",  "example": "Paracetamol 500mg"},
                "jumlah":       {"type": "integer", "example": 10},
                "aturan_pakai": {"type": "string",  "example": "3x sehari sesudah makan"},
                "harga_satuan": {"type": "number",  "example": 500.0},
                "subtotal":     {"type": "number",  "example": 5000.0}
            }
        },

        "Resep": {
            "type": "object",
            "properties": {
                "id":           {"type": "integer", "example": 1},
                "nomor_resep":  {"type": "string",  "example": "RES-20240601-ABC123"},
                "patient_id":   {"type": "string",  "example": "REG-20240601-XYZ"},
                "nama_pasien":  {"type": "string",  "example": "Budi Santoso"},
                "dokter":       {"type": "string",  "example": "dr. Andi"},
                "diagnosis":    {"type": "string",  "example": "Demam tifoid"},
                "status": {
                    "type": "string",
                    "enum": ["pending", "diproses", "selesai"],
                    "example": "pending"
                },
                "total_harga":  {"type": "number",  "example": 25000.0},
                "detail_resep": {
                    "type": "array",
                    "items": {"$ref": "#/definitions/DetailResep"}
                },
                "created_at":   {"type": "string",  "example": "2024-06-01T10:00:00"},
                "updated_at":   {"type": "string",  "example": "2024-06-01T10:00:00"}
            }
        },

        "SuccessResponse": {
            "type": "object",
            "properties": {
                "status":  {"type": "string", "example": "success"},
                "message": {"type": "string", "example": "Operasi berhasil"},
                "data":    {"type": "object"}
            }
        },

        "ErrorResponse": {
            "type": "object",
            "properties": {
                "status": {"type": "string", "example": "error"},
                "kode":   {"type": "integer", "example": 404},
                "pesan":  {"type": "string",  "example": "Data tidak ditemukan"}
            }
        }
    }
}

# ── Konfigurasi tampilan Swagger UI ───────────────────────────────────────
SWAGGER_CONFIG = {
    "headers": [],
    "specs": [
        {
            "endpoint": "apispec",
            "route": "/apispec.json",
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/apidocs"   # URL untuk buka Swagger UI
}
