export type FruinLevel = "A" | "B" | "C" | "D" | "E" | "F";

export interface Point2D {
  x: number;
  y: number;
}

export interface Track {
  person_id: string;
  bbox: [number, number, number, number];
  map_point: Point2D;
  velocity_mps: number;
  spine_angle_deg: number;
  bbox_ratio: number;
}

export interface AlertReason {
  reason_code: string;
  details: Record<string, unknown>;
}

export interface AlertItem {
  event_id: string;
  person_id?: string;
  event_type: "fall" | "los_critical" | "bottleneck";
  severity: "info" | "warn" | "critical";
  zone_id: string;
  message: string;
  reasons: AlertReason[];
}

export interface StreamPayload {
  version: "v1";
  timestamp: string;
  camera_id: string;
  zone_id: string;
  people_count: number;
  density_per_m2: number;
  fruin_level: FruinLevel;
  avg_velocity_mps: number;
  tracks: Track[];
  alerts: AlertItem[];
  frame_jpeg?: string | null;
  frame_width?: number | null;
  frame_height?: number | null;
}
