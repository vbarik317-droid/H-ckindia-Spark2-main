// src/services/api.ts
import axios from 'axios';
import { Satellite, Alert, CollisionCheckResponse, Prediction } from '../types';
import { cartesianToLatLonAlt } from "../utils/coordinates";

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for logging
api.interceptors.request.use(request => {
  console.log('Starting Request:', request.url);
  return request;
});

// Response interceptor for error handling
api.interceptors.response.use(
  response => response,
  error => {
    console.error('API Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

export const fetchSatellites = async (
    limit = 300,
    offset = 0,
    mode: "leo" | "geo" | "all" = "leo"
  ): Promise<Satellite[]> => {
  const response = await api.get("/satellites/", {
    params: { limit, offset, mode }
  });

  return response.data
    .filter((sat: any) => {
      return (
        sat.pos_x !== 0 &&
        sat.pos_y !== 0 &&
        sat.pos_z !== 0
      );
    })
    .map((sat: any) => {
      const { latitude, longitude, altitude } =
        cartesianToLatLonAlt(sat.pos_x, sat.pos_y, sat.pos_z);

      return {
        ...sat,
        latitude,
        longitude,
        altitude
      };
    });
  
}

export const fetchSatellitePositions = async (noradId: string, hours: number = 24) => {
  try {
    const response = await api.get(`/satellites/${noradId}/positions`, {
      params: { hours }
    });
    return response.data;
  } catch (error) {
    console.error('Error fetching positions:', error);
    return [];
  }
};

export const fetchPredictions = async (noradId: string, hours: number = 24): Promise<Prediction> => {
  try {
    const response = await api.get(`/satellites/${noradId}/predict`, {
      params: { hours }
    });
    return response.data;
  } catch (error) {
    console.error('Error fetching predictions:', error);
    return { predictions: [], confidence: 0, model_version: '', norad_id: noradId };
  }
};

export const fetchAlerts = async (hoursBack: number = 24, riskLevel?: string): Promise<Alert[]> => {
  try {
    const response = await api.get('/alerts/', {
      params: { hours_back: hoursBack, risk_level: riskLevel }
    });
    return response.data;
  } catch (error) {
    console.error('Error fetching alerts:', error);
    return [];
  }
};

export const checkCollisions = async (
  hoursAhead: number = 24,
  minRisk: string = 'LOW'
) => {
  const response = await api.get('/collisions/', {
    params: {
      hours_ahead: hoursAhead,
      min_risk: minRisk
    }
  });
  return response.data;
};

export const triggerDataFetch = async (source?: string) => {
  try {
    const response = await api.post('/fetch-data', null, {
      params: { source }
    });
    return response.data;
  } catch (error) {
    console.error('Error triggering data fetch:', error);
    throw error;
  }
};

export const trainModel = async (satelliteId?: string) => {
  try {
    const response = await api.post('/train-model', null, {
      params: { satellite_id: satelliteId }
    });
    return response.data;
  } catch (error) {
    console.error('Error training model:', error);
    throw error;
  }
};

export const simulateData = async (count: number = 50) => {
  try {
    const response = await api.post('/simulate-data', null, {
      params: { count }
    });
    return response.data;
  } catch (error) {
    console.error('Error simulating data:', error);
    throw error;
  }
};

export default api;