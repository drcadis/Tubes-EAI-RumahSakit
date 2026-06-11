from flask import Flask
from flask_cors import CORS
from flasgger import Swagger
from .models import db, Obat
from .routes import pharmacy_bp
from .errors import register_error_handlers
from .consumer import start_consumer
from .swagger_config import SWAGGER_TEMPLATE, SWAGGER_CONFIG
import os
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)


def create_app():
    app = Flask(__name__)
    CORS(app)

    # ── Konfigurasi dari Environment Variable ──────────────────────────────
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
        'DATABASE_URL',
        'mysql+pymysql://pharmacy_user:pharmacy_pass@mysql_pharmacy:3306/pharmacy_db'
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')

    # ── Init SQLAlchemy ─────────────────────────────────────────────────────
    db.init_app(app)

    # ── Daftarkan Blueprint routes ──────────────────────────────────────────
    app.register_blueprint(pharmacy_bp, url_prefix='/api/pharmacy')

    # ── Daftarkan Swagger (harus setelah blueprint) ─────────────────────────
    # Akses di: http://localhost:5001/apidocs
    Swagger(app, template=SWAGGER_TEMPLATE, config=SWAGGER_CONFIG)

    # ── Daftarkan global error handler ─────────────────────────────────────
    register_error_handlers(app)

    # ── Buat tabel database dan isi data awal ───────────────────────────────
    with app.app_context():
        db.create_all()
        _seed_data()

    # ── Jalankan consumer RabbitMQ di background thread ─────────────────────
    start_consumer()

    return app


def _seed_data():
    """Isi data obat awal jika database masih kosong"""
    if Obat.query.count() == 0:
        obat_awal = [
            Obat(kode_obat='OBT001', nama_obat='Paracetamol 500mg',  stok=200, satuan='tablet',  harga=500),
            Obat(kode_obat='OBT002', nama_obat='Amoxicillin 500mg',  stok=150, satuan='kapsul',  harga=2000),
            Obat(kode_obat='OBT003', nama_obat='Omeprazole 20mg',    stok=100, satuan='kapsul',  harga=3000),
            Obat(kode_obat='OBT004', nama_obat='Cetirizine 10mg',    stok=80,  satuan='tablet',  harga=1500),
            Obat(kode_obat='OBT005', nama_obat='ORS / Oralit',       stok=50,  satuan='sachet',  harga=1000),
            Obat(kode_obat='OBT006', nama_obat='Antasida Suspensi',  stok=30,  satuan='botol',   harga=8000),
        ]
        db.session.add_all(obat_awal)
        db.session.commit()
        logging.getLogger(__name__).info("[SEED] Data obat awal berhasil dimasukkan")
