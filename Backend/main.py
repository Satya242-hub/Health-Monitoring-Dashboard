import asyncio
import datetime as dt
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database import get_db, init_db, AsyncSessionLocal
from models import Alert, Patient, VitalReading
from schemas import AlertOut, PatientOut, VitalReadingOut, VitalsOut
from simulator import run_simulator
from vitals_logic import classify
from ws_manager import manager

SEED_PATIENTS = [
    dict(name="Eleanor Voss", age=74, room="204A", baseline_hr=78, baseline_bp_sys=122, baseline_bp_dia=80, baseline_spo2=97, baseline_temp=37.0, drift=1.0),
    dict(name="Marcus Whitfield", age=58, room="211B", baseline_hr=92, baseline_bp_sys=148, baseline_bp_dia=94, baseline_spo2=95, baseline_temp=37.4, drift=1.6),
    dict(name="Priya Nair", age=42, room="217A", baseline_hr=70, baseline_bp_sys=114, baseline_bp_dia=74, baseline_spo2=98, baseline_temp=36.8, drift=0.7),
    dict(name="Samuel Okoro", age=66, room="223C", baseline_hr=101, baseline_bp_sys=138, baseline_bp_dia=88, baseline_spo2=93, baseline_temp=38.1, drift=2.1),
    dict(name="Grace Lindqvist", age=81, room="230A", baseline_hr=84, baseline_bp_sys=130, baseline_bp_dia=82, baseline_spo2=94, baseline_temp=37.2, drift=1.3),
    dict(name="Daniel Reyes", age=35, room="236B", baseline_hr=66, baseline_bp_sys=118, baseline_bp_dia=76, baseline_spo2=99, baseline_temp=36.7, drift=0.6),
]

_simulator_task: asyncio.Task | None = None


async def _seed_if_empty():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Patient))
        if result.scalars().first() is None:
            for p in SEED_PATIENTS:
                session.add(Patient(**p))
            await session.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _simulator_task
    await init_db()
    await _seed_if_empty()
    _simulator_task = asyncio.create_task(run_simulator())
    yield
    if _simulator_task:
        _simulator_task.cancel()


app = FastAPI(title="Providence Health Monitor API", lifespan=lifespan)

# No auth yet (per current requirements) - open CORS for local dev.
# Tighten allow_origins before deploying beyond a trusted network.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _patient_to_out(patient: Patient, latest: VitalReading | None) -> PatientOut:
    if latest is None:
        vitals = dict(hr=patient.baseline_hr, bp_sys=patient.baseline_bp_sys,
                       bp_dia=patient.baseline_bp_dia, spo2=patient.baseline_spo2,
                       temp=patient.baseline_temp)
    else:
        vitals = dict(hr=latest.hr, bp_sys=latest.bp_sys, bp_dia=latest.bp_dia,
                       spo2=latest.spo2, temp=latest.temp)
    level, flags = classify(vitals)
    return PatientOut(
        id=patient.id, name=patient.name, age=patient.age, room=patient.room,
        vitals=VitalsOut(**vitals), status=level, flags=flags,
    )


@app.get("/api/patients", response_model=list[PatientOut])
async def list_patients(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Patient))
    patients = result.scalars().all()
    out = []
    for p in patients:
        latest_res = await db.execute(
            select(VitalReading).where(VitalReading.patient_id == p.id)
            .order_by(VitalReading.timestamp.desc()).limit(1)
        )
        out.append(_patient_to_out(p, latest_res.scalars().first()))
    return out


@app.get("/api/patients/{patient_id}", response_model=PatientOut)
async def get_patient(patient_id: int, db: AsyncSession = Depends(get_db)):
    patient = await db.get(Patient, patient_id)
    if patient is None:
        raise HTTPException(404, "Patient not found")
    latest_res = await db.execute(
        select(VitalReading).where(VitalReading.patient_id == patient_id)
        .order_by(VitalReading.timestamp.desc()).limit(1)
    )
    return _patient_to_out(patient, latest_res.scalars().first())


@app.get("/api/patients/{patient_id}/history", response_model=list[VitalReadingOut])
async def get_history(patient_id: int, limit: int = 25, db: AsyncSession = Depends(get_db)):
    patient = await db.get(Patient, patient_id)
    if patient is None:
        raise HTTPException(404, "Patient not found")
    result = await db.execute(
        select(VitalReading).where(VitalReading.patient_id == patient_id)
        .order_by(VitalReading.timestamp.desc()).limit(limit)
    )
    readings = list(reversed(result.scalars().all()))
    return readings


@app.get("/api/alerts", response_model=list[AlertOut])
async def list_alerts(dismissed: bool | None = None, db: AsyncSession = Depends(get_db)):
    stmt = select(Alert).options(selectinload(Alert.patient)).order_by(Alert.timestamp.desc()).limit(50)
    if dismissed is not None:
        stmt = stmt.where(Alert.dismissed == dismissed)
    result = await db.execute(stmt)
    alerts = result.scalars().all()
    return [
        AlertOut(
            id=a.id, patient_id=a.patient_id, patient_name=a.patient.name,
            timestamp=a.timestamp, level=a.level, message=a.message, dismissed=a.dismissed,
        )
        for a in alerts
    ]


@app.post("/api/alerts/{alert_id}/dismiss", response_model=AlertOut)
async def dismiss_alert(alert_id: int, db: AsyncSession = Depends(get_db)):
    alert = await db.get(Alert, alert_id)
    if alert is None:
        raise HTTPException(404, "Alert not found")
    alert.dismissed = True
    await db.commit()
    await db.refresh(alert, attribute_names=["patient"])
    return AlertOut(
        id=alert.id, patient_id=alert.patient_id, patient_name=alert.patient.name,
        timestamp=alert.timestamp, level=alert.level, message=alert.message, dismissed=alert.dismissed,
    )


@app.websocket("/ws/vitals")
async def ws_vitals(ws: WebSocket):
    """Dashboards connect here and receive a stream of
    {type: "vitals_update", ...} and {type: "alert", ...} messages as
    the simulator (or, in production, real monitors) produce new data."""
    await manager.connect(ws)
    try:
        while True:
            # We don't expect inbound messages, but read to detect disconnects.
            await ws.receive_text()
    except WebSocketDisconnect:
        await manager.disconnect(ws)


@app.get("/api/health")
async def health():
    return {"status": "ok", "time": dt.datetime.utcnow().isoformat()}
