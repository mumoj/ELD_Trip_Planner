import React from 'react';
import { Card, Table, Badge } from 'react-bootstrap';
import { Trip, RouteStop } from '../types';

interface TripSummaryProps {
  trip: Trip;
  routeData: any;
  stops: RouteStop[];
}

const TripSummary: React.FC<TripSummaryProps> = ({ trip, routeData, stops }) => {
  if (!trip || !routeData) {
    return null;
  }
  
  const formatDistance = (miles: number) => {
    return `${Math.round(miles)} mi`;
  };
  
  const formatDuration = (hours: number) => {
    const totalMinutes = Math.round(hours * 60);
    const h = Math.floor(totalMinutes / 60);
    const m = totalMinutes % 60;
    
    return `${h}h ${m}m`;
  };
  
  const getTotalDrivingTime = () => {
    let drivingHours = 0;
    
    if (routeData) {
      drivingHours = routeData.duration_hours;
    }
    
    return formatDuration(drivingHours);
  };
  
  const getTotalRestTime = () => {
    let restHours = 0;
    
    stops.forEach(stop => {
      if (stop.stop_type === 'rest' || stop.stop_type === 'sleep') {
        const arrivalTime = new Date(stop.arrival_time);
        const departureTime = new Date(stop.departure_time);
        const durationHours = (departureTime.getTime() - arrivalTime.getTime()) / (1000 * 60 * 60);
        restHours += durationHours;
      }
    });
    
    return formatDuration(restHours);
  };
  
  const getServiceHours = () => {
    let serviceHours = 0;
    
    stops.forEach(stop => {
      if (stop.stop_type === 'pickup' || stop.stop_type === 'dropoff' || stop.stop_type === 'fuel') {
        const arrivalTime = new Date(stop.arrival_time);
        const departureTime = new Date(stop.departure_time);
        const durationHours = (departureTime.getTime() - arrivalTime.getTime()) / (1000 * 60 * 60);
        serviceHours += durationHours;
      }
    });
    
    return formatDuration(serviceHours);
  };
  
  const getTripDuration = () => {
    if (stops.length === 0) return 'N/A';
    
    const firstStop = stops[0];
    const lastStop = stops[stops.length - 1];
    
    const startTime = new Date(firstStop.arrival_time);
    const endTime = new Date(lastStop.departure_time);
    
    const durationHours = (endTime.getTime() - startTime.getTime()) / (1000 * 60 * 60);
    return formatDuration(durationHours);
  };
  
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'planned': return 'primary';
      case 'in_progress': return 'warning';
      case 'completed': return 'success';
      case 'cancelled': return 'danger';
      default: return 'secondary';
    }
  };
  
  const formatDateTime = (dateStr: string) => {
    if (!dateStr) return 'N/A';
    
    const date = new Date(dateStr);
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };
  
  return (
    <Card className="mb-4">
      <Card.Header className="d-flex justify-content-between align-items-center">
        <h4>Trip Summary</h4>
        <Badge bg={getStatusColor(trip.status)}>
          {trip.status.replace('_', ' ').toUpperCase()}
        </Badge>
      </Card.Header>
      <Card.Body>
        <div className="row mb-3">
          <div className="col-md-6">
            <div className="mb-3">
              <h5>Route Details</h5>
              <Table bordered size="sm">
                <tbody>
                  <tr>
                    <th>Total Distance</th>
                    <td>{formatDistance(routeData.distance_miles)}</td>
                  </tr>
                  <tr>
                    <th>Total Duration</th>
                    <td>{getTripDuration()}</td>
                  </tr>
                  <tr>
                    <th>Driving Time</th>
                    <td>{getTotalDrivingTime()}</td>
                  </tr>
                  <tr>
                    <th>Rest Time</th>
                    <td>{getTotalRestTime()}</td>
                  </tr>
                  <tr>
                    <th>Service Time</th>
                    <td>{getServiceHours()}</td>
                  </tr>
                  <tr>
                    <th>Total Stops</th>
                    <td>{stops.length}</td>
                  </tr>
                </tbody>
              </Table>
            </div>
          </div>
          <div className="col-md-6">
            <div className="mb-3">
              <h5>Trip Details</h5>
              <Table bordered size="sm">
                <tbody>
                  <tr>
                    <th>Trip ID</th>
                    <td>{trip.id}</td>
                  </tr>
                  <tr>
                    <th>Current Location</th>
                    <td>{trip.current_location_details?.name || 'Unknown'}</td>
                  </tr>
                  <tr>
                    <th>Pickup Location</th>
                    <td>{trip.pickup_location_details?.name || 'Unknown'}</td>
                  </tr>
                  <tr>
                    <th>Dropoff Location</th>
                    <td>{trip.dropoff_location_details?.name || 'Unknown'}</td>
                  </tr>
                  <tr>
                    <th>Created</th>
                    <td>{formatDateTime(trip.created_at)}</td>
                  </tr>
                  <tr>
                    <th>Updated</th>
                    <td>{formatDateTime(trip.updated_at)}</td>
                  </tr>
                </tbody>
              </Table>
            </div>
          </div>
        </div>
      </Card.Body>
    </Card>
  );
};

export default TripSummary;