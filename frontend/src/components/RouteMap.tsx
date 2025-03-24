import React, { useEffect } from 'react';
import { MapContainer, TileLayer, Polyline, Marker, Popup } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import { RouteStop } from '../types';

const DefaultIcon = L.icon({
    iconUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon.png',
    shadowUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-shadow.png',
    iconSize: [25, 41],
    iconAnchor: [12, 41]
  });
  
  L.Marker.prototype.options.icon = DefaultIcon;

interface RouteMapProps {
  routeData: any;
  stops: RouteStop[];
}

const RouteMap: React.FC<RouteMapProps> = ({ routeData, stops }) => {
  if (!routeData || !stops.length) {
    return <div>No route data available</div>;
  }

  // Convert coordinates from [longitude, latitude] to [latitude, longitude] for Leaflet
  const routeCoordinates: [number, number][] = [
    ...routeData.coordinates.current_to_pickup,
    ...routeData.coordinates.pickup_to_dropoff
  ].map(coord => [coord[1], coord[0]]);

  // Calculate bounds to fit all markers
  const bounds = L.latLngBounds(routeCoordinates);

  const getMarkerColor = (stopType: string): string => {
    switch (stopType) {
      case 'rest': return '#28a745'; // Green
      case 'sleep': return '#6f42c1'; // Purple
      case 'fuel': return '#fd7e14'; // Orange
      case 'food': return '#ffc107'; // Yellow
      case 'pickup': return '#007bff'; // Blue
      case 'dropoff': return '#dc3545'; // Red
      default: return '#6c757d'; // Gray
    }
  };

  const formatStopType = (stopType: string): string => {
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

  const formatDateTime = (dateStr: string): string => {
    if (!dateStr) return 'N/A';
    const date = new Date(dateStr);
    return date.toLocaleString();
  };

  return (
    <div>
      <MapContainer 
        bounds={bounds} 
        style={{ height: '400px', width: '100%', borderRadius: '4px' }}
        zoom={5}
        scrollWheelZoom={true}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        
        {/* Draw the route line */}
        <Polyline 
          positions={routeCoordinates} 
          color="#3887be"
          weight={5}
          opacity={0.75}
        />
        
        {/* Add markers for each stop */}
        {stops.map((stop, index) => {
          // Skip if coordinates are missing
          if (!stop.location_details.latitude || !stop.location_details.longitude) return null;
          
          return (
            <Marker
              key={index}
              position={[stop.location_details.latitude, stop.location_details.longitude]}
              icon={L.divIcon({
                className: 'custom-div-icon',
                html: `<div style="background-color: ${getMarkerColor(stop.stop_type)}; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; font-size: 12px; border: 2px solid white; box-shadow: 0 2px 5px rgba(0,0,0,0.2);">${index + 1}</div>`,
                iconSize: [24, 24],
                iconAnchor: [12, 12],
                popupAnchor: [0, -12]
              })}
            >
              <Popup>
                <div style={{ maxWidth: '250px' }}>
                  <h5 style={{ marginBottom: '8px' }}>{stop.location_details.name}</h5>
                  <p style={{ marginBottom: '5px' }}><strong>Type:</strong> {formatStopType(stop.stop_type)}</p>
                  <p style={{ marginBottom: '5px' }}><strong>Arrival:</strong> {formatDateTime(stop.arrival_time)}</p>
                  <p style={{ marginBottom: '5px' }}><strong>Departure:</strong> {formatDateTime(stop.departure_time)}</p>
                  {stop.notes && <p style={{ marginBottom: '0' }}><strong>Notes:</strong> {stop.notes}</p>}
                </div>
              </Popup>
            </Marker>
          );
        })}
      </MapContainer>
      
      {/* Map legend */}
      <div className="map-legend mt-2">
        <div className="d-flex flex-wrap">
          <div className="me-3 mb-2">
            <span className="legend-marker" style={{ backgroundColor: '#28a745' }}></span>
            <span>Rest</span>
          </div>
          <div className="me-3 mb-2">
            <span className="legend-marker" style={{ backgroundColor: '#6f42c1' }}></span>
            <span>Sleep</span>
          </div>
          <div className="me-3 mb-2">
            <span className="legend-marker" style={{ backgroundColor: '#fd7e14' }}></span>
            <span>Fuel</span>
          </div>
          <div className="me-3 mb-2">
            <span className="legend-marker" style={{ backgroundColor: '#ffc107' }}></span>
            <span>Food</span>
          </div>
          <div className="me-3 mb-2">
            <span className="legend-marker" style={{ backgroundColor: '#007bff' }}></span>
            <span>Pickup</span>
          </div>
          <div className="me-3 mb-2">
            <span className="legend-marker" style={{ backgroundColor: '#dc3545' }}></span>
            <span>Dropoff</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default RouteMap;