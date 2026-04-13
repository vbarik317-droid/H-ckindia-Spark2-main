import React, { useState } from 'react';
import { formatDistanceToNow } from 'date-fns';
import { Satellite } from '../types';

interface SatelliteListProps {
  satellites: Satellite[];
  onSelect: (sat: Satellite) => void;
  selectedId?: string;
}

const SatelliteList: React.FC<SatelliteListProps> = ({ satellites, onSelect, selectedId }) => {
  const [filter, setFilter] = useState('');
  const [sortBy, setSortBy] = useState<'name' | 'altitude' | 'country'>('name');

  const filteredSatellites = satellites
    .filter(sat => 
      sat.name.toLowerCase().includes(filter.toLowerCase()) ||
      sat.norad_id.includes(filter) ||
      sat.country.toLowerCase().includes(filter.toLowerCase())
    )
    .sort((a, b) => {
      if (sortBy === 'name') {
        return a.name.localeCompare(b.name);
      }

      if (sortBy === 'altitude') {
        return (a.altitude ?? 0) - (b.altitude ?? 0);
      }

      if (sortBy === 'country') {
        return a.country.localeCompare(b.country);
      }

      return 0;
    });

  return (
    <div className="satellite-list">
      <div className="list-header">
        <h3>Tracked Satellites</h3>
        <input
          type="text"
          placeholder="🔍 Search..."
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          className="search-input"
        />
      </div>

      <div className="sort-controls">
        <button 
          className={`sort-btn ${sortBy === 'name' ? 'active' : ''}`}
          onClick={() => setSortBy('name')}
        >
          Name
        </button>
        <button 
          className={`sort-btn ${sortBy === 'altitude' ? 'active' : ''}`}
          onClick={() => setSortBy('altitude')}
        >
          Altitude
        </button>
        <button 
          className={`sort-btn ${sortBy === 'country' ? 'active' : ''}`}
          onClick={() => setSortBy('country')}
        >
          Country
        </button>
      </div>

      <div className="satellites-container">
        {filteredSatellites.map(sat => (
          <div
            key={sat.norad_id}
            className={`satellite-item ${selectedId === sat.norad_id ? 'selected' : ''}`}
            onClick={() => onSelect(sat)}
          >
            <div className="satellite-header">
              <div className="satellite-name">{sat.name}</div>
              <div className={`satellite-type ${(sat.object_type || '').toLowerCase()}`}>
                {sat.object_type || 'UNKNOWN'}
              </div>
            </div>
            
            <div className="satellite-details">
              <div className="detail">
                <span className="detail-label">NORAD:</span>
                <span className="detail-value">{sat.norad_id}</span>
              </div>
              <div className="detail">
                <span className="detail-label">Country:</span>
                <span className="detail-value">{sat.country || 'Unknown'}</span>
              </div>
              <div className="detail">
                <span className="detail-label">Altitude:</span>
                <span className="detail-value">{(sat.altitude?? 0).toFixed(2) || 'N/A'} km</span>
              </div>
              <div className="detail">
                <span className="detail-label">Inclination:</span>
                <span className="detail-value">{sat.inclination?.toFixed(1) || 'N/A'}°</span>
              </div>
              <div className="detail">
                <span className="detail-label">Updated:</span>
                <span className="detail-value">
                  {sat.updated_at ? formatDistanceToNow(new Date(sat.updated_at)) + ' ago' : 'N/A'}
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="list-footer">
        Showing {filteredSatellites.length} of {satellites.length} satellites
      </div>

      <style>{`
        .satellite-list {
          height: 100%;
          display: flex;
          flex-direction: column;
          color: #ffffff;
        }

        .list-header {
          padding-bottom: 15px;
          border-bottom: 1px solid rgba(74, 144, 226, 0.2);
        }

        .list-header h3 {
          margin: 0 0 10px 0;
          font-size: 16px;
          color: #8e9bb3;
        }

        .search-input {
          width: 100%;
          padding: 10px;
          background: rgba(0, 0, 0, 0.3);
          border: 1px solid rgba(74, 144, 226, 0.3);
          border-radius: 6px;
          color: white;
          font-size: 14px;
        }

        .search-input:focus {
          outline: none;
          border-color: #4a90e2;
        }

        .sort-controls {
          display: flex;
          gap: 10px;
          padding: 15px 0;
        }

        .sort-btn {
          flex: 1;
          padding: 8px;
          background: transparent;
          border: 1px solid rgba(74, 144, 226, 0.3);
          border-radius: 6px;
          color: #8e9bb3;
          cursor: pointer;
          transition: all 0.2s;
        }

        .sort-btn:hover {
          border-color: #4a90e2;
          color: white;
        }

        .sort-btn.active {
          background: #4a90e2;
          border-color: #4a90e2;
          color: white;
        }

        .satellites-container {
          flex: 1;
          overflow-y: auto;
          padding-right: 5px;
        }

        .satellite-item {
          background: rgba(0, 0, 0, 0.2);
          border: 1px solid rgba(74, 144, 226, 0.1);
          border-radius: 8px;
          padding: 12px;
          margin-bottom: 10px;
          cursor: pointer;
          transition: all 0.2s;
        }

        .satellite-item:hover {
          border-color: #4a90e2;
          transform: translateX(2px);
        }

        .satellite-item.selected {
          border-color: #4a90e2;
          background: rgba(74, 144, 226, 0.1);
        }

        .satellite-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 10px;
        }

        .satellite-name {
          font-weight: bold;
          color: white;
        }

        .satellite-type {
          font-size: 11px;
          padding: 3px 8px;
          border-radius: 12px;
          text-transform: uppercase;
        }

        .satellite-type.payload {
          background: rgba(76, 175, 80, 0.2);
          color: #4caf50;
        }

        .satellite-type.debris {
          background: rgba(255, 77, 77, 0.2);
          color: #ff4d4d;
        }

        .satellite-type.rocket {
          background: rgba(255, 193, 7, 0.2);
          color: #ffc107;
        }

        .satellite-details {
          display: grid;
          grid-template-columns: repeat(2, 1fr);
          gap: 8px;
          font-size: 12px;
        }

        .detail {
          display: flex;
          flex-direction: column;
        }

        .detail-label {
          color: #8e9bb3;
          font-size: 10px;
          margin-bottom: 2px;
        }

        .detail-value {
          color: white;
        }

        .list-footer {
          padding-top: 15px;
          text-align: center;
          color: #8e9bb3;
          font-size: 12px;
          border-top: 1px solid rgba(74, 144, 226, 0.2);
        }
      `}</style>
    </div>
  );
};

export default SatelliteList;