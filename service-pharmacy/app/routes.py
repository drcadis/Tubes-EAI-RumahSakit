from flask import Blueprint, request, jsonify
from .models import db, Obat, Resep, DetailResep
from .publisher import publish_resep_selesai, publish_stok_menipis
from datetime import datetime
import uuid

pharmacy_bp = Blueprint('pharmacy', __name__)

STOK_MINIMUM = 10  # Batas minimum stok sebelum kirim alert


# ══════════════════════════════════════════════
#  HEALTH CHECK
# ══════════════════════════════════════════════

@pharmacy_bp.route('/health', methods=['GET'])
def health_check():
    """
    Cek status service
    ---
    tags:
      - Utilitas
    summary: Health check pharmacy service
    responses:
      200:
        description: Service berjalan normal
        schema:
          type: object
          properties:
            status:
              type: string
              example: ok
            service:
              type: string
              example: pharmacy-service
    """
    return jsonify({"status": "ok", "service": "pharmacy-service"}), 200


# ══════════════════════════════════════════════
#  OBAT — CRUD stok obat
# ══════════════════════════════════════════════

@pharmacy_bp.route('/obat', methods=['GET'])
def get_all_obat():
    """
    Ambil semua daftar obat
    ---
    tags:
      - Obat
    summary: Daftar seluruh obat di stok farmasi
    responses:
      200:
        description: Daftar obat berhasil diambil
        schema:
          type: object
          properties:
            status:
              type: string
              example: success
            total:
              type: integer
              example: 6
            data:
              type: array
              items:
                $ref: '#/definitions/Obat'
    """
    obat_list = Obat.query.all()
    return jsonify({
        "status": "success",
        "total": len(obat_list),
        "data": [o.to_dict() for o in obat_list]
    }), 200


@pharmacy_bp.route('/obat/<string:kode_obat>', methods=['GET'])
def get_obat(kode_obat):
    """
    Ambil detail satu obat
    ---
    tags:
      - Obat
    summary: Detail obat berdasarkan kode obat
    parameters:
      - name: kode_obat
        in: path
        type: string
        required: true
        description: Kode unik obat
        example: OBT001
    responses:
      200:
        description: Detail obat ditemukan
        schema:
          type: object
          properties:
            status:
              type: string
              example: success
            data:
              $ref: '#/definitions/Obat'
      404:
        description: Obat tidak ditemukan
        schema:
          $ref: '#/definitions/ErrorResponse'
    """
    obat = Obat.query.filter_by(kode_obat=kode_obat).first()
    if not obat:
        return jsonify({"status": "error", "kode": 404, "pesan": "Obat tidak ditemukan"}), 404
    return jsonify({"status": "success", "data": obat.to_dict()}), 200


@pharmacy_bp.route('/obat', methods=['POST'])
def tambah_obat():
    """
    Tambah obat baru ke stok
    ---
    tags:
      - Obat
    summary: Tambahkan obat baru ke database farmasi
    parameters:
      - name: body
        in: body
        required: true
        schema:
          $ref: '#/definitions/ObatInput'
    responses:
      201:
        description: Obat berhasil ditambahkan
        schema:
          type: object
          properties:
            status:
              type: string
              example: success
            message:
              type: string
              example: Obat berhasil ditambahkan
            data:
              $ref: '#/definitions/Obat'
      400:
        description: Field wajib tidak lengkap
        schema:
          $ref: '#/definitions/ErrorResponse'
      409:
        description: Kode obat sudah ada
        schema:
          $ref: '#/definitions/ErrorResponse'
    """
    body = request.get_json()
    if not body:
        return jsonify({"status": "error", "kode": 400, "pesan": "Body JSON kosong"}), 400

    required = ['kode_obat', 'nama_obat', 'stok', 'harga']
    for field in required:
        if field not in body:
            return jsonify({"status": "error", "kode": 400, "pesan": f"Field '{field}' wajib diisi"}), 400

    if Obat.query.filter_by(kode_obat=body['kode_obat']).first():
        return jsonify({"status": "error", "kode": 409, "pesan": "Kode obat sudah ada"}), 409

    obat = Obat(
        kode_obat=body['kode_obat'],
        nama_obat=body['nama_obat'],
        stok=body['stok'],
        satuan=body.get('satuan', 'tablet'),
        harga=body['harga']
    )
    db.session.add(obat)
    db.session.commit()

    return jsonify({
        "status": "success",
        "message": "Obat berhasil ditambahkan",
        "data": obat.to_dict()
    }), 201


@pharmacy_bp.route('/obat/<string:kode_obat>/stok', methods=['PATCH'])
def update_stok(kode_obat):
    """
    Update stok obat
    ---
    tags:
      - Obat
    summary: Tambah atau kurangi stok obat
    description: |
      Gunakan operasi **tambah** untuk menambah stok (misalnya saat terima kiriman obat),
      dan operasi **kurangi** untuk mengurangi stok manual.
      
      Pengurangan stok otomatis terjadi saat resep dibuat.
    parameters:
      - name: kode_obat
        in: path
        type: string
        required: true
        example: OBT001
      - name: body
        in: body
        required: true
        schema:
          $ref: '#/definitions/UpdateStokInput'
    responses:
      200:
        description: Stok berhasil diperbarui
        schema:
          type: object
          properties:
            status:
              type: string
              example: success
            message:
              type: string
              example: Stok diperbarui
            data:
              $ref: '#/definitions/Obat'
      400:
        description: Stok tidak mencukupi atau operasi tidak valid
        schema:
          $ref: '#/definitions/ErrorResponse'
      404:
        description: Obat tidak ditemukan
        schema:
          $ref: '#/definitions/ErrorResponse'
    """
    obat = Obat.query.filter_by(kode_obat=kode_obat).first()
    if not obat:
        return jsonify({"status": "error", "kode": 404, "pesan": "Obat tidak ditemukan"}), 404

    body = request.get_json()
    jumlah  = body.get('jumlah', 0)
    operasi = body.get('operasi', 'tambah')

    if operasi == 'tambah':
        obat.stok += jumlah
    elif operasi == 'kurangi':
        if obat.stok < jumlah:
            return jsonify({"status": "error", "kode": 400, "pesan": "Stok tidak mencukupi"}), 400
        obat.stok -= jumlah
    else:
        return jsonify({"status": "error", "kode": 400, "pesan": "Operasi tidak valid (tambah/kurangi)"}), 400

    db.session.commit()

    if obat.stok <= STOK_MINIMUM:
        publish_stok_menipis(obat.to_dict())

    return jsonify({
        "status": "success",
        "message": "Stok diperbarui",
        "data": obat.to_dict()
    }), 200


# ══════════════════════════════════════════════
#  RESEP — Buat dan proses resep
# ══════════════════════════════════════════════

@pharmacy_bp.route('/resep', methods=['GET'])
def get_all_resep():
    """
    Ambil semua resep
    ---
    tags:
      - Resep
    summary: Daftar seluruh resep pasien
    responses:
      200:
        description: Daftar resep berhasil diambil
        schema:
          type: object
          properties:
            status:
              type: string
              example: success
            total:
              type: integer
              example: 3
            data:
              type: array
              items:
                $ref: '#/definitions/Resep'
    """
    resep_list = Resep.query.all()
    return jsonify({
        "status": "success",
        "total": len(resep_list),
        "data": [r.to_dict() for r in resep_list]
    }), 200


@pharmacy_bp.route('/resep/<string:nomor_resep>', methods=['GET'])
def get_resep(nomor_resep):
    """
    Ambil detail satu resep
    ---
    tags:
      - Resep
    summary: Detail resep berdasarkan nomor resep
    parameters:
      - name: nomor_resep
        in: path
        type: string
        required: true
        example: RES-20240601-ABC123
    responses:
      200:
        description: Detail resep ditemukan
        schema:
          type: object
          properties:
            status:
              type: string
              example: success
            data:
              $ref: '#/definitions/Resep'
      404:
        description: Resep tidak ditemukan
        schema:
          $ref: '#/definitions/ErrorResponse'
    """
    resep = Resep.query.filter_by(nomor_resep=nomor_resep).first()
    if not resep:
        return jsonify({"status": "error", "kode": 404, "pesan": "Resep tidak ditemukan"}), 404
    return jsonify({"status": "success", "data": resep.to_dict()}), 200


@pharmacy_bp.route('/resep', methods=['POST'])
def buat_resep():
    """
    Buat resep baru
    ---
    tags:
      - Resep
    summary: Buat resep obat untuk pasien
    description: |
      Endpoint ini membuat resep baru dan **otomatis mengurangi stok** obat yang dipilih.
      
      Dipanggil oleh **Integration Layer** setelah dokter selesai diagnosa di Rekam Medis.
      
      Nomor resep di-generate otomatis dengan format: `RES-YYYYMMDD-XXXXXX`
    parameters:
      - name: body
        in: body
        required: true
        schema:
          $ref: '#/definitions/ResepInput'
    responses:
      201:
        description: Resep berhasil dibuat, stok obat dikurangi
        schema:
          type: object
          properties:
            status:
              type: string
              example: success
            message:
              type: string
              example: Resep berhasil dibuat
            data:
              $ref: '#/definitions/Resep'
      400:
        description: Field tidak lengkap atau stok tidak mencukupi
        schema:
          $ref: '#/definitions/ErrorResponse'
      404:
        description: Kode obat tidak ditemukan
        schema:
          $ref: '#/definitions/ErrorResponse'
    """
    body = request.get_json()
    if not body:
        return jsonify({"status": "error", "kode": 400, "pesan": "Body JSON kosong"}), 400

    required = ['patient_id', 'nama_pasien', 'dokter', 'obat_list']
    for field in required:
        if field not in body:
            return jsonify({"status": "error", "kode": 400, "pesan": f"Field '{field}' wajib diisi"}), 400

    nomor_resep = f"RES-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:6].upper()}"

    detail_list = []
    total_harga = 0.0

    for item in body['obat_list']:
        kode_obat = item.get('kode_obat')
        jumlah    = item.get('jumlah', 1)

        obat = Obat.query.filter_by(kode_obat=kode_obat).first()
        if not obat:
            return jsonify({"status": "error", "kode": 404, "pesan": f"Obat '{kode_obat}' tidak ditemukan"}), 404
        if obat.stok < jumlah:
            return jsonify({"status": "error", "kode": 400, "pesan": f"Stok '{obat.nama_obat}' tidak mencukupi (stok: {obat.stok})"}), 400

        subtotal = obat.harga * jumlah
        total_harga += subtotal

        detail_list.append({
            "obat": obat,
            "jumlah": jumlah,
            "aturan_pakai": item.get('aturan_pakai', '-'),
            "harga_satuan": obat.harga,
            "subtotal": subtotal
        })

    resep = Resep(
        nomor_resep=nomor_resep,
        patient_id=body['patient_id'],
        nama_pasien=body['nama_pasien'],
        dokter=body['dokter'],
        diagnosis=body.get('diagnosis', ''),
        status='pending',
        total_harga=total_harga
    )
    db.session.add(resep)
    db.session.flush()

    for item_data in detail_list:
        detail = DetailResep(
            resep_id=resep.id,
            kode_obat=item_data['obat'].kode_obat,
            nama_obat=item_data['obat'].nama_obat,
            jumlah=item_data['jumlah'],
            aturan_pakai=item_data['aturan_pakai'],
            harga_satuan=item_data['harga_satuan'],
            subtotal=item_data['subtotal']
        )
        db.session.add(detail)
        item_data['obat'].stok -= item_data['jumlah']

        if item_data['obat'].stok <= STOK_MINIMUM:
            publish_stok_menipis(item_data['obat'].to_dict())

    db.session.commit()

    return jsonify({
        "status": "success",
        "message": "Resep berhasil dibuat",
        "data": resep.to_dict()
    }), 201


@pharmacy_bp.route('/resep/<string:nomor_resep>/selesai', methods=['PATCH'])
def selesaikan_resep(nomor_resep):
    """
    Selesaikan resep (trigger event ke Billing)
    ---
    tags:
      - Resep
    summary: Tandai resep selesai dan kirim event ke Billing Service
    description: |
      Menandai resep sebagai **selesai** (obat sudah diserahkan ke pasien).
      
      ## ⚡ Alur End-to-End
      Setelah endpoint ini dipanggil:
      1. Status resep berubah → `selesai`
      2. Event `resep.selesai` dikirim ke RabbitMQ exchange `pharmacy_events`
      3. **Billing Service** menerima event tersebut dan membuat tagihan otomatis
      
      Ini adalah implementasi pola **Publish-Subscribe** dan **Event-Driven Integration**.
    parameters:
      - name: nomor_resep
        in: path
        type: string
        required: true
        example: RES-20240601-ABC123
    responses:
      200:
        description: Resep selesai, event dikirim ke Billing Service
        schema:
          type: object
          properties:
            status:
              type: string
              example: success
            message:
              type: string
              example: Resep selesai. Event dikirim ke Billing Service.
            data:
              $ref: '#/definitions/Resep'
      404:
        description: Resep tidak ditemukan
        schema:
          $ref: '#/definitions/ErrorResponse'
      409:
        description: Resep sudah berstatus selesai sebelumnya
        schema:
          $ref: '#/definitions/ErrorResponse'
    """
    resep = Resep.query.filter_by(nomor_resep=nomor_resep).first()
    if not resep:
        return jsonify({"status": "error", "kode": 404, "pesan": "Resep tidak ditemukan"}), 404

    if resep.status == 'selesai':
        return jsonify({"status": "error", "kode": 409, "pesan": "Resep sudah selesai sebelumnya"}), 409

    resep.status = 'selesai'
    resep.updated_at = datetime.utcnow()
    db.session.commit()

    # ★ KIRIM EVENT KE RABBITMQ ★
    publish_resep_selesai(resep.to_dict())

    return jsonify({
        "status": "success",
        "message": "Resep selesai. Event dikirim ke Billing Service.",
        "data": resep.to_dict()
    }), 200
