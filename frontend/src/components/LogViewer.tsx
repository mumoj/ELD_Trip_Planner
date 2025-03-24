import React from 'react';
import { Nav, Tab } from 'react-bootstrap';
import { DailyLog } from '../types';

interface LogViewerProps {
  logs: DailyLog[];
  activeLog: number;
  onLogChange: (index: number) => void;
}

const LogViewer: React.FC<LogViewerProps> = ({ logs, activeLog, onLogChange }) => {
  if (!logs || logs.length === 0) {
    return <div>No logs available</div>;
  }
  
  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', {
      weekday: 'short',
      month: 'short',
      day: 'numeric'
    });
  };
  
  return (
    <div className="log-viewer">
      <Tab.Container activeKey={activeLog.toString()} onSelect={(key) => onLogChange(Number(key))}>
        <Nav variant="pills" className="mb-3 flex-row log-nav">
          {logs.map((log, index) => (
            <Nav.Item key={log.id}>
              <Nav.Link eventKey={index.toString()}>
                {formatDate(log.date)}
              </Nav.Link>
            </Nav.Item>
          ))}
        </Nav>
        
        <Tab.Content>
          {logs.map((log, index) => (
            <Tab.Pane key={log.id} eventKey={index.toString()}>
              <div className="log-image-container text-center">
                {log.log_image ? (
                  <img 
                    src={log.log_image} 
                    alt={`Daily log for ${log.date}`} 
                    className="img-fluid log-sheet"
                  />
                ) : (
                  <div className="log-placeholder">
                    <p>Log image not available</p>
                  </div>
                )}
              </div>
              
              <div className="log-entries mt-3">
                <h5>Log Entries:</h5>
                <ul className="list-group">
                  {log.entries && log.entries.map((entry, entryIndex) => (
                    <li key={entryIndex} className="list-group-item log-entry">
                      <div className="log-entry-status">
                        <span className={`status-badge status-${entry.status}`}>
                          {formatStatus(entry.status)}
                        </span>
                      </div>
                      <div className="log-entry-time">
                        <span>{formatTime(entry.start_time)}</span>
                        <span className="mx-2">to</span>
                        <span>{formatTime(entry.end_time || '')}</span>
                      </div>
                      {entry.location && (
                        <div className="log-entry-location">
                          <i className="bi bi-geo-alt"></i> {entry.location}
                        </div>
                      )}
                      {entry.remarks && (
                        <div className="log-entry-remarks">
                          <small>{entry.remarks}</small>
                        </div>
                      )}
                    </li>
                  ))}
                </ul>
              </div>
            </Tab.Pane>
          ))}
        </Tab.Content>
      </Tab.Container>
    </div>
  );
};

const formatStatus = (status: string): string => {
  switch (status) {
    case 'off_duty': return 'Off Duty';
    case 'sleeper': return 'Sleeper Berth';
    case 'driving': return 'Driving';
    case 'on_duty': return 'On Duty (Not Driving)';
    default: return status;
  }
};

const formatTime = (timeStr: string): string => {
  if (!timeStr) return '';
  
  const date = new Date(timeStr);
  return date.toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit'
  });
};

export default LogViewer;