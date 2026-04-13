import React from 'react';
import { format } from 'date-fns';

interface Alert {
  id: number;
  satellite1: string;
  satellite2: string;
  predicted_time: string;
  distance_km: number;
  probability: number;
  risk_level: string;
  detected_at: string;
}

interface CollisionAlertsProps {
  alerts: Alert[];
}

const CollisionAlerts: React.FC<CollisionAlertsProps> = ({ alerts }) => {
  const getRiskColor = (level: string) => {
    switch (level) {
      case 'HIGH': return '#ff4d4d';
      case 'MEDIUM': return '#ffc107';
      case 'LOW': return '#4caf50';
      default: return '#8e9bb3';
    }
  };

  const getRiskIcon = (level: string) => {
    switch (level) {
      case 'HIGH': return '🚨';
      case 'MEDIUM': return '⚠️';
      case 'LOW': return 'ℹ️';
      default: return '•';
    }
  };

  if (alerts.length === 0) {
    return (
      <div className="no-alerts">
        <div className="no-alerts-icon">✅</div>
        <div className="no-alerts-text">No active collision alerts</div>
        <div className="no-alerts-subtext">All systems nominal</div>
      </div>
    );
  }

  return (
    <div className="collision-alerts">
      {alerts.map(alert => (
        <div 
          key={alert.id} 
          className={`alert-card ${alert.risk_level.toLowerCase()}`}
          style={{ borderLeftColor: getRiskColor(alert.risk_level) }}
        >
          <div className="alert-header">
            <div className="alert-risk">
              <span className="risk-icon">{getRiskIcon(alert.risk_level)}</span>
              <span className="risk-level">{alert.risk_level} RISK</span>
            </div>
            <div className="alert-time">
              {format(new Date(alert.predicted_time), 'HH:mm:ss')}
            </div>
          </div>

          <div className="alert-satellites">
            <div className="satellite-badge">{alert.satellite1}</div>
            <div className="vs">vs</div>
            <div className="satellite-badge">{alert.satellite2}</div>
          </div>

          <div className="alert-details">
            <div className="detail-item">
              <span className="detail-label">Distance</span>
              <span className="detail-value">{alert.distance_km.toFixed(2)} km</span>
            </div>
            <div className="detail-item">
              <span className="detail-label">Probability</span>
              <span className="detail-value">{(alert.probability * 100).toFixed(1)}%</span>
            </div>
            <div className="detail-item">
              <span className="detail-label">Detected</span>
              <span className="detail-value">
                {format(new Date(alert.detected_at), 'HH:mm')}
              </span>
            </div>
          </div>

          <div className="alert-actions">
            <button className="action-btn">View Trajectory</button>
            <button className="action-btn">Calculate Maneuver</button>
          </div>
        </div>
      ))}

      <style>{`
        .collision-alerts {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
          gap: 15px;
          max-height: 400px;
          overflow-y: auto;
          padding: 5px;
        }

        .no-alerts {
          text-align: center;
          padding: 40px;
          background: rgba(76, 175, 80, 0.1);
          border-radius: 12px;
          border: 1px solid #4caf50;
        }

        .no-alerts-icon {
          font-size: 48px;
          margin-bottom: 10px;
        }

        .no-alerts-text {
          font-size: 18px;
          color: #4caf50;
          margin-bottom: 5px;
        }

        .no-alerts-subtext {
          color: #8e9bb3;
          font-size: 14px;
        }

        .alert-card {
          background: rgba(30, 36, 52, 0.9);
          border-radius: 8px;
          padding: 15px;
          border-left: 4px solid;
          border: 1px solid rgba(255, 255, 255, 0.1);
          transition: transform 0.2s;
        }

        .alert-card:hover {
          transform: translateY(-2px);
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
        }

        .alert-card.high {
          background: rgba(255, 77, 77, 0.1);
        }

        .alert-card.medium {
          background: rgba(255, 193, 7, 0.1);
        }

        .alert-card.low {
          background: rgba(76, 175, 80, 0.1);
        }

        .alert-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 12px;
        }

        .alert-risk {
          display: flex;
          align-items: center;
          gap: 8px;
        }

        .risk-icon {
          font-size: 18px;
        }

        .risk-level {
          font-weight: bold;
          font-size: 14px;
        }

        .alert-time {
          color: #8e9bb3;
          font-size: 12px;
        }

        .alert-satellites {
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 15px;
          margin-bottom: 15px;
        }

        .satellite-badge {
          background: rgba(74, 144, 226, 0.2);
          border: 1px solid #4a90e2;
          padding: 8px 12px;
          border-radius: 20px;
          font-family: monospace;
          font-size: 14px;
        }

        .vs {
          color: #8e9bb3;
          font-size: 12px;
        }

        .alert-details {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: 10px;
          margin-bottom: 15px;
          padding: 10px;
          background: rgba(0, 0, 0, 0.2);
          border-radius: 6px;
        }

        .detail-item {
          display: flex;
          flex-direction: column;
          align-items: center;
        }

        .detail-label {
          color: #8e9bb3;
          font-size: 11px;
          margin-bottom: 3px;
        }

        .detail-value {
          font-weight: bold;
          font-size: 14px;
        }

        .alert-actions {
          display: flex;
          gap: 10px;
        }

        .action-btn {
          flex: 1;
          padding: 8px;
          background: transparent;
          border: 1px solid #4a90e2;
          border-radius: 4px;
          color: #4a90e2;
          cursor: pointer;
          transition: all 0.2s;
          font-size: 12px;
        }

        .action-btn:hover {
          background: #4a90e2;
          color: white;
        }
      `}</style>
    </div>
  );
};

export default CollisionAlerts;