# CrowdGuard

Stage 1 implementation for CrowdGuard with a runnable backend and guard-focused React dashboard.

## One-Command Launcher (Recommended)

From project root:

```powershell
powershell -ExecutionPolicy Bypass -File .\start.ps1
```

## Demo Source Modes (Real Feed)

Set environment variables before running `start.ps1`.

### 1) Simulation (default)

```powershell
$env:CROWDGUARD_SOURCE_MODE = "simulation"
```

### 2) Webcam feed with real person boxes

```powershell
$env:CROWDGUARD_SOURCE_MODE = "webcam"
$env:CROWDGUARD_SOURCE_CAMERA_INDEX = "0"
$env:CROWDGUARD_DETECTOR_MODE = "yolo"
powershell -ExecutionPolicy Bypass -File .\start.ps1
```

### 3) Dataset clip / local video file demo

```powershell
$env:CROWDGUARD_SOURCE_MODE = "video_file"
$env:CROWDGUARD_SOURCE_URI = "D:\\datasets\\demo_clip.mp4"
$env:CROWDGUARD_DETECTOR_MODE = "yolo"
powershell -ExecutionPolicy Bypass -File .\start.ps1
```

### 4) RTSP feed demo

```powershell
$env:CROWDGUARD_SOURCE_MODE = "rtsp"
$env:CROWDGUARD_SOURCE_URI = "rtsp://user:pass@ip:port/stream"
$env:CROWDGUARD_DETECTOR_MODE = "yolo"
powershell -ExecutionPolicy Bypass -File .\start.ps1
```

Notes:
- YOLO mode uses `ultralytics` model `yolov8n.pt` by default.
- If YOLO is unavailable, set detector to HOG fallback:

```powershell
$env:CROWDGUARD_DETECTOR_MODE = "hog"
```

## Stop Services

```powershell
powershell -ExecutionPolicy Bypass -File .\stop.ps1
```

## Current Reality

- In real source modes, dashboard shows actual camera/video frames and real detected person boxes.
- Current alert logic for real feed is LOS/density-focused for demo reliability.
- Advanced fall logic with pose + tracking is next phase.
