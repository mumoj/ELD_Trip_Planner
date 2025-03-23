import requests
import datetime
from .models import RouteStop, Location
from django.conf import settings
from django.utils import timezone

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
    
    # Extract the detailed route geometry coordinates
    current_to_pickup_coordinates = current_to_pickup_data['routes'][0]['geometry']['coordinates']
    
    # Pickup to dropoff
    pickup_to_dropoff_url = f"{base_url}{pickup_location.longitude},{pickup_location.latitude};"
    pickup_to_dropoff_url += f"{dropoff_location.longitude},{dropoff_location.latitude}?overview=full&geometries=geojson"
    
    # Make API request
    response = requests.get(pickup_to_dropoff_url)
    pickup_to_dropoff_data = response.json()
    
    # Extract the detailed route geometry coordinates
    pickup_to_dropoff_coordinates = pickup_to_dropoff_data['routes'][0]['geometry']['coordinates']
    
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
        'coordinates': {
            'current_to_pickup': current_to_pickup_coordinates,
            'pickup_to_dropoff': pickup_to_dropoff_coordinates
        },
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
    current_time = timezone.make_aware(current_time)
    
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
    
    # SEGMENT 1: Current location to pickup
    distance_to_pickup = route_data['current_to_pickup']['distance_miles']
    duration_to_pickup = route_data['current_to_pickup']['duration_hours']
    coordinates_section1 = route_data['coordinates']['current_to_pickup']
    
    # Process segment iteratively instead of recursively
    segment_result = process_segment_iteratively(
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
        last_fuel_position,
        coordinates_section1
    )
    
    current_time = segment_result['current_time']
    driving_hours_today = segment_result['driving_hours_today']
    on_duty_hours_today = segment_result['on_duty_hours_today']
    cycle_hours_used = segment_result['cycle_hours_used']
    current_position = segment_result['current_position']
    last_fuel_position = segment_result['last_fuel_position']
    
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
    
    # SEGMENT 2: Pickup to dropoff
    distance_to_dropoff = route_data['pickup_to_dropoff']['distance_miles']
    duration_to_dropoff = route_data['pickup_to_dropoff']['duration_hours']
    coordinates_section2 = route_data['coordinates']['pickup_to_dropoff']
    
    # Process segment iteratively
    segment_result = process_segment_iteratively(
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
        last_fuel_position,
        coordinates_section2
    )
    
    current_time = segment_result['current_time']
    
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

def process_segment_iteratively(trip, stops, start_location, end_location, 
                               current_time, total_distance, total_duration, 
                               driving_hours_today, on_duty_hours_today, cycle_hours_used, 
                               current_position, last_fuel_position, coordinates):
    """
    Process a driving segment iteratively (not recursively) with potential breaks
    """
    # Initialize variables for tracking progress
    distance_covered = 0
    time_spent = 0
    current_location = start_location
    
    # Continue until segment is complete
    while distance_covered < total_distance:
        # Calculate remaining portions
        remaining_distance = total_distance - distance_covered
        remaining_duration = (remaining_distance / total_distance) * total_duration
        
        # Check for driver hours limits
        remaining_driving_hours = min(MAX_DRIVING_HOURS - driving_hours_today, MAX_ON_DUTY_HOURS - on_duty_hours_today)
        
        # Need a break?
        
        last_rest_stop = RouteStop.objects.filter(trip=trip, stop_type__in=["rest", "fuel"]).order_by('-pk').first()
        last_rest_location = getattr(last_rest_stop, 'location', None)
        if driving_hours_today > 0 and driving_hours_today + remaining_duration > MAX_DRIVING_BEFORE_BREAK and current_location != last_rest_location:
            # Calculate when the break is needed
            break_point = MAX_DRIVING_BEFORE_BREAK - driving_hours_today
            break_distance = (break_point / remaining_duration) * remaining_distance
            
            # Find exact break location using coordinates
            break_ratio = (distance_covered + break_distance) / total_distance
            break_location = get_location_at_position(start_location, end_location, break_ratio, coordinates)
            
            # Update progress
            distance_covered += break_distance
            current_position += break_distance
            time_spent += break_point
            
            # Add break stop
            break_stop_time = current_time + datetime.timedelta(hours=break_point)
            break_stop = RouteStop(
                trip=trip,
                location=break_location,
                arrival_time=break_stop_time,
                departure_time=break_stop_time + datetime.timedelta(hours=0.5),  # 30-minute break
                stop_type='rest',
                notes="Required 30-minute break"
            )
            break_stop.save()
            stops.append(break_stop)
            
            
            
            # Update time and hours
            current_time = break_stop_time + datetime.timedelta(hours=0.5)
            driving_hours_today += break_point
            on_duty_hours_today += break_point + 0.5
            cycle_hours_used += break_point + 0.5
            current_location = break_location
            
            continue
        
        # Need fueling?
        if current_position - last_fuel_position >= FUELING_INTERVAL_MILES - 100:  # 100 mile buffer
            # Add fuel after a bit more driving
            fuel_miles = min(100, remaining_distance)  # Don't go past the destination
            
            # Find exact fuel location using coordinates
            fuel_ratio = (distance_covered + fuel_miles) / total_distance
            fuel_location = get_location_at_position(start_location, end_location, fuel_ratio, coordinates)
            
            # Calculate driving time to fuel location
            fuel_driving_time = (fuel_miles / remaining_distance) * remaining_duration
            
            # Update progress
            distance_covered += fuel_miles
            current_position += fuel_miles
            time_spent += fuel_driving_time
            
            # Add fuel stop
            fuel_stop_time = current_time + datetime.timedelta(hours=fuel_driving_time)
            fuel_stop = RouteStop(
                trip=trip,
                location=fuel_location,
                arrival_time=fuel_stop_time,
                departure_time=fuel_stop_time + datetime.timedelta(hours=0.75),  # 45 minutes for fueling
                stop_type='fuel',
                notes="Scheduled refueling"
            )
            fuel_stop.save()
            stops.append(fuel_stop)
            
            # Update time and hours
            current_time = fuel_stop_time + datetime.timedelta(hours=0.75)
            driving_hours_today += fuel_driving_time
            on_duty_hours_today += fuel_driving_time + 0.75
            cycle_hours_used += fuel_driving_time + 0.75
            current_location = fuel_location
            last_fuel_position = current_position
            
            continue
        
        # Can we complete the segment within today's hours?
        if remaining_duration > remaining_driving_hours:
            # Calculate how far we can go today
            drivable_hours = remaining_driving_hours
            drivable_distance = (drivable_hours / remaining_duration) * remaining_distance
            
            # Find exact overnight location using coordinates
            overnight_ratio = (distance_covered + drivable_distance) / total_distance
            overnight_location = get_location_at_position(start_location, end_location, overnight_ratio, coordinates)
            
            # Update progress
            distance_covered += drivable_distance
            current_position += drivable_distance
            time_spent += drivable_hours
            
            # Add overnight stop
            overnight_arrival = current_time + datetime.timedelta(hours=drivable_hours)
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
            
            # Update time and reset hours for new day
            current_time = overnight_arrival + datetime.timedelta(hours=REQUIRED_REST_HOURS)
            driving_hours_today = 0  # Reset for new day
            on_duty_hours_today = 0  # Reset for new day
            cycle_hours_used += drivable_hours
            current_location = overnight_location
            
            continue
        
        # We can complete the remainder of the segment
        current_time += datetime.timedelta(hours=remaining_duration)
        driving_hours_today += remaining_duration
        on_duty_hours_today += remaining_duration
        cycle_hours_used += remaining_duration
        current_position += remaining_distance
        
        # We've completed the segment
        distance_covered = total_distance
    
    # Return updated state
    return {
        'current_time': current_time,
        'driving_hours_today': driving_hours_today,
        'on_duty_hours_today': on_duty_hours_today,
        'cycle_hours_used': cycle_hours_used,
        'current_position': current_position,
        'last_fuel_position': last_fuel_position
    }

def get_location_at_position(start_location, end_location, ratio, coordinates):
    """
    Get an exact location that's a certain ratio along the route using the actual route coordinates
    
    Args:
        start_location: Starting location object
        end_location: Ending location object
        ratio: Position ratio along the route (0.0 to 1.0)
        coordinates: List of [lon, lat] coordinates from the routing API
    
    Returns:
        Location object at the specified position
    """
    # Check if we're at the start or end
    if ratio <= 0:
        return start_location
    if ratio >= 1:
        return end_location
    
    # Get the actual coordinates at the specified ratio along the route
    total_points = len(coordinates)
    point_index = int(ratio * (total_points - 1))
    
    # Get the coordinates
    lon, lat = coordinates[point_index]
    
    # Create or find a location object
    location_name = f"Stop at {ratio:.0%} between {start_location.name} and {end_location.name}"
    
    location, created = Location.objects.get_or_create(
        latitude=round(lat, 6),
        longitude=round(lon, 6),
        defaults={'name': location_name}
    )
    
    return location