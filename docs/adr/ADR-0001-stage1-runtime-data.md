# ADR-0001: Stage 1 Runtime and Data Decisions

## Status
Accepted

## Date
2026-04-06

## Context
Stage 1 had to be presentation-ready while preserving the final architecture direction and avoiding fragile dependencies on model weights and camera availability.

## Decision
1. Implement minimal threaded ingestion (`CaptureEngine`) in Stage 1.
2. Implement Stage 1 logic using deterministic simulator outputs with production-like payload contracts.
3. Persist only structured metadata and alerts; do not persist raw frames or per-frame track snapshots.
4. Add `metric_timeseries` table in Stage 1 for analytics graph rendering.

## Consequences

### Positive
- Demo reliability is high even on machines without CUDA/model weights.
- Stage 2 can replace simulation internals without changing API contracts.
- Privacy stance is enforced early by design.
- Dashboard analytics are available immediately.

### Negative
- Stage 1 perception quality is simulated, not benchmark-real.
- Additional implementation work is needed in Stage 2 to plug YOLOv8-Pose + ByteTrack inference.

## Related
- `docs/benchmarks/stage1-benchmark-plan.md`
- `docs/architecture/stage1-implementation.md`
