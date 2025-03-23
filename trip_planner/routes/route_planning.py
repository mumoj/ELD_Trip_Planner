import requests
import datetime
from .models import RouteStop, Location
from django.conf import settings

# HOS (Hours of Service) regulations
MAX_DRIVING_HOURS = 11  # Maximum driving hours per day
MAX_ON_DUTY_HOURS = 14  # Maximum on-duty hours per day
MAX_CYCLE_HOURS = 70    # Maximum on-duty hours in 8 days
REQUIRED_REST_HOURS = 10 # Required consecutive rest hours
MAX_DRIVING_BEFORE_BREAK = 8  # Maximum driving hours before a 30-minute break
AVERAGE_SPEED_MPH = 55  # Average truck speed in miles per hour
FUELING_INTERVAL_MILES = 1000  # Fueling needed every 1000 miles
PICKUP_DROPOFF_HOURS = 1  # Hours needed for pickup and dropoff

def calculate_route(current_location, pickup_location, dropoff_location, current_cycle_hours):
    """
    Calculate the route using a free map API
    
    This function uses OpenStreetMap's Nominatim API for geocoding
    and OSRM (Open Source Routing Machine) for route planning
    """
    # Create a route object with sections:
    # 1. Current location to pickup
    # 2. Pickup to dropoff
    
    # For OSRM API
    base_url = "http://router.project-osrm.org/route/v1/driving/"
    
    # Current to pickup
    current_to_pickup_url = f"{base_url}{current_location.longitude},{current_location.latitude};"
    current_to_pickup_url += f"{pickup_location.longitude},{pickup_location.latitude}?overview=full&geometries=geojson"
    
    # Make API request
    response = requests.get(current_to_pickup_url)
    current_to_pickup_data = response.json()
    
    # Pickup to dropoff
    pickup_to_dropoff_url = f"{base_url}{pickup_location.longitude},{pickup_location.latitude};"
    pickup_to_dropoff_url += f"{dropoff_location.longitude},{dropoff_location.latitude}?overview=full&geometries=geojson"
    
    # Make API request
    response = requests.get(pickup_to_dropoff_url)
    pickup_to_dropoff_data = response.json()
    
    # Calculate distance and time
    total_distance_meters = (
        current_to_pickup_data['routes'][0]['distance'] + 
        pickup_to_dropoff_data['routes'][0]['distance']
    )
    total_distance_miles = total_distance_meters / 1609.34
    
    total_duration_seconds = (
        current_to_pickup_data['routes'][0]['duration'] + 
        pickup_to_dropoff_data['routes'][0]['duration']
    )
    # Convert to hours and add pickup/dropoff time
    total_duration_hours = (total_duration_seconds / 3600) + (2 * PICKUP_DROPOFF_HOURS)
    
    # Combine route geometries
    combined_geometry = {
        'section1': current_to_pickup_data['routes'][0]['geometry'],
        'section2': pickup_to_dropoff_data['routes'][0]['geometry']
    }
    
    return {
        'distance_miles': total_distance_miles,
        'duration_hours': total_duration_hours,
        'geometry': combined_geometry,
        'current_to_pickup': {
            'distance_miles': current_to_pickup_data['routes'][0]['distance'] / 1609.34,
            'duration_hours': current_to_pickup_data['routes'][0]['duration'] / 3600
        },
        'pickup_to_dropoff': {
            'distance_miles': pickup_to_dropoff_data['routes'][0]['distance'] / 1609.34,
            'duration_hours': pickup_to_dropoff_data['routes'][0]['duration'] / 3600
        }
    }

def generate_stops(trip, route_data):
    """Generate all necessary stops based on HOS regulations"""
    # Clear existing stops
    trip.stops.all().delete()
    
    # Start with current time
    current_time = datetime.datetime.now()
    
    # Track driver hours
    driving_hours_today = 0
    on_duty_hours_today = 0
    cycle_hours_used = trip.current_cycle_hours
    
    # Track position (miles from start)
    current_position = 0
    last_fuel_position = 0
    
    stops = []
    
    # Add current location as starting point
    start_stop = RouteStop(
        trip=trip,
        location=trip.current_location,
        arrival_time=current_time,
        departure_time=current_time + datetime.timedelta(minutes=15),
        stop_type='rest',
        notes="Trip start"
    )
    start_stop.save()
    stops.append(start_stop)
    
    current_time += datetime.timedelta(minutes=15)  # 15 min preparation
    
    # Current location to pickup
    distance_to_pickup = route_data['current_to_pickup']['distance_miles']
    duration_to_pickup = route_data['current_to_pickup']['duration_hours']
    
    # Handle driving to pickup with potential breaks
    current_time, driving_hours_today, on_duty_hours_today, cycle_hours_used, current_position, last_fuel_position = process_driving_segment(
        trip, 
        stops, 
        trip.current_location, 
        trip.pickup_location,
        current_time, 
        distance_to_pickup, 
        duration_to_pickup,
        driving_hours_today, 
        on_duty_hours_today, 
        cycle_hours_used,
        current_position,
        last_fuel_position
    )
    
    # Add pickup stop
    pickup_stop = RouteStop(
        trip=trip,
        location=trip.pickup_location,
        arrival_time=current_time,
        departure_time=current_time + datetime.timedelta(hours=PICKUP_DROPOFF_HOURS),
        stop_type='pickup',
        notes="Cargo pickup"
    )
    pickup_stop.save()
    stops.append(pickup_stop)
    
    current_time += datetime.timedelta(hours=PICKUP_DROPOFF_HOURS)
    on_duty_hours_today += PICKUP_DROPOFF_HOURS
    cycle_hours_used += PICKUP_DROPOFF_HOURS
    
    # Check if we need a reset after pickup
    if on_duty_hours_today >= MAX_ON_DUTY_HOURS - 2:  # Leave buffer
        # Add rest stop for reset
        rest_stop = RouteStop(
            trip=trip,
            location=trip.pickup_location,
            arrival_time=current_time,
            departure_time=current_time + datetime.timedelta(hours=REQUIRED_REST_HOURS),
            stop_type='sleep',
            notes="Required 10-hour rest period"
        )
        rest_stop.save()
        stops.append(rest_stop)
        
        current_time += datetime.timedelta(hours=REQUIRED_REST_HOURS)
        driving_hours_today = 0
        on_duty_hours_today = 0
    
    # Pickup to dropoff
    distance_to_dropoff = route_data['pickup_to_dropoff']['distance_miles']
    duration_to_dropoff = route_data['pickup_to_dropoff']['duration_hours']
    
    # Handle driving to dropoff with potential breaks
    current_time, driving_hours_today, on_duty_hours_today, cycle_hours_used, current_position, last_fuel_position = process_driving_segment(
        trip, 
        stops, 
        trip.pickup_location, 
        trip.dropoff_location,
        current_time, 
        distance_to_dropoff, 
        duration_to_dropoff,
        driving_hours_today, 
        on_duty_hours_today, 
        cycle_hours_used,
        current_position,
        last_fuel_position
    )
    
    # Add dropoff stop
    dropoff_stop = RouteStop(
        trip=trip,
        location=trip.dropoff_location,
        arrival_time=current_time,
        departure_time=current_time + datetime.timedelta(hours=PICKUP_DROPOFF_HOURS),
        stop_type='dropoff',
        notes="Cargo dropoff"
    )
    dropoff_stop.save()
    stops.append(dropoff_stop)
    
    return stops

def process_driving_segment(trip, stops, start_location, end_location, current_time, distance, duration, 
                            driving_hours_today, on_duty_hours_today, cycle_hours_used, 
                            current_position, last_fuel_position):
    """Process a driving segment with potential breaks"""
    # Calculate how many miles we can cover in the remaining driving time today
    remaining_driving_hours = min(MAX_DRIVING_HOURS - driving_hours_today, MAX_ON_DUTY_HOURS - on_duty_hours_today)
    
    # If we have a break coming up soon, account for that
    if driving_hours_today > 0 and driving_hours_today + duration > MAX_DRIVING_BEFORE_BREAK:
        # We need a 30-minute break
        break_point = MAX_DRIVING_BEFORE_BREAK - driving_hours_today
        
        # Calculate position at break point
        break_miles = (break_point / duration) * distance
        break_position = current_position + break_miles
        
        # Estimate break location
        break_location, _ = get_location_at_position(start_location, end_location, break_position / distance)
        
        # Add break stop
        break_stop = RouteStop(
            trip=trip,
            location=break_location,
            arrival_time=current_time + datetime.timedelta(hours=break_point),
            departure_time=current_time + datetime.timedelta(hours=break_point + 0.5),  # 30-minute break
            stop_type='rest',
            notes="Required 30-minute break"
        )
        break_stop.save()
        stops.append(break_stop)
        
        # Update time and hours
        current_time += datetime.timedelta(hours=break_point + 0.5)
        driving_hours_today += break_point
        on_duty_hours_today += break_point + 0.5
        cycle_hours_used += break_point + 0.5
        current_position = break_position
        
        # Recalculate remaining driving hours
        remaining_driving_hours = min(MAX_DRIVING_HOURS - driving_hours_today, MAX_ON_DUTY_HOURS - on_duty_hours_today)
        
        # Recalculate remaining distance and duration
        remaining_distance = distance - break_miles
        remaining_duration = duration - break_point
        
        # Process the rest of the segment
        return process_driving_segment(
            trip, stops, break_location, end_location,
            current_time, remaining_distance, remaining_duration,
            driving_hours_today, on_duty_hours_today, cycle_hours_used,
            current_position, last_fuel_position
        )
    
    # Check if we need fueling
    if current_position - last_fuel_position >= FUELING_INTERVAL_MILES - 100:  # 100 mile buffer
        # Determine where to fuel
        fuel_miles = 100  # Fuel after driving 100 more miles
        fuel_position = current_position + fuel_miles
        
        # Estimate fuel location
        fuel_location, _ = get_location_at_position(start_location, end_location, fuel_miles / distance)
        
        # Add fuel stop
        fuel_time = current_time + datetime.timedelta(hours=(fuel_miles / AVERAGE_SPEED_MPH))
        fuel_stop = RouteStop(
            trip=trip,
            location=fuel_location,
            arrival_time=fuel_time,
            departure_time=fuel_time + datetime.timedelta(hours=0.75),  # 45 minutes for fueling
            stop_type='fuel',
            notes="Scheduled refueling"
        )
        fuel_stop.save()
        stops.append(fuel_stop)
        
        # Update time and hours
        driving_time = fuel_miles / AVERAGE_SPEED_MPH
        current_time = fuel_time + datetime.timedelta(hours=0.75)
        driving_hours_today += driving_time
        on_duty_hours_today += driving_time + 0.75
        cycle_hours_used += driving_time + 0.75
        current_position = fuel_position
        last_fuel_position = fuel_position
        
        # Recalculate remaining distance and duration
        remaining_distance = distance - fuel_miles
        remaining_duration = duration - driving_time
        
        # Process the rest of the segment
        return process_driving_segment(
            trip, stops, fuel_location, end_location,
            current_time, remaining_distance, remaining_duration,
            driving_hours_today, on_duty_hours_today, cycle_hours_used,
            current_position, last_fuel_position
        )
    
    # If we can't complete the segment today, add overnight stop
    if duration > remaining_driving_hours:
        # Calculate how far we can go today
        drive_hours_today = remaining_driving_hours
        miles_today = (drive_hours_today / duration) * distance
        overnight_position = current_position + miles_today
        
        # Estimate overnight location
        overnight_location, _ = get_location_at_position(start_location, end_location, miles_today / distance)
        
        # Add overnight stop
        overnight_arrival = current_time + datetime.timedelta(hours=drive_hours_today)
        overnight_stop = RouteStop(
            trip=trip,
            location=overnight_location,
            arrival_time=overnight_arrival,
            departure_time=overnight_arrival + datetime.timedelta(hours=REQUIRED_REST_HOURS),
            stop_type='sleep',
            notes="Required 10-hour rest period"
        )
        overnight_stop.save()
        stops.append(overnight_stop)
        
        # Update time and hours
        current_time = overnight_arrival + datetime.timedelta(hours=REQUIRED_REST_HOURS)
        driving_hours_today = 0  # Reset for new day
        on_duty_hours_today = 0  # Reset for new day
        cycle_hours_used += drive_hours_today
        current_position = overnight_position
        
        # Process the rest of the segment tomorrow
        remaining_distance = distance - miles_today
        remaining_duration = duration - drive_hours_today
        
        return process_driving_segment(
            trip, stops, overnight_location, end_location,
            current_time, remaining_distance, remaining_duration,
            driving_hours_today, on_duty_hours_today, cycle_hours_used,
            current_position, last_fuel_position
        )
    
    # We can complete the segment today
    current_time += datetime.timedelta(hours=duration)
    driving_hours_today += duration
    on_duty_hours_today += duration
    cycle_hours_used += duration
    current_position += distance
    
    return current_time, driving_hours_today, on_duty_hours_today, cycle_hours_used, current_position, last_fuel_position

def get_location_at_position(start_location, end_location, ratio):
    """
    Estimate a location that's a certain ratio along the route from start to end
    
    This is a simple linear interpolation - in a real app, you'd use the actual route
    geometry from the routing API to find the exact location.
    """
    # Simple linear interpolation between start and end coordinates
    lat = start_location.latitude + (end_location.latitude - start_location.latitude) * ratio
    lon = start_location.longitude + (end_location.longitude - start_location.longitude) * ratio
    
    # Create or find a location object
    location_name = f"Stop at {ratio:.0%} between {start_location.name} and {end_location.name}"
    
    location, created = Location.objects.get_or_create(
        latitude=round(lat, 6),
        longitude=round(lon, 6),
        defaults={'name': location_name}
    )
    
    return location, created