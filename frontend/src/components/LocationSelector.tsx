import React, { useState, useEffect } from 'react';
import { Form, Button, Modal, InputGroup } from 'react-bootstrap';
import { Location } from '../types';

interface LocationSelectorProps {
  label: string;
  value: number;
  onChange: (locationId: number) => void;
  locations: Location[];
}

const LocationSelector: React.FC<LocationSelectorProps> = ({ label, value, onChange, locations }) => {
  const [showModal, setShowModal] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [filteredLocations, setFilteredLocations] = useState<Location[]>([]);
  
  // Set initial filtered locations
  useEffect(() => {
    setFilteredLocations(locations);
  }, [locations]);
  
  // Handle search filter
  useEffect(() => {
    if (!searchTerm.trim()) {
      setFilteredLocations(locations);
      return;
    }
    
    const lowerSearchTerm = searchTerm.toLowerCase();
    const filtered = locations.filter(location => 
      location.name.toLowerCase().includes(lowerSearchTerm) ||
      (location.address && location.address.toLowerCase().includes(lowerSearchTerm))
    );
    
    setFilteredLocations(filtered);
  }, [searchTerm, locations]);
  
  const handleOpenModal = () => {
    setSearchTerm('');
    setFilteredLocations(locations);
    setShowModal(true);
  };
  
  const handleSelectLocation = (locationId: number) => {
    onChange(locationId);
    setShowModal(false);
  };
  
  const getSelectedLocationName = () => {
    const selected = locations.find(loc => loc.id === value);
    return selected ? selected.name : 'Select location';
  };
  
  return (
    <>
      <Form.Group className="mb-3">
        <Form.Label>{label}</Form.Label>
        <InputGroup>
          <Form.Control
            value={getSelectedLocationName()}
            readOnly
            placeholder="Select location"
          />
          <Button variant="outline-secondary" onClick={handleOpenModal}>
            <i className="bi bi-geo-alt"></i> Select
          </Button>
        </InputGroup>
      </Form.Group>
      
      <Modal show={showModal} onHide={() => setShowModal(false)} size="lg">
        <Modal.Header closeButton>
          <Modal.Title>Select {label}</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <Form.Group className="mb-3">
            <InputGroup>
              <InputGroup.Text>
                <i className="bi bi-search"></i>
              </InputGroup.Text>
              <Form.Control
                type="text"
                placeholder="Search locations..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </InputGroup>
          </Form.Group>
          
          <div className="location-list">
            {filteredLocations.length === 0 ? (
              <div className="text-center p-3">
                <p>No locations found</p>
              </div>
            ) : (
              <div className="list-group">
                {filteredLocations.map(location => (
                  <button
                    key={location.id}
                    type="button"
                    className={`list-group-item list-group-item-action ${value === location.id ? 'active' : ''}`}
                    onClick={() => handleSelectLocation(location.id)}
                  >
                    <div className="d-flex w-100 justify-content-between">
                      <h5 className="mb-1">{location.name}</h5>
                    </div>
                    {location.address && (
                      <p className="mb-1 text-muted">
                        <small><i className="bi bi-geo"></i> {location.address}</small>
                      </p>
                    )}
                    <div className="d-flex w-100 justify-content-between mt-2">
                      <small>
                        <i className="bi bi-geo-alt"></i> Lat: {location.latitude}, Lng: {location.longitude}
                      </small>
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowModal(false)}>
            Cancel
          </Button>
        </Modal.Footer>
      </Modal>
    </>
  );
};

export default LocationSelector;