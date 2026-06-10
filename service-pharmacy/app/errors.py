from flask import jsonify
import logging

logger = logging.getLogger(__name__)


def register_error_handlers(app):
    """
    Daftarkan semua error handler ke Flask app.
    Dipanggil sekali di factory.py saat app dibuat.
    
    Tanpa ini, kalau ada error maka Flask mengembalikan HTML — 
    tidak cocok untuk REST API yang harus selalu return JSON.
    """

    # ── 400 Bad Request ────────────────────────────────────────────────────
    @app.errorhandler(400)
    def bad_request(e):
        logger.warning(f"[400] Bad Request: {e}")
        return jsonify({
            "status": "error",
            "kode": 400,
            "pesan": "Request tidak valid. Periksa format dan isi body kiriman kamu."
        }), 400

    # ── 404 Not Found ──────────────────────────────────────────────────────
    @app.errorhandler(404)
    def not_found(e):
        logger.warning(f"[404] Not Found: {e}")
        return jsonify({
            "status": "error",
            "kode": 404,
            "pesan": "Endpoint atau data yang dicari tidak ditemukan."
        }), 404

    # ── 405 Method Not Allowed ─────────────────────────────────────────────
    @app.errorhandler(405)
    def method_not_allowed(e):
        logger.warning(f"[405] Method Not Allowed: {e}")
        return jsonify({
            "status": "error",
            "kode": 405,
            "pesan": "HTTP method tidak diizinkan untuk endpoint ini."
        }), 405

    # ── 409 Conflict ───────────────────────────────────────────────────────
    @app.errorhandler(409)
    def conflict(e):
        logger.warning(f"[409] Conflict: {e}")
        return jsonify({
            "status": "error",
            "kode": 409,
            "pesan": "Data konflik — kemungkinan data sudah ada sebelumnya."
        }), 409

    # ── 422 Unprocessable Entity ───────────────────────────────────────────
    @app.errorhandler(422)
    def unprocessable(e):
        logger.warning(f"[422] Unprocessable: {e}")
        return jsonify({
            "status": "error",
            "kode": 422,
            "pesan": "Data tidak dapat diproses. Periksa tipe dan nilai field."
        }), 422

    # ── 500 Internal Server Error ──────────────────────────────────────────
    # Handler paling penting: tangkap semua error Python yang tidak terduga
    @app.errorhandler(500)
    def internal_error(e):
        logger.error(f"[500] Internal Server Error: {e}", exc_info=True)
        return jsonify({
            "status": "error",
            "kode": 500,
            "pesan": "Terjadi kesalahan internal pada server. Hubungi administrator."
        }), 500

    # ── Exception umum Python (ValueError, TypeError, dll) ────────────────
    @app.errorhandler(Exception)
    def unhandled_exception(e):
        # Jika sudah ditangani handler di atas, lewati
        if hasattr(e, 'code') and e.code in [400, 404, 405, 409, 422, 500]:
            raise e

        logger.error(f"[UNHANDLED] Exception: {type(e).__name__}: {e}", exc_info=True)
        return jsonify({
            "status": "error",
            "kode": 500,
            "pesan": f"Terjadi error tidak terduga: {type(e).__name__}",
            "detail": str(e)
        }), 500
