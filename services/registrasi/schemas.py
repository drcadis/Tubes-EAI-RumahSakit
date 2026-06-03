from pydantic import BaseModel, Field
import datetime
from typing import Optional

class PatientBase(BaseModel):
    nik: str = Field(..., max_length=16, min_length=16, description="Nomor Induk Kependudukan")
    full_name: str
    date_of_birth: datetime.date
    gender: str = Field(..., max_length=1, description="L atau P")
    contact_number: Optional[str] = None
    address: Optional[str] = None
    blood_type: Optional[str] = Field(None, max_length=2)
    registration_type: str = Field(..., description="UMUM, BPJS, atau ASURANSI")

class PatientCreate(PatientBase):
    pass

class PatientResponse(PatientBase):
    patient_id: str
    created_at: datetime.datetime

    class Config:
        from_attributes = True

# Skema Event untuk RabbitMQ
class PatientRegisteredEvent(BaseModel):
    event_id: str
    event_timestamp: str
    event_type: str = "PATIENT_REGISTERED"
    data: dict
