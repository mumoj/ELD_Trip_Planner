import datetime
import pytz


def generate_log_image(daily_log):
    """
    Placeholder function to maintain API compatibility.
    Actual image generation now happens client-side in React.
    """
    return None
   

def generate_daily_logs_for_trip(trip):
    """
    Generate daily logs for entire trip based on route stops
    This function creates a DailyLog entry for each day of the trip
    and populates it with LogEntry objects based on the schedule
    
    Parameters:
    trip - The Trip model instance
    """
    stops = trip.stops.all().order_by('arrival_time')
    client_tz = pytz.timezone(trip.client_timezone if trip.client_timezone else 'UTC')
    
    if not stops:
        return []
    
    # Initialize tracking variables
    current_date = stops.first().arrival_time.astimezone(client_tz).date()
    end_date = stops.last().departure_time.astimezone(client_tz).date()
    daily_logs = []
    
    first_stop = stops.first()
    current_status = 'driving'
    status_start_time = first_stop.arrival_time.astimezone(client_tz)
    
   
    # Track the pending status to carry over at midnight
    pending_midnight_status = None
    pending_midnight_location = None
    pending_midnight_remarks = None
    pending_midnight_status_end = None

    # Process each day
    while current_date <= end_date:
        # Create or get daily log for this date
        daily_log, created = DailyLog.objects.get_or_create(
            trip=trip,
            date=current_date,
            defaults={'json_data': {}}
        )
        
        # Clear existing entries if we're regenerating
        if not created:
            daily_log.entries.all().delete()
        
        # Check if there's a status carried over from the previous day
        if pending_midnight_status:
            # Create an entry from midnight to either the first stop of the day or when the status changes
            midnight_start = datetime.datetime.combine(
                current_date,
                datetime.time(0, 0, 0)
            ).replace(tzinfo=status_start_time.tzinfo)
            
            # Find the first stop of the day (if any)
            day_stops = [stop for stop in stops if stop.arrival_time.astimezone(client_tz).date() == current_date]
            day_stops = sorted(day_stops, key = lambda stop: stop.arrival_time)
            if day_stops:
                # The continued status ends at the first stop of the day
                first_stop_of_day = day_stops[0]
                
                if midnight_start < first_stop_of_day.arrival_time.astimezone(client_tz):
                    LogEntry.objects.create(
                        daily_log=daily_log,
                        start_time=midnight_start,
                        end_time=pending_midnight_status_end,
                        status=pending_midnight_status,
                        location=pending_midnight_location,
                        remarks=pending_midnight_remarks + " (continued from previous day)"
                    )
                    
                    # Update tracking variables to process remaining stops
                    status_start_time = pending_midnight_status_end
                    current_status = 'driving'
                    
            
            # Reset pending status as it's been handled
            pending_midnight_status = None
            pending_midnight_location = None
            pending_midnight_remarks = None
        
        # Process stops for this day
        day_stops = [stop for stop in stops if stop.arrival_time.astimezone(client_tz).date() == current_date]
        day_end = datetime.datetime.combine(current_date, datetime.time(23, 59, 59)).replace(tzinfo=status_start_time.tzinfo)
        for ind, stop in enumerate(day_stops):
            # Create log entry for driving/on-duty to this stop if coming from previous status
            if stop.arrival_time.astimezone(client_tz) > status_start_time and current_status == 'driving':
                # Driving to this stop
                driving_entry = LogEntry.objects.create(
                    daily_log=daily_log,
                    start_time=status_start_time,
                    end_time=stop.arrival_time,
                    status='driving',
                    location=f"En route to {stop.location.name}",
                    remarks=f"Driving to {stop.get_stop_type_display()}"
                )
                
                entry_end_time = driving_entry.end_time.astimezone(client_tz) 
                if entry_end_time.date() > current_date:
                    last_entry = driving_entry
                    status_start_time = entry_end_time
                    current_status = 'driving'
                    continue
                          
            # Determine status at stop
            if stop.stop_type == 'rest':
                new_status = 'off_duty'
            elif stop.stop_type == 'sleep':
                new_status = 'sleeper'
            elif stop.stop_type in ['pickup', 'dropoff', 'fuel']:
                new_status = 'on_duty'
            else:
                new_status = 'on_duty'
            
            # Create log entry for time at the stop
            last_entry = LogEntry.objects.create(
                daily_log=daily_log,
                start_time=stop.arrival_time,
                end_time=stop.departure_time,
                status=new_status,
                location=stop.location.name,
                remarks=stop.notes
            )
            
            if stop.stop_type == "dropoff":
                daily_logs.append(daily_log)
                return daily_logs
            
            if ind == len(day_stops)- 1 and last_entry.end_time.astimezone(client_tz) < day_end:
                last_entry = LogEntry.objects.create(
                    daily_log=daily_log,
                    start_time=stop.departure_time,
                    end_time=day_end,
                    status='driving',
                    location=f"En route",
                    remarks=f"Driving"
                )
                
                status_start_time = day_end +  datetime.timedelta(seconds=1)
                current_status = 'driving'
                continue
                
                
            
                
            # Update tracking variables
            status_start_time = stop.departure_time.astimezone(client_tz)
            current_status = 'driving'  # Assume driving after each stop unless it's the end of day
            current_remarks = f"Driving after {stop.get_stop_type_display()}"
    
        if status_start_time.date() > current_date:
            # Limit entry to midnight.
            last_entry.end_time = day_end
            last_entry.save()
            
            # If not the last day and we're still active, set pending status for next day
            if current_date < end_date:
                pending_midnight_status = last_entry.status
                pending_midnight_location = last_entry.location
                pending_midnight_remarks = last_entry.remarks
                pending_midnight_status_end = status_start_time
                
        daily_logs.append(daily_log)
        
        # Move to the next day
        current_date += datetime.timedelta(days=1)
    
    return daily_logs

# Import models at the end to avoid circular imports
from .models import DailyLog, LogEntry