# ── Base image: Python 3.11 versi ringan (slim) ───────────────────────────
FROM python:3.11-slim

# Set working directory di dalam container
WORKDIR /pharmacy-service

# Copy requirements dulu (agar layer ini di-cache jika requirements tidak berubah)
COPY requirements.txt .

# Install dependencies Python
RUN pip install --no-cache-dir -r requirements.txt

# Copy seluruh kode aplikasi
COPY . .

# Expose port yang dipakai Flask
EXPOSE 5001

# Jalankan dengan gunicorn (lebih stabil dari flask run untuk production)
# workers=2: 2 proses worker
CMD ["gunicorn", "--bind", "0.0.0.0:5001", "--workers", "2", "--timeout", "60", "main:app"]
