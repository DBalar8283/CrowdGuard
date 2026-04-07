from __future__ import annotations

import argparse
import json
import time
from pathlib import Path


def benchmark_mock(model_name: str, frames: int) -> dict:
    # Stage-1 executable harness for latency-first gating.
    # Replace mock section with real YOLOv8 inference when weights are available.
    base_ms = {"yolov8n-pose": 22.0, "yolov8s-pose": 36.0}.get(model_name, 30.0)
    total_ms = 0.0
    for _ in range(frames):
        start = time.perf_counter()
        time.sleep(base_ms / 1000.0)
        total_ms += (time.perf_counter() - start) * 1000.0

    avg_ms = total_ms / frames
    fps = 1000.0 / avg_ms
    return {
        "model": model_name,
        "frames": frames,
        "avg_latency_ms": round(avg_ms, 3),
        "fps": round(fps, 3),
        "passes_latency_gate": avg_ms < 150.0,
        "passes_fps_gate": fps >= 30.0,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="CrowdGuard Stage-1 benchmark harness")
    parser.add_argument("--frames", type=int, default=120)
    parser.add_argument("--output", type=Path, default=Path("backend/benchmark-results.json"))
    args = parser.parse_args()

    results = [benchmark_mock("yolov8n-pose", args.frames), benchmark_mock("yolov8s-pose", args.frames)]
    args.output.write_text(json.dumps({"results": results}, indent=2), encoding="utf-8")
    print(json.dumps({"results": results}, indent=2))


if __name__ == "__main__":
    main()
