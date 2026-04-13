import React, { useState, useEffect } from 'react';
import Globe from './components/Globe';
import SatelliteList from './components/SatelliteList';
import CollisionAlerts from './components/CollisionAlerts';
import PredictionChart from './components/PredictionChart';
import Navbar from './components/Navbar';
import { fetchSatellites, fetchAlerts, checkCollisions } from './services/api';
import { Satellite, Alert, Collision } from "./types";
import './App.css';
import * as Cesium from "cesium";

function cartesianToLatLon(
  x: number,
  y: number,
  z: number
) {
  const carto = Cesium.Cartographic.fromCartesian(
    new Cesium.Cartesian3(x, y, z)
  );

  return {
    lat: Cesium.Math.toDegrees(carto.latitude),
    lon: Cesium.Math.toDegrees(carto.longitude),
    alt: carto.height / 1000
  };
}

function App() {
  const [satellites, setSatellites] = useState<Satellite[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [selectedSatellite, setSelectedSatellite] = useState<Satellite | null>(null);
  const [loading, setLoading] = useState(true);
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());
  const [showPredictions, setShowPredictions] = useState(false);
  const [dataSource, setDataSource] = useState<'real' | 'simulated'>('simulated');
  const [satelliteCount, setSatelliteCount] = useState(0);
  const [collisions, setCollisions] = useState<Collision[]>([]);  
  const [page, setPage] = useState(0);
  const PAGE_SIZE = 300;
  useEffect(() => {
    loadData();
    // Refresh data every 30 seconds for real-time tracking
    const interval = setInterval(loadData, 30000);
    return () => clearInterval(interval);
  }, []);

  const loadData = async () => {
    try {
      const [satsData, alertsData, collisionData] = await Promise.all([
        fetchSatellites(300, 0, "leo"),
        fetchAlerts(),
        checkCollisions(48, "MEDIUM")
      ]);

      const formatted = (collisionData.collisions || [])
        .filter(
          (c: any) =>
            c.pos1_x !== null &&
            c.pos1_y !== null &&
            c.pos1_z !== null &&
            c.pos2_x !== null &&
            c.pos2_y !== null &&
            c.pos2_z !== null
        )
        .map((c: any) => ({
          satellite1: c.satellite1,
          satellite2: c.satellite2,
          risk_level: c.risk_level,
          distance_km: c.distance_km,
          probability: c.probability,
          pos1: cartesianToLatLon(c.pos1_x, c.pos1_y, c.pos1_z),
          pos2: cartesianToLatLon(c.pos2_x, c.pos2_y, c.pos2_z)
        }));

      console.log("SATELLITES:", satsData.length);
      console.log("ALERTS:", alertsData.length);
      console.log("COLLISIONS (RAW):", collisionData.collisions?.length ?? 0);
      console.log("COLLISIONS (FORMATTED):", formatted.length);

      setSatellites(satsData);
      setSatelliteCount(satsData.length);
      setAlerts(alertsData);
      setCollisions(formatted);
      setLastUpdate(new Date());

    } catch (error) {
      console.error("Error loading data:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = () => {
    setLoading(true);
    loadData();
  };

  if (loading && satellites.length === 0) {
    return <div className="loading">Loading satellite data...</div>;
  }

  return (
    <div className="app">
      <Navbar 
        lastUpdate={lastUpdate} 
        onRefresh={handleRefresh}
        dataSource={dataSource}
      />
      
      <div className="dashboard">
        {/* Stats Cards */}
        <div className="stats-container">
          <div className="stat-card">
            <div className="stat-value">{satelliteCount}</div>
            <div className="stat-label">Satellites Tracked</div>
            <div className="stat-source">{dataSource === 'real' ? '📡 LIVE' : '🧪 TEST'}</div>
          </div>
          <div className="stat-card warning">
            <div className="stat-value">
              {alerts.filter(a => a.risk_level === 'HIGH').length}
            </div>
            <div className="stat-label">High Risk Collisions</div>
          </div>
          <div className="stat-card info">
            <div className="stat-value">
              {collisions.filter(c => c.risk_level === 'MEDIUM').length}
            </div>
            <div className="stat-label">Medium Risk</div>
          </div>
          <div className="stat-card success">
            <div className="stat-value">94%</div>
            <div className="stat-label">AI Confidence</div>
          </div>
        </div>

        {/* Main Grid */}
        <div className="main-grid">
          {/* 3D Globe */}
          <div className="globe-container">
            <Globe 
              satellites={satellites}
              collisions={collisions}
              selectedSatellite={selectedSatellite}
            />
          </div>

          {/* Satellite List Sidebar */}
          <div className="sidebar">
            <SatelliteList 
              satellites={satellites}
              onSelect={setSelectedSatellite}
              selectedId={selectedSatellite?.norad_id}
            />
          </div>
        </div>

        {/* Collision Alerts Section */}
        <div className="alerts-section">
          <h2>🚨 Collision Alerts</h2>
          <CollisionAlerts alerts={alerts} />
        </div>

        {/* Prediction Section */}
        {selectedSatellite && (
          <div className="predictions-section">
            <div className="predictions-header">
              <h2>AI Predictions for {selectedSatellite.name}</h2>
              <button 
                className="toggle-btn"
                onClick={() => setShowPredictions(!showPredictions)}
              >
                {showPredictions ? 'Hide' : 'Show'} Predictions
              </button>
            </div>
            {showPredictions && (
              <PredictionChart satelliteId={selectedSatellite.norad_id} />
            )}
          </div>
        )}
      </div>

      <style>{`
        .stat-source {
          font-size: 11px;
          color: #8e9bb3;
          margin-top: 5px;
        }
        
        .loading {
          display: flex;
          justify-content: center;
          align-items: center;
          height: 100vh;
          font-size: 18px;
          color: #4a90e2;
          background: linear-gradient(135deg, #0b0f1a 0%, #1a1f2f 100%);
        }
      `}</style>
    </div>
  );
}

export default App;