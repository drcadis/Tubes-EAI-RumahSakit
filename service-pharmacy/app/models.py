from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Obat(db.Model):
    """Model untuk stok obat di farmasi"""
    __tablename__ = 'obat'

    id          = db.Column(db.Integer, primary_key=True)
    kode_obat   = db.Column(db.String(20), unique=True, nullable=False)
    nama_obat   = db.Column(db.String(100), nullable=False)
    stok        = db.Column(db.Integer, default=0)
    satuan      = db.Column(db.String(20), default='tablet')  # tablet, kapsul, botol, dll
    harga       = db.Column(db.Float, default=0.0)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at  = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "kode_obat": self.kode_obat,
            "nama_obat": self.nama_obat,
            "stok": self.stok,
            "satuan": self.satuan,
            "harga": self.harga,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


class Resep(db.Model):
    """Model untuk resep obat pasien"""
    __tablename__ = 'resep'

    id              = db.Column(db.Integer, primary_key=True)
    nomor_resep     = db.Column(db.String(50), unique=True, nullable=False)
    patient_id      = db.Column(db.String(50), nullable=False)   # ID dari sistem Registrasi
    nama_pasien     = db.Column(db.String(100), nullable=False)
    dokter          = db.Column(db.String(100), nullable=False)
    diagnosis       = db.Column(db.Text, nullable=True)
    status          = db.Column(db.String(20), default='pending') # pending, diproses, selesai
    total_harga     = db.Column(db.Float, default=0.0)
    created_at      = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at      = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relasi ke detail resep
    detail_resep    = db.relationship('DetailResep', backref='resep', lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "nomor_resep": self.nomor_resep,
            "patient_id": self.patient_id,
            "nama_pasien": self.nama_pasien,
            "dokter": self.dokter,
            "diagnosis": self.diagnosis,
            "status": self.status,
            "total_harga": self.total_harga,
            "detail_resep": [d.to_dict() for d in self.detail_resep],
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


class DetailResep(db.Model):
    """Model untuk detail item obat dalam satu resep"""
    __tablename__ = 'detail_resep'

    id          = db.Column(db.Integer, primary_key=True)
    resep_id    = db.Column(db.Integer, db.ForeignKey('resep.id'), nullable=False)
    kode_obat   = db.Column(db.String(20), nullable=False)
    nama_obat   = db.Column(db.String(100), nullable=False)
    jumlah      = db.Column(db.Integer, nullable=False)
    aturan_pakai = db.Column(db.String(100), nullable=True)  # "3x sehari sesudah makan"
    harga_satuan = db.Column(db.Float, default=0.0)
    subtotal    = db.Column(db.Float, default=0.0)

    def to_dict(self):
        return {
            "id": self.id,
            "resep_id": self.resep_id,
            "kode_obat": self.kode_obat,
            "nama_obat": self.nama_obat,
            "jumlah": self.jumlah,
            "aturan_pakai": self.aturan_pakai,
            "harga_satuan": self.harga_satuan,
            "subtotal": self.subtotal
        }
