# Stage 1 Dashboard Screens (Implemented)

## Operator Persona
Security guards/operators monitoring live crowd feeds with low tolerance for ambiguous alerts.

## Screen Layout

1. Top status bar
- Live/offline badge
- Mission context statement

2. KPI strip
- People count
- Fruin LOS
- Density (per m2)
- Average velocity

3. Main grid
- Live feed overlay (bounding boxes + IDs)
- Digital twin minimap (map points)
- Density/velocity trend chart
- XAI alert log (persistent, scrollable)

## UX Rules Applied

- High-contrast dark environment for control-room readability
- Critical alerts use red semantic emphasis
- Key operator metrics always visible above fold
- Alert messages prioritize why the system triggered (XAI-first)

## File References

- `frontend/src/App.tsx`
- `frontend/src/components/LiveFeedPanel.tsx`
- `frontend/src/components/MiniMapPanel.tsx`
- `frontend/src/components/AlertLogPanel.tsx`
- `frontend/src/components/AnalyticsPanel.tsx`
