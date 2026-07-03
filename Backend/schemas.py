import datetime as dt

from pydantic import BaseModel, ConfigDict


class VitalsOut(BaseModel):
    hr: float
    bp_sys: float
    bp_dia: float
    spo2: float
    temp: float


class VitalReadingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    timestamp: dt.datetime
    hr: float
    bp_sys: float
    bp_dia: float
    spo2: float
    temp: float


class PatientOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    age: int
    room: str
    vitals: VitalsOut
    status: str  # "normal" | "warning" | "critical"
    flags: list[str]


class AlertOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    patient_id: int
    patient_name: str
    timestamp: dt.datetime
    level: str
    message: str
    dismissed: bool
