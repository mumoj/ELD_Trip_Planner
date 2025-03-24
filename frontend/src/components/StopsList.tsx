import React from 'react';
import { ListGroup } from 'react-bootstrap';
import { RouteStop } from '../types';

interface StopsListProps {
  stops: RouteStop[];
}

const StopsList: React.FC<StopsListProps> = ({ stops }) => {
  if (!stops || stops.length === 0) {
    return <div>No stops available</div>;
  }
  
  const formatDate = (dateStr: string) => {
    if (!dateStr) return 'N/A';
    
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric'
    });
  };
  
  const formatTime = (dateStr: string) => {
    if (!dateStr) return 'N/A';
    
    const date = new Date(dateStr);
    return date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit'
    });
  };
  
  const getDuration = (arrival: string, departure: string) => {
    if (!arrival || !departure) return 'N/A';
    
    const arrivalDate = new Date(arrival);
    const departureDate = new Date(departure);
    
    const durationMs = departureDate.getTime() - arrivalDate.getTime();
    const durationMins = Math.round(durationMs / 60000);
    
    if (durationMins < 60) {
      return `${durationMins} min`;
    } else {
      const hours = Math.floor(durationMins / 60);
      const mins = durationMins % 60;
      return `${hours}h ${mins}m`;
    }
  };
  
  const getStopTypeIcon = (stopType: string) => {
    switch (stopType) {
      case 'rest': return 'bi-cup-hot';
      case 'sleep': return 'bi-moon';
      case 'fuel': return 'bi-fuel-pump';
      case 'food': return 'bi-egg-fried';
      case 'pickup': return 'bi-box-seam';
      case 'dropoff': return 'bi-truck';
      default: return 'bi-geo-alt';
    }
  };
  
  const getStopTypeLabel = (stopType: string) => {
    switch (stopType) {
      case 'rest': return 'Required Rest';
      case 'sleep': return 'Sleep Break';
      case 'fuel': return 'Fuel Stop';
      case 'food': return 'Food Break';
      case 'pickup': return 'Pickup';
      case 'dropoff': return 'Dropoff';
      default: return stopType;
    }
  };
  
  return (
    <div className="stops-list">
      <ListGroup variant="flush">
        {stops.map((stop, index) => (
          <ListGroup.Item key={index} className="stop-item">
            <div className="stop-number">{index + 1}</div>
            <div className="stop-content">
              <div className="stop-header">
                <h5 className="stop-location">{stop.location_details?.name || 'Unknown Location'}</h5>
                <div className="stop-type">
                  <i className={`bi ${getStopTypeIcon(stop.stop_type)}`}></i> {getStopTypeLabel(stop.stop_type)}
                </div>
              </div>
              
              <div className="stop-times">
                <div className="time-block">
                  <div className="time-label">Arrive</div>
                  <div className="time-value">
                    <div>{formatDate(stop.arrival_time)}</div>
                    <div>{formatTime(stop.arrival_time)}</div>
                  </div>
                </div>
                
                <div className="duration-block">
                  <div className="duration-value">
                    {getDuration(stop.arrival_time, stop.departure_time)}
                  </div>
                  <div className="duration-line"></div>
                </div>
                
                <div className="time-block">
                  <div className="time-label">Depart</div>
                  <div className="time-value">
                    <div>{formatDate(stop.departure_time)}</div>
                    <div>{formatTime(stop.departure_time)}</div>
                  </div>
                </div>
              </div>
              
              {stop.notes && (
                <div className="stop-notes">
                  <small>{stop.notes}</small>
                </div>
              )}
            </div>
          </ListGroup.Item>
        ))}
      </ListGroup>
    </div>
  );
};

export default StopsList;