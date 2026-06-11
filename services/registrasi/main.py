from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from database import engine, Base, get_db
import models
import schemas
import rabbitmq
from typing import List
import json

# Buat tabel jika belum ada
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Sistem Registrasi Pasien",
    description="API untuk Registrasi Pasien - Integrasi EAI",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/v1/patients", response_model=schemas.PatientResponse, status_code=201)
def create_patient(patient: schemas.PatientCreate, db: Session = Depends(get_db)):
    # Cek apakah NIK sudah terdaftar
    db_patient = db.query(models.PatientModel).filter(models.PatientModel.nik == patient.nik).first()
    if db_patient:
        raise HTTPException(status_code=400, detail="NIK already registered")

    # Simpan ke DB
    new_patient = models.PatientModel(**patient.model_dump())
    db.add(new_patient)
    db.commit()
    db.refresh(new_patient)

    # Siapkan data untuk dikirim ke message broker
    # Konversi tipe data yang tidak serializable seperti Date ke string
    event_data = schemas.PatientResponse.model_validate(new_patient).model_dump()
    event_data["date_of_birth"] = event_data["date_of_birth"].isoformat()
    event_data["created_at"] = event_data["created_at"].isoformat() + "Z"

    # Publish event
    published = rabbitmq.publish_patient_registered(event_data)
    if not published:
        # Pilihan desain: jika gagal publish, kita bisa rollback DB atau membiarkannya. 
        # Di sini kita log error saja untuk kesederhanaan. Idealnya ada Outbox Pattern.
        print("Warning: Patient registered but failed to publish event.")

    return new_patient

@app.get("/api/v1/patients", response_model=List[schemas.PatientResponse])
def get_patients(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    patients = db.query(models.PatientModel).offset(skip).limit(limit).all()
    return patients

@app.get("/api/v1/patients/{patient_id}", response_model=schemas.PatientResponse)
def get_patient(patient_id: str, db: Session = Depends(get_db)):
    patient = db.query(models.PatientModel).filter(models.PatientModel.patient_id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient

@app.get("/health")
def health_check():
    return {"status": "healthy"}
