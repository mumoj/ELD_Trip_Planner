import React, { useState } from 'react';
import { Container, Row, Col, Card } from 'react-bootstrap';
import TripForm from './components/TripForm';
import RouteMap from './components/RouteMap';
import LogViewer from './components/LogViewer';
import StopsList from './components/StopsList';
import TripSummary from './components/TripSummary';
import { Location, Trip, RouteStop, DailyLog } from './types';
import './App.css';

const App: React.FC = () => {
  const [trip, setTrip] = useState<Trip | null>(null);
  const [routeData, setRouteData] = useState<any | null>(null);
  const [stops, setStops] = useState<RouteStop[]>([]);
  const [dailyLogs, setDailyLogs] = useState<DailyLog[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [activeLog, setActiveLog] = useState<number>(0);
  const [error, setError] = useState<string | null>(null);
  
  const handleTripSubmit = async (
    currentLocation: Location,
    pickupLocation: Location,
    dropoffLocation: Location,
    cycleHours: number
  ) => {
    setLoading(true);
    setError(null);
    
    try {
      // First, create a new trip
      const tripResponse = await fetch('/api/trips/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          current_location: currentLocation.id,
          pickup_location: pickupLocation.id,
          dropoff_location: dropoffLocation.id,
          current_cycle_hours: cycleHours,
          driver: 1, // Assuming user is logged in with ID 1
          status: 'planned'
        }),
      });
      
      if (!tripResponse.ok) {
        throw new Error('Failed to create trip');
      }
      
      const tripData = await tripResponse.json();
      setTrip(tripData);
      
      // Then calculate the route
      const routeResponse = await fetch(`/api/trips/${tripData.id}/calculate_route/`, {
        method: 'GET',
      });
      
      if (!routeResponse.ok) {
        throw new Error('Failed to calculate route');
      }
      
      const routeData = await routeResponse.json();
      setRouteData(routeData.route);
      setStops(routeData.stops);
      setDailyLogs(routeData.daily_logs);
      
      if (routeData.daily_logs.length > 0) {
        setActiveLog(0);
      }
    } catch (err) {
      console.error('Error planning trip:', err);
      setError(err instanceof Error ? err.message : 'An unknown error occurred');
    } finally {
      setLoading(false);
    }
  };
  
  const handleLogChange = (index: number) => {
    setActiveLog(index);
  };
  
  return (
    <Container fluid className="mt-4 mb-5">
      <Row>
        <Col md={12}>
          <h1 className="text-center mb-4">Trip Planner & ELD Logger</h1>
        </Col>
      </Row>
      
      <Row>
        <Col md={4}>
          <Card className="mb-4">
            <Card.Header>
              <h4>Trip Details</h4>
            </Card.Header>
            <Card.Body>
              <TripForm onSubmit={handleTripSubmit} loading={loading} />
            </Card.Body>
          </Card>
          
          {stops.length > 0 && (
            <Card>
              <Card.Header>
                <h4>Route Stops</h4>
              </Card.Header>
              <Card.Body>
                <StopsList stops={stops} />
              </Card.Body>
            </Card>
          )}
        </Col>
        
        <Col md={8}>
          {error && (
            <div className="alert alert-danger" role="alert">
              {error}
            </div>
          )}
          
          {loading && (
            <div className="text-center p-5">
              <div className="spinner-border text-primary" role="status">
                <span className="visually-hidden">Loading...</span>
              </div>
              <p className="mt-3">Calculating route and generating logs...</p>
            </div>
          )}
          
          {trip && routeData && !loading && (
            <TripSummary trip={trip} routeData={routeData} stops={stops} />
          )}
          
          {routeData && !loading && (
            <Card className="mb-4">
              <Card.Header>
                <h4>Route Map</h4>
              </Card.Header>
              <Card.Body>
                <RouteMap routeData={routeData} stops={stops} />
              </Card.Body>
            </Card>
          )}
          
          {dailyLogs.length > 0 && !loading && (
            <Card>
              <Card.Header>
                <h4>Daily Logs</h4>
              </Card.Header>
              <Card.Body>
                <LogViewer 
                  logs={dailyLogs} 
                  activeLog={activeLog} 
                  onLogChange={handleLogChange} 
                />
              </Card.Body>
            </Card>
          )}
        </Col>
      </Row>
    </Container>
  );
};

export default App;