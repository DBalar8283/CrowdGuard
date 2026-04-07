# Stage 1 Architecture (As Implemented)

## Layer Coverage

- Layer 1: Threaded ingestion contract (`CaptureEngine` freshest-frame buffer)
- Layer 2: Perception/tracking interfaces represented in stream payload (`tracks`, `person_id`, keypoints)
- Layer 3: Logic engine implemented for density + Fruin LOS + XAI fall detection + LOS override path
- Layer 4: FastAPI routes, SQLite persistence, WebSocket stream, privacy-first metadata storage
- Layer 5: React dashboard panels for feed, minimap, XAI log, analytics

## Runtime Flow

1. FastAPI app starts and initializes SQLite schema.
2. Capture thread updates latest frame packet continuously.
3. Stream simulator produces per-tick perception/logic outputs.
4. Metrics and alerts are persisted into SQLite.
5. `/ws/live` broadcasts the latest `v1` payload to frontend clients.
6. React dashboard renders KPIs, map movement, alerts, and trend lines.

## Stage 1 Decisions Reflected in Code

- Includes minimal zero-latency ingestion primitives now (to reduce Stage 2 risk).
- Uses core DB tables + `metric_timeseries` for charting and presentation.
- Skips `track_snapshot` persistence to preserve privacy and reduce storage churn.
- Uses a deterministic stream simulator for reliable demos without model-weight dependency.

## Key Files

- `backend/app/main.py`
- `backend/app/services/simulation.py`
- `backend/app/services/logic.py`
- `backend/app/db/database.py`
- `frontend/src/App.tsx`
- `frontend/src/components/*`
