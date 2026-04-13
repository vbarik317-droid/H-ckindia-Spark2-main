import React from 'react';
import { format } from 'date-fns';

interface NavbarProps {
  lastUpdate: Date;
  onRefresh: () => void;
  dataSource?: 'real' | 'simulated';
}

const Navbar: React.FC<NavbarProps> = ({ lastUpdate, onRefresh, dataSource = 'real' }) => {
  return (
    <nav className="navbar">
      <div className="navbar-brand">
        <img src="/vite.svg" alt="Logo" className="logo" />
        <h1>🛰️ Satellite Collision Prediction System</h1>
      </div>
      
      <div className="navbar-controls">
        {/* Data Source Indicator */}
        <div className={`data-source ${dataSource}`}>
          {dataSource === 'real' ? (
            <>
              <span className="source-dot real"></span>
              <span className="source-text">LIVE DATA</span>
            </>
          ) : (
            <>
              <span className="source-dot simulated"></span>
              <span className="source-text">SIMULATED</span>
            </>
          )}
        </div>
        
        <div className="last-update">
          <span className="label">Last Update:</span>
          <span className="time">{format(lastUpdate, 'HH:mm:ss')}</span>
        </div>
        
        <button className="refresh-btn" onClick={onRefresh}>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <path d="M1 4v6h6" strokeWidth="2" strokeLinecap="round"/>
            <path d="M3.51 14a9 9 0 1 0 2.13-9.36L1 10" strokeWidth="2" strokeLinecap="round"/>
          </svg>
          Refresh
        </button>
      </div>

      <style>{`
        .navbar {
          height: 60px;
          background: rgba(20, 25, 40, 0.95);
          backdrop-filter: blur(10px);
          border-bottom: 1px solid #4a90e2;
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 0 30px;
          color: white;
          position: relative;
          z-index: 1000;
        }

        .navbar-brand {
          display: flex;
          align-items: center;
          gap: 15px;
        }

        .navbar-brand h1 {
          font-size: 20px;
          margin: 0;
          background: linear-gradient(135deg, #4a90e2, #9b6bff);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
        }

        .logo {
          height: 35px;
          width: 35px;
        }

        .navbar-controls {
          display: flex;
          align-items: center;
          gap: 20px;
        }

        .data-source {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 6px 12px;
          border-radius: 20px;
          font-size: 12px;
          font-weight: 600;
        }

        .data-source.real {
          background: rgba(76, 175, 80, 0.15);
          border: 1px solid #4caf50;
        }

        .data-source.simulated {
          background: rgba(255, 193, 7, 0.15);
          border: 1px solid #ffc107;
        }

        .source-dot {
          width: 8px;
          height: 8px;
          border-radius: 50%;
        }

        .source-dot.real {
          background: #4caf50;
          animation: pulse 2s infinite;
        }

        .source-dot.simulated {
          background: #ffc107;
        }

        @keyframes pulse {
          0% {
            box-shadow: 0 0 0 0 rgba(76, 175, 80, 0.7);
          }
          70% {
            box-shadow: 0 0 0 5px rgba(76, 175, 80, 0);
          }
          100% {
            box-shadow: 0 0 0 0 rgba(76, 175, 80, 0);
          }
        }

        .source-text {
          color: white;
        }

        .last-update {
          display: flex;
          align-items: center;
          gap: 8px;
          background: rgba(74, 144, 226, 0.1);
          padding: 8px 15px;
          border-radius: 20px;
          border: 1px solid rgba(74, 144, 226, 0.3);
        }

        .last-update .label {
          color: #8e9bb3;
          font-size: 14px;
        }

        .last-update .time {
          color: #4a90e2;
          font-weight: bold;
          font-size: 14px;
        }

        .refresh-btn {
          display: flex;
          align-items: center;
          gap: 8px;
          background: #4a90e2;
          color: white;
          border: none;
          padding: 8px 16px;
          border-radius: 6px;
          cursor: pointer;
          font-size: 14px;
          transition: background 0.2s;
        }

        .refresh-btn:hover {
          background: #357abd;
        }

        .refresh-btn svg {
          transition: transform 0.5s;
        }

        .refresh-btn:hover svg {
          transform: rotate(180deg);
        }
      `}</style>
    </nav>
  );
};

export default Navbar;