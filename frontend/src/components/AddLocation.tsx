import React, { useState } from 'react';
import { Modal, Button, Form, Alert, Spinner } from 'react-bootstrap';

interface AddLocationProps {
  show: boolean;
  onHide: () => void;
  onLocationAdded: () => void;
}

const AddLocation: React.FC<AddLocationProps> = ({ show, onHide, onLocationAdded }) => {
  const [name, setName] = useState<string>('');
  const [latitude, setLatitude] = useState<string>('');
  const [longitude, setLongitude] = useState<string>('');
  const [address, setAddress] = useState<string>('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  
  const resetForm = () => {
    setName('');
    setLatitude('');
    setLongitude('');
    setAddress('');
    setError(null);
  };
  
  const handleHide = () => {
    resetForm();
    onHide();
  };
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    
    // Basic validation
    if (!name.trim()) {
      setError('Location name is required');
      return;
    }
    
    const lat = parseFloat(latitude);
    const lng = parseFloat(longitude);
    
    if (isNaN(lat) || lat < -90 || lat > 90) {
      setError('Latitude must be a number between -90 and 90');
      return;
    }
    
    if (isNaN(lng) || lng < -180 || lng > 180) {
      setError('Longitude must be a number between -180 and 180');
      return;
    }
    
    setLoading(true);
    
    try {
      const response = await fetch('/api/locations/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name,
          latitude: lat,
          longitude: lng,
          address: address || null,
        }),
      });
      
      if (!response.ok) {
        throw new Error('Failed to add location');
      }
      
      // Success
      resetForm();
      onLocationAdded();
      onHide();
    } catch (err) {
      console.error('Error adding location:', err);
      setError(err instanceof Error ? err.message : 'An unknown error occurred');
    } finally {
      setLoading(false);
    }
  };
  
  const handleSearchLocation = async () => {
    if (!name.trim()) {
      setError('Please enter a location name to search');
      return;
    }
    
    setLoading(true);
    setError(null);
    
    try {
      // Use Nominatim geocoding service (free and requires no API key)
      const url = `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(name)}`;
      
      const response = await fetch(url, {
        headers: {
          'Accept': 'application/json',
          'User-Agent': 'Trip Planner App', // Nominatim requires a user agent
        },
      });
      
      if (!response.ok) {
        throw new Error('Geocoding service error');
      }
      
      const data = await response.json();
      
      if (data.length === 0) {
        setError('No locations found. Try a different search term or enter coordinates manually.');
        return;
      }
      
      // Use the first result
      const result = data[0];
      
      setLatitude(result.lat);
      setLongitude(result.lon);
      setAddress(result.display_name);
      
    } catch (err) {
      console.error('Error searching location:', err);
      setError(err instanceof Error ? err.message : 'An unknown error occurred');
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <Modal show={show} onHide={handleHide}>
      <Modal.Header closeButton>
        <Modal.Title>Add New Location</Modal.Title>
      </Modal.Header>
      <Modal.Body>
        {error && (
          <Alert variant="danger">{error}</Alert>
        )}
        
        <Form onSubmit={handleSubmit}>
          <Form.Group className="mb-3">
            <Form.Label>Location Name</Form.Label>
            <Form.Control
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Enter location name"
              required
            />
          </Form.Group>
          
          <div className="d-grid mb-3">
            <Button 
              variant="outline-primary" 
              onClick={handleSearchLocation}
              disabled={loading || !name.trim()}
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
                  Searching...
                </>
              ) : (
                <><i className="bi bi-search"></i> Search for Coordinates</>
              )}
            </Button>
          </div>
          
          <div className="row">
            <div className="col-md-6">
              <Form.Group className="mb-3">
                <Form.Label>Latitude</Form.Label>
                <Form.Control
                  type="number"
                  step="any"
                  value={latitude}
                  onChange={(e) => setLatitude(e.target.value)}
                  placeholder="e.g. 40.7128"
                  required
                />
              </Form.Group>
            </div>
            <div className="col-md-6">
              <Form.Group className="mb-3">
                <Form.Label>Longitude</Form.Label>
                <Form.Control
                  type="number"
                  step="any"
                  value={longitude}
                  onChange={(e) => setLongitude(e.target.value)}
                  placeholder="e.g. -74.0060"
                  required
                />
              </Form.Group>
            </div>
          </div>
          
          <Form.Group className="mb-3">
            <Form.Label>Address (Optional)</Form.Label>
            <Form.Control
              as="textarea"
              rows={2}
              value={address}
              onChange={(e) => setAddress(e.target.value)}
              placeholder="Enter full address"
            />
          </Form.Group>
        </Form>
      </Modal.Body>
      <Modal.Footer>
        <Button variant="secondary" onClick={handleHide}>
          Cancel
        </Button>
        <Button
          variant="primary"
          onClick={handleSubmit}
          disabled={loading}
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
              Saving...
            </>
          ) : (
            'Save Location'
          )}
        </Button>
      </Modal.Footer>
    </Modal>
  );
};

export default AddLocation;


