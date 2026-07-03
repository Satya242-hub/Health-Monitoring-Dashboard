"""
Simulates a live vitals feed. In a real deployment this file would not
exist - readings would instead be ingested from bedside monitors (e.g.
via an HL7/MQTT bridge) and pushed into `ingest_reading()` below.
"""
import asyncio
import datetime as dt
import random

from sqlalchemy import select

from database import AsyncSessionLocal
from models import Alert, Patient, VitalReading
from vitals_logic import alert_message, classify
from ws_manager import manager

TICK_SECONDS = 2.6

# tracks last known status level per patient so we only fire a new alert
# when a patient crosses INTO an abnormal state, not on every tick.
_last_level: dict[int, str] = {}


def _jitter(drift: float) -> float:
    return (random.random() - 0.5) * drift


async def _generate_reading(patient: Patient) -> dict:
    j = lambda scale: _jitter(patient.drift) * scale
    return {
        "hr": max(40, round(patient.baseline_hr + j(7))),
        "bp_sys": max(80, round(patient.baseline_bp_sys + j(5))),
        "bp_dia": max(50, round(patient.baseline_bp_dia + j(4))),
        "spo2": min(100, max(85, round(patient.baseline_spo2 + j(1.4), 1))),
        "temp": round(patient.baseline_temp + j(0.3), 1),
    }


async def ingest_reading(session, patient: Patient, vitals: dict):
    """Persist a reading, evaluate thresholds, raise an alert on
    transition into an abnormal state, and broadcast both over the
    WebSocket. Shared by the simulator and could be called by a real
    device-ingestion endpoint too."""
    reading = VitalReading(patient_id=patient.id, timestamp=dt.datetime.utcnow(), **vitals)
    session.add(reading)

    level, flags = classify(vitals)
    new_alert = None
    if level != "normal" and _last_level.get(patient.id) != level:
        new_alert = Alert(
            patient_id=patient.id,
            timestamp=dt.datetime.utcnow(),
            level=level,
            message=alert_message(level, flags),
        )
        session.add(new_alert)
    _last_level[patient.id] = level

    await session.commit()

    await manager.broadcast(
        {
            "type": "vitals_update",
            "patient_id": patient.id,
            "vitals": vitals,
            "status": level,
            "flags": flags,
            "timestamp": reading.timestamp.isoformat(),
        }
    )
    if new_alert is not None:
        await manager.broadcast(
            {
                "type": "alert",
                "id": new_alert.id,
                "patient_id": patient.id,
                "patient_name": patient.name,
                "level": level,
                "message": new_alert.message,
                "timestamp": new_alert.timestamp.isoformat(),
            }
        )


async def run_simulator():
    while True:
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(select(Patient))
                patients = result.scalars().all()
                for patient in patients:
                    vitals = await _generate_reading(patient)
                    await ingest_reading(session, patient, vitals)
        except Exception as exc:  # pragma: no cover - keep the loop alive
            print(f"[simulator] tick failed: {exc}")
        await asyncio.sleep(TICK_SECONDS)
