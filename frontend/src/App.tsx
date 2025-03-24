import React, { useState, useEffect } from 'react';
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
  const [csrfToken, setCsrfToken] = useState<string | null>(null);
  
  // Get CSRF token on component mount
  useEffect(() => {
    // Function to get cookie by name
    const getCookie = (name: string): string | null => {
      const value = `; ${document.cookie}`;
      const parts = value.split(`; ${name}=`);
      if (parts.length === 2) {
        const cookieValue = parts.pop()?.split(';').shift() || null;
        return cookieValue;
      }
      return null;
    };
    
    // Get CSRF token from cookie
    const token = getCookie('csrftoken');
    setCsrfToken(token);
    
    // If no token found, try to get one
    if (!token) {
      fetch('/api-auth/login/', { method: 'GET', credentials: 'include' })
        .then(response => {
          // After this request, Django should set the CSRF cookie
          const newToken = getCookie('csrftoken');
          setCsrfToken(newToken);
        })
        .catch(err => {
          console.error('Error fetching CSRF token:', err);
        });
    }
  }, []);
  
  const handleTripSubmit = async (
    currentLocation: Location,
    pickupLocation: Location,
    dropoffLocation: Location,
    cycleHours: number
  ) => {
    setLoading(true);
    setError(null);
    
    try {
      console.log('Making POST request to /api/trips/ with data:', {
        current_location: currentLocation.id,
        pickup_location: pickupLocation.id,
        dropoff_location: dropoffLocation.id,
        current_cycle_hours: cycleHours,
        driver: 1,
        status: 'planned'
      });
      
      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
        'X-Requested-With': 'XMLHttpRequest'
      };
      
      // Add CSRF token header if available
      if (csrfToken) {
        headers['X-CSRFToken'] = csrfToken;
      }
      
      // First, create a new trip
      const tripResponse = await fetch('/api/trips/', {
        method: 'POST',
        headers: headers,
        credentials: 'include', // Important for sending cookies
        body: JSON.stringify({
          current_location: currentLocation.id,
          pickup_location: pickupLocation.id,
          dropoff_location: dropoffLocation.id,
          current_cycle_hours: cycleHours,
          driver: 1, // Assuming user is logged in with ID 1
          status: 'planned'
        }),
      });
      
      console.log('Trip response status:', tripResponse.status);
      console.log('Trip response status text:', tripResponse.statusText);
      
      // Log headers
      const responseHeaders: Record<string, string> = {};
      tripResponse.headers.forEach((value, name) => {
        responseHeaders[name] = value;
      });
      console.log('Trip response headers:', responseHeaders);
      
      // Clone the response so we can log the body and still use it later
      const responseClone = tripResponse.clone();
      
      try {
        const responseText = await responseClone.text();
        console.log('Trip response body:', responseText);
        
        // Try to parse as JSON if applicable
        try {
          const responseJson = JSON.parse(responseText);
          console.log('Trip response as JSON:', responseJson);
        } catch (e) {
          console.log('Response is not valid JSON');
        }
      } catch (e) {
        console.log('Could not read response body:', e);
      }
      
      if (!tripResponse.ok) {
        const errorData = await tripResponse.json().catch(() => ({}));
        throw new Error(errorData.detail || `Failed to create trip: ${tripResponse.status} ${tripResponse.statusText}`);
      }
      
      const tripData = await tripResponse.json();
      console.log('Trip data after successful response:', tripData);
      
      setTrip(tripData);
      
      // Then calculate the route
      console.log(`Fetching route for trip ID ${tripData.id}`);
      const routeResponse = await fetch(`/api/trips/${tripData.id}/calculate_route/`, {
        method: 'GET',
        headers: {
          'X-Requested-With': 'XMLHttpRequest',
          ...(csrfToken && { 'X-CSRFToken': csrfToken })
        },
        credentials: 'include',
      });
      
      console.log('Route response status:', routeResponse.status);
      
      if (!routeResponse.ok) {
        throw new Error('Failed to calculate route');
      }
      
      const routeData = await routeResponse.json();
      console.log('Route data:', routeData);
      
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