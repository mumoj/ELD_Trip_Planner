// src/types.ts
export interface Location {
    id: number;
    name: string;
    latitude: number;
    longitude: number;
    address?: string;
  }
  
  export interface Trip {
    id: number;
    driver: number;
    current_location: number;
    current_location_details?: Location;
    pickup_location: number;
    pickup_location_details?: Location;
    dropoff_location: number;
    dropoff_location_details?: Location;
    current_cycle_hours: number;
    created_at: string;
    updated_at: string;
    status: string;
    stops?: RouteStop[];
  }
  
  export interface RouteStop {
    id: number;
    location: number;
    location_details: Location;
    arrival_time: string;
    departure_time: string;
    stop_type: string;
    notes?: string;
  }
  
  export interface LogEntry {
    id: number;
    start_time: string;
    end_time: string;
    status: string;
    location?: string;
    remarks?: string;
  }
  
  export interface DailyLog {
    id: number;
    trip: number;
    date: string;
    log_image: string;
    json_data?: any;
    entries: LogEntry[];
  }