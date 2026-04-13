// src/types/index.ts


export interface Satellite {
  norad_id: string;
  name: string;
  country: string;
  object_type: 'PAYLOAD' | 'DEBRIS' | 'ROCKET BODY' | string;
  inclination: number;
  eccentricity: number;
  altitude?: number;
  pos_x: number;
  pos_y: number;
  pos_z: number;
  latitude?: number;
  longitude?: number;
  updated_at: string;  // This is required
  source?: string;
  [key: string]: any;  // Allow additional properties
}

export interface Position {
  timestamp: string;
  x: number;
  y: number;
  z: number;
  altitude: number;
  vx?: number;
  vy?: number;
  vz?: number;
}

export interface Prediction {
  norad_id: string;
  predictions: Position[];
  confidence: number;
  model_version: string;
}

export interface CollisionEvent {
  satellite1: string;
  satellite2: string;
  risk_level: "LOW" | "MEDIUM" | "HIGH";
  distance_km: number;
  probability: number;

  // backend fields
  pos1_x?: number;
  pos1_y?: number;
  pos1_z?: number;
  pos2_x?: number;
  pos2_y?: number;
  pos2_z?: number;
}

export interface Collision {
  satellite1: string;
  satellite2: string;
  risk_level: "LOW" | "MEDIUM" | "HIGH";
  distance_km: number;
  probability: number;

  // optional (used by Globe if available)
  pos1?: {
    lat: number;
    lon: number;
    alt: number;
  };
  pos2?: {
    lat: number;
    lon: number;
    alt: number;
  };
}

export interface Alert {
  id: number;
  satellite1: string;
  satellite2: string;
  predicted_time: string;
  distance_km: number;
  probability: number;
  risk_level: string;
  detected_at: string;
}

export interface CollisionCheckResponse {
  collisions: CollisionEvent[];
  total_checked: number;
  timestamp: string;
}

export interface ApiResponse<T> {
  data: T;
  message?: string;
  status: 'success' | 'error';
}