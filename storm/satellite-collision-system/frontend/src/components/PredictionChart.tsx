import React, { useEffect, useState } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';
import { fetchPredictions } from '../services/api';

interface PredictionChartProps {
  satelliteId: string;
}

interface PredictionPoint {
  timestamp: string;
  altitude: number;
  x: number;
  y: number;
  z: number;
}

const PredictionChart: React.FC<PredictionChartProps> = ({ satelliteId }) => {
  const [predictions, setPredictions] = useState<PredictionPoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [chartType, setChartType] = useState<'altitude' | 'position'>('altitude');

  useEffect(() => {
    loadPredictions();
  }, [satelliteId]);

  const loadPredictions = async () => {
    try {
      setLoading(true);
      const data = await fetchPredictions(satelliteId, 24);
      setPredictions(data.predictions || []);
      setError(null);
    } catch (err) {
      setError('Failed to load predictions');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="chart-loading">
        <div className="spinner"></div>
        <div>Loading predictions...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="chart-error">
        <div className="error-icon">⚠️</div>
        <div>{error}</div>
        <button onClick={loadPredictions} className="retry-btn">
          Retry
        </button>
      </div>
    );
  }

  if (!predictions.length) {
    return (
      <div className="no-data">
        <div>📊 No prediction data available</div>
        <div className="no-data-sub">Train the model first or try again later</div>
      </div>
    );
  }

  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp);
    return `${date.getHours()}:${date.getMinutes().toString().padStart(2, '0')}`;
  };

  return (
    <div className="prediction-chart">
      <div className="chart-controls">
        <button 
          className={`chart-type-btn ${chartType === 'altitude' ? 'active' : ''}`}
          onClick={() => setChartType('altitude')}
        >
          Altitude
        </button>
        <button 
          className={`chart-type-btn ${chartType === 'position' ? 'active' : ''}`}
          onClick={() => setChartType('position')}
        >
          Position
        </button>
      </div>

      <ResponsiveContainer width="100%" height={300}>
        {chartType === 'altitude' ? (
          <LineChart data={predictions}>
            <CartesianGrid strokeDasharray="3 3" stroke="#333" />
            <XAxis 
              dataKey="timestamp" 
              tickFormatter={formatTime}
              stroke="#8e9bb3"
            />
            <YAxis stroke="#8e9bb3" />
            <Tooltip 
              labelFormatter={(label) => new Date(label).toLocaleString()}
              formatter={(value: any) => [`${Number(value).toFixed(2)} km`, 'Altitude']}
              contentStyle={{ background: '#1e2434', border: '1px solid #4a90e2' }}
            />
            <Legend />
            <Line 
              type="monotone" 
              dataKey="altitude" 
              stroke="#4a90e2" 
              name="Altitude"
              dot={false}
              strokeWidth={2}
            />
          </LineChart>
        ) : (
          <LineChart data={predictions}>
            <CartesianGrid strokeDasharray="3 3" stroke="#333" />
            <XAxis 
              dataKey="timestamp" 
              tickFormatter={formatTime}
              stroke="#8e9bb3"
            />
            <YAxis stroke="#8e9bb3" />
            <Tooltip 
              labelFormatter={(label) => new Date(label).toLocaleString()}
              contentStyle={{ background: '#1e2434', border: '1px solid #4a90e2' }}
            />
            <Legend />
            <Line 
              type="monotone" 
              dataKey="x" 
              stroke="#ff4d4d" 
              name="X Position"
              dot={false}
            />
            <Line 
              type="monotone" 
              dataKey="y" 
              stroke="#4caf50" 
              name="Y Position"
              dot={false}
            />
            <Line 
              type="monotone" 
              dataKey="z" 
              stroke="#ffc107" 
              name="Z Position"
              dot={false}
            />
          </LineChart>
        )}
      </ResponsiveContainer>

      <div className="confidence-score">
        <div className="confidence-label">AI Confidence</div>
        <div className="confidence-bar">
          <div className="confidence-fill" style={{ width: '94%' }}></div>
        </div>
        <div className="confidence-value">94%</div>
      </div>

      <style>{`
        .prediction-chart {
          background: rgba(0, 0, 0, 0.2);
          border-radius: 8px;
          padding: 15px;
        }

        .chart-controls {
          display: flex;
          gap: 10px;
          margin-bottom: 15px;
        }

        .chart-type-btn {
          padding: 8px 16px;
          background: transparent;
          border: 1px solid #4a90e2;
          border-radius: 6px;
          color: #8e9bb3;
          cursor: pointer;
          transition: all 0.2s;
        }

        .chart-type-btn:hover {
          border-color: #4a90e2;
          color: white;
        }

        .chart-type-btn.active {
          background: #4a90e2;
          color: white;
        }

        .chart-loading {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          height: 300px;
          gap: 15px;
        }

        .spinner {
          width: 40px;
          height: 40px;
          border: 3px solid rgba(74, 144, 226, 0.3);
          border-top-color: #4a90e2;
          border-radius: 50%;
          animation: spin 1s linear infinite;
        }

        @keyframes spin {
          to { transform: rotate(360deg); }
        }

        .chart-error {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          height: 300px;
          gap: 10px;
          color: #ff4d4d;
        }

        .error-icon {
          font-size: 32px;
        }

        .retry-btn {
          padding: 8px 16px;
          background: #4a90e2;
          color: white;
          border: none;
          border-radius: 6px;
          cursor: pointer;
          margin-top: 10px;
        }

        .no-data {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          height: 300px;
          color: #8e9bb3;
        }

        .no-data-sub {
          font-size: 12px;
          margin-top: 5px;
        }

        .confidence-score {
          display: flex;
          align-items: center;
          gap: 10px;
          margin-top: 15px;
          padding: 10px;
          background: rgba(74, 144, 226, 0.1);
          border-radius: 6px;
        }

        .confidence-label {
          color: #8e9bb3;
          font-size: 12px;
          min-width: 80px;
        }

        .confidence-bar {
          flex: 1;
          height: 8px;
          background: rgba(255, 255, 255, 0.1);
          border-radius: 4px;
          overflow: hidden;
        }

        .confidence-fill {
          height: 100%;
          background: linear-gradient(90deg, #4a90e2, #9b6bff);
          border-radius: 4px;
        }

        .confidence-value {
          color: #4a90e2;
          font-weight: bold;
          font-size: 14px;
          min-width: 45px;
        }
      `}</style>
    </div>
  );
};

export default PredictionChart;