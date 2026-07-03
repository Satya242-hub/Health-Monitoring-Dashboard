# Providence Health Monitor — Backend

FastAPI + SQLAlchemy (async) backend for the health monitoring dashboard.
Streams live vitals over WebSocket and generates alerts when a patient's
readings cross clinical thresholds.

## Quick start (SQLite, zero setup)

```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

The app creates `health.db` and seeds 6 demo patients on first run. A
background task then "monitors" them, writing a new reading and
broadcasting it every ~2.6 seconds, the same cadence as the frontend mock.

Open http://127.0.0.1:8000/docs for interactive API docs.

## Switching to PostgreSQL

Set `DATABASE_URL` before starting the app:

```bash
export DATABASE_URL="postgresql+asyncpg://USER:PASSWORD@HOST:5432/providence"
uvicorn main:app --port 8000
```

No code changes needed — `database.py` picks the driver from the URL.
Create the database first (`createdb providence`); tables are created
automatically on startup.

## REST API

| Method | Path | Description |
|---|---|---|
| GET | `/api/patients` | All patients with their latest vitals + status |
| GET | `/api/patients/{id}` | Single patient |
| GET | `/api/patients/{id}/history?limit=25` | Recent vital readings, oldest first |
| GET | `/api/alerts?dismissed=false` | Alerts, most recent first |
| POST | `/api/alerts/{id}/dismiss` | Mark an alert as dismissed |
| GET | `/api/health` | Liveness check |

`status` is one of `normal`, `warning`, `critical`, derived from
`vitals_logic.classify()` (same thresholds used by the frontend mock, so
swapping the frontend to real data won't change what counts as abnormal).

## WebSocket

Connect to `ws://HOST:PORT/ws/vitals`. The server pushes JSON messages,
no need to send anything:

```json
{"type": "vitals_update", "patient_id": 1, "vitals": {"hr": 78, "bp_sys": 122, "bp_dia": 80, "spo2": 97, "temp": 37.0}, "status": "normal", "flags": [], "timestamp": "..."}
{"type": "alert", "id": 7, "patient_id": 2, "patient_name": "Marcus Whitfield", "level": "warning", "message": "Abnormal reading: blood pressure", "timestamp": "..."}
```

## Project layout

```
main.py           FastAPI app, REST routes, WebSocket route, startup seeding
database.py       Async engine/session (SQLite by default, Postgres via env var)
models.py         SQLAlchemy models: Patient, VitalReading, Alert
schemas.py        Pydantic response models
vitals_logic.py   Threshold rules shared by simulator + API
simulator.py      Background task generating readings (swap for a real device feed later)
ws_manager.py     WebSocket connection registry + broadcast
```

## Wiring up the real device feed later

Replace the loop in `simulator.py` with whatever ingests real monitor
data (HL7 listener, MQTT subscriber, etc.), and call
`simulator.ingest_reading(session, patient, vitals)` for each incoming
reading — it already handles persistence, threshold checks, alerting,
and broadcasting.

## No auth (current scope)

CORS is wide open and there's no login, per current requirements. Before
this touches real patient data: add authentication (e.g. OAuth2 password
flow via FastAPI's `Depends`), scope which doctors can see which
patients, and lock down CORS to the real frontend origin.
