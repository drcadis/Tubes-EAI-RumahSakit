from sqlalchemy import Column, String, Date, DateTime, Text
from database import Base
import datetime
import uuid

def generate_uuid():
    return str(uuid.uuid4())

class PatientModel(Base):
    __tablename__ = "patients"

    patient_id = Column(String, primary_key=True, index=True, default=generate_uuid)
    nik = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=False)
    date_of_birth = Column(Date, nullable=False)
    gender = Column(String(1), nullable=False) # L / P
    contact_number = Column(String, nullable=True)
    address = Column(Text, nullable=True)
    blood_type = Column(String(2), nullable=True)
    registration_type = Column(String, nullable=False) # UMUM, BPJS, ASURANSI
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
