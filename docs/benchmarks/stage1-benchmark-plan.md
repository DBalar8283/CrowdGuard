# Stage 1 Benchmark Plan (Latency-First Gate)

## Goal
Select the Stage 2 default pose model by passing strict real-time gates first:

- FPS >= 30
- Average latency < 150ms/frame

Then maximize quality among passing candidates.

## Current Stage 1 Harness

Script: `backend/scripts/benchmark_pose_models.py`

What it does now:
- Runs executable timed loops for `yolov8n-pose` and `yolov8s-pose`
- Produces comparable latency/FPS output JSON
- Encodes pass/fail gates for immediate decision support

## Run

```powershell
cd backend
python scripts/benchmark_pose_models.py --frames 120 --output benchmark-results.json
```

## Stage 2 Upgrade Path

Replace mock timing section with real model inference:
- Load actual model weights
- Decode test clips from ShanghaiTech/UCSD/CUHK/URFD/local clips
- Compute tracking continuity and event-level quality metrics
- Keep the same output schema to preserve decision workflow
