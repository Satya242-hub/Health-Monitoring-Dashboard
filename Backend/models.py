import datetime as dt

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class Patient(Base):
    __tablename__ = "patients"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    age: Mapped[int] = mapped_column(Integer)
    room: Mapped[str] = mapped_column(String(20))

    # Baseline physiology used by the simulator to generate realistic,
    # patient-specific vitals. In a real system this table would not
    # exist and readings would come from actual monitoring hardware.
    baseline_hr: Mapped[float] = mapped_column(Float)
    baseline_bp_sys: Mapped[float] = mapped_column(Float)
    baseline_bp_dia: Mapped[float] = mapped_column(Float)
    baseline_spo2: Mapped[float] = mapped_column(Float)
    baseline_temp: Mapped[float] = mapped_column(Float)
    drift: Mapped[float] = mapped_column(Float, default=1.0)

    readings: Mapped[list["VitalReading"]] = relationship(
        back_populates="patient", cascade="all, delete-orphan", order_by="VitalReading.timestamp"
    )
    alerts: Mapped[list["Alert"]] = relationship(
        back_populates="patient", cascade="all, delete-orphan", order_by="Alert.timestamp.desc()"
    )


class VitalReading(Base):
    __tablename__ = "vital_readings"

    id: Mapped[int] = mapped_column(primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"))
    timestamp: Mapped[dt.datetime] = mapped_column(DateTime, default=dt.datetime.utcnow, index=True)

    hr: Mapped[float] = mapped_column(Float)
    bp_sys: Mapped[float] = mapped_column(Float)
    bp_dia: Mapped[float] = mapped_column(Float)
    spo2: Mapped[float] = mapped_column(Float)
    temp: Mapped[float] = mapped_column(Float)

    patient: Mapped["Patient"] = relationship(back_populates="readings")


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"))
    timestamp: Mapped[dt.datetime] = mapped_column(DateTime, default=dt.datetime.utcnow, index=True)

    level: Mapped[str] = mapped_column(String(20))  # "warning" | "critical"
    message: Mapped[str] = mapped_column(String(255))
    dismissed: Mapped[bool] = mapped_column(Boolean, default=False)

    patient: Mapped["Patient"] = relationship(back_populates="alerts")
