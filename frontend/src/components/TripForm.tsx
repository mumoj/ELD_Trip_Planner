import React, { useState, useEffect } from 'react';
import { Form, Button, Spinner } from 'react-bootstrap';
import { Location } from '../types';

interface TripFormProps {
  onSubmit: (
    currentLocation: Location,
    pickupLocation: Location,
    dropoffLocation: Location,
    cycleHours: number
  ) => void;
  loading: boolean;
}

const TripForm: React.FC<TripFormProps> = ({ onSubmit, loading }) => {
  const [locations, setLocations] = useState<Location[]>([]);
  const [currentLocationId, setCurrentLocationId] = useState<number>(0);
  const [pickupLocationId, setPickupLocationId] = useState<number>(0);
  const [dropoffLocationId, setDropoffLocationId] = useState<number>(0);
  const [cycleHours, setCycleHours] = useState<number>(0);
  const [loadingLocations, setLoadingLocations] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  
  useEffect(() => {
    // Load locations from API
    const fetchLocations = async () => {
      setLoadingLocations(true);
      try {
        const response = await fetch('/api/locations/');
        if (!response.ok) {
          throw new Error('Failed to fetch locations');
        }
        const data = await response.json();
        setLocations(data);
        
        // Set default values if locations exist
        if (data.length > 0) {
          setCurrentLocationId(data[0].id);
          setPickupLocationId(data.length > 1 ? data[1].id : data[0].id);
          setDropoffLocationId(data.length > 2 ? data[2].id : data[0].id);
        }
      } catch (err) {
        console.error('Error fetching locations:', err);
        setError('Failed to load locations. Please try again later.');
      } finally {
        setLoadingLocations(false);
      }
    };
    
    fetchLocations();
  }, []);
  
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    const currentLocation = locations.find(loc => loc.id === currentLocationId);
    const pickupLocation = locations.find(loc => loc.id === pickupLocationId);
    const dropoffLocation = locations.find(loc => loc.id === dropoffLocationId);
    
    if (!currentLocation || !pickupLocation || !dropoffLocation) {
      setError('Please select valid locations');
      return;
    }
    
    if (cycleHours < 0 || cycleHours > 70) {
      setError('Cycle hours must be between 0 and 70');
      return;
    }
    
    onSubmit(currentLocation, pickupLocation, dropoffLocation, cycleHours);
  };
  
  if (loadingLocations) {
    return (
      <div className="text-center p-3">
        <Spinner animation="border" role="status">
          <span className="visually-hidden">Loading locations...</span>
        </Spinner>
      </div>
    );
  }
  
  if (error) {
    return (
      <div className="alert alert-danger" role="alert">
        {error}
      </div>
    );
  }
  
  return (
    <Form onSubmit={handleSubmit}>
      <Form.Group className="mb-3">
        <Form.Label>Current Location</Form.Label>
        <Form.Select
          value={currentLocationId}
          onChange={(e) => setCurrentLocationId(Number(e.target.value))}
          required
        >
          <option value="">Select current location</option>
          {locations.map((loc) => (
            <option key={loc.id} value={loc.id}>
              {loc.name}
            </option>
          ))}
        </Form.Select>
      </Form.Group>
      
      <Form.Group className="mb-3">
        <Form.Label>Pickup Location</Form.Label>
        <Form.Select
          value={pickupLocationId}
          onChange={(e) => setPickupLocationId(Number(e.target.value))}
          required
        >
          <option value="">Select pickup location</option>
          {locations.map((loc) => (
            <option key={loc.id} value={loc.id}>
              {loc.name}
            </option>
          ))}
        </Form.Select>
      </Form.Group>
      
      <Form.Group className="mb-3">
        <Form.Label>Dropoff Location</Form.Label>
        <Form.Select
          value={dropoffLocationId}
          onChange={(e) => setDropoffLocationId(Number(e.target.value))}
          required
        >
          <option value="">Select dropoff location</option>
          {locations.map((loc) => (
            <option key={loc.id} value={loc.id}>
              {loc.name}
            </option>
          ))}
        </Form.Select>
      </Form.Group>
      
      <Form.Group className="mb-3">
        <Form.Label>Current Cycle Hours Used</Form.Label>
        <Form.Control
          type="number"
          min="0"
          max="70"
          step="0.5"
          value={cycleHours}
          onChange={(e) => setCycleHours(Number(e.target.value))}
          required
        />
        <Form.Text className="text-muted">
          Hours of service used in current 8-day cycle (0-70)
        </Form.Text>
      </Form.Group>
      
      <div className="d-grid">
        <Button 
          variant="primary" 
          type="submit" 
          disabled={loading || locations.length === 0}
        >
          {loading ? (
            <>
              <Spinner
                as="span"
                animation="border"
                size="sm"
                role="status"
                aria-hidden="true"
                className="me-2"
              />
              Planning Trip...
            </>
          ) : (
            'Plan Trip'
          )}
        </Button>
      </div>
    </Form>
  );
};

export default TripForm;