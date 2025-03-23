import os
import datetime
from PIL import Image, ImageDraw, ImageFont
from django.conf import settings
from django.core.files.base import ContentFile
from io import BytesIO

def generate_log_image(daily_log):
    """Generate an image of the ELD log grid for a specific day"""
    # Create blank canvas for log grid
    width, height = 1000, 600
    image = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(image)
    
    # Try to load fonts
    try:
        font_regular = ImageFont.truetype("Arial.ttf", 12)
        font_bold = ImageFont.truetype("Arial Bold.ttf", 14)
    except IOError:
        # Fall back to default font if Arial not available
        font_regular = ImageFont.load_default()
        font_bold = ImageFont.load_default()
    
    # Draw header information
    draw.text((20, 20), f"Driver's Daily Log", font=font_bold, fill='black')
    draw.text((20, 40), f"Date: {daily_log.date.strftime('%m/%d/%Y')}", font=font_regular, fill='black')
    draw.text((20, 60), f"Driver: {daily_log.trip.driver.get_full_name()}", font=font_regular, fill='black')
    
    # Draw grid for 24-hour log
    grid_top = 120
    grid_height = 400
    grid_width = 900
    
    # Draw vertical time lines (one per hour)
    hours_per_day = 24
    for hour in range(hours_per_day + 1):
        x = 50 + (hour * (grid_width / hours_per_day))
        draw.line([(x, grid_top), (x, grid_top + grid_height)], fill='black', width=1)
        
        # Draw hour labels
        if hour < hours_per_day:
            time_label = f"{hour}:00"
            draw.text((x + 5, grid_top - 20), time_label, font=font_regular, fill='black')
    
    # Draw horizontal status lines
    statuses = ['OFF', 'SB', 'D', 'ON']
    status_height = grid_height / len(statuses)
    
    for i, status in enumerate(statuses):
        y = grid_top + (i * status_height)
        draw.line([(50, y), (50 + grid_width, y)], fill='black', width=1)
        draw.text((20, y + (status_height / 2) - 10), status, font=font_regular, fill='black')
    
    # Draw the bottom line
    draw.line([(50, grid_top + grid_height), (50 + grid_width, grid_top + grid_height)], fill='black', width=1)
    
    # Get all log entries for this day and plot them
    log_entries = daily_log.entries.all().order_by('start_time')
    
    for i, entry in enumerate(log_entries):
        # Skip entries with no end time (current entry)
        if not entry.end_time:
            continue
            
        # Calculate x-coordinates based on time
        start_minutes = (entry.start_time.hour * 60) + entry.start_time.minute
        end_minutes = (entry.end_time.hour * 60) + entry.end_time.minute
        
        # Handle entries crossing midnight
        if end_minutes < start_minutes:
            end_minutes = 24 * 60  # End at midnight
        
        start_x = 50 + (start_minutes * grid_width / (24 * 60))
        end_x = 50 + (end_minutes * grid_width / (24 * 60))
        
        # Determine y-coordinate based on status
        status_map = {
            'off_duty': 0,  # OFF
            'sleeper': 1,   # SB
            'driving': 2,   # D
            'on_duty': 3    # ON
        }
        
        status_idx = status_map.get(entry.status, 0)
        y_top = grid_top + (status_idx * status_height)
        
        # Draw the activity line
        if entry.status == 'driving':
            # Draw driving as a thick line
            draw.line([(start_x, y_top + status_height/2), (end_x, y_top + status_height/2)], fill='blue', width=4)
        else:
            # Draw other statuses as rectangles
            draw.rectangle([(start_x, y_top), (end_x, y_top + status_height)], fill='lightblue', outline='blue')
    
    # Add certification signature area
    draw.text((50, grid_top + grid_height + 20), "I hereby certify that my entries are true and correct:", font=font_regular, fill='black')
    draw.line([(300, grid_top + grid_height + 40), (600, grid_top + grid_height + 40)], fill='black', width=1)
    draw.text((400, grid_top + grid_height + 45), "Driver's Signature", font=font_regular, fill='black')
    
    # Save the image to a BytesIO object
    image_io = BytesIO()
    image.save(image_io, format='PNG')
    image_io.seek(0)
    
    # Create a unique filename
    filename = f"log_{daily_log.trip.id}_{daily_log.date.strftime('%Y%m%d')}.png"
    
    # Save the image to the model
    daily_log.log_image.save(filename, ContentFile(image_io.getvalue()), save=True)
    
    return daily_log.log_image.name

def generate_daily_logs_for_trip(trip):
    """
    Generate daily logs for entire trip based on route stops
    This function creates a DailyLog entry for each day of the trip
    and populates it with LogEntry objects based on the schedule
    """
    # Get all stops sorted by arrival time
    stops = trip.stops.all().order_by('arrival_time')
    
    if not stops:
        return []
    
    # Initialize tracking variables
    current_date = stops.first().arrival_time.date()
    end_date = stops.last().departure_time.date()
    current_status = 'off_duty'
    status_start_time = stops.first().arrival_time
    daily_logs = []
    
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
        
        # Process stops for this day
        for stop in stops.filter(arrival_time__date=current_date):
            # Create log entry for driving/on-duty to this stop
            if stop.arrival_time > status_start_time:
                # Determine status based on stop type
                status_to_stop = 'driving'  # Assume driving to all stops
                
                LogEntry.objects.create(
                    daily_log=daily_log,
                    start_time=status_start_time,
                    end_time=stop.arrival_time,
                    status=status_to_stop,
                    location=f"En route to {stop.location.name}",
                    remarks=f"Driving to {stop.get_stop_type_display()}"
                )
            
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
            LogEntry.objects.create(
                daily_log=daily_log,
                start_time=stop.arrival_time,
                end_time=stop.departure_time,
                status=new_status,
                location=stop.location.name,
                remarks=stop.notes
            )
            
            # Update tracking variables
            status_start_time = stop.departure_time
            current_status = new_status
        
        # Create log entry for time from last stop of the day until midnight
        day_end = datetime.datetime.combine(
            current_date, 
            datetime.time(23, 59, 59)
        ).replace(tzinfo=status_start_time.tzinfo)
        
        if status_start_time.date() == current_date and status_start_time < day_end:
            LogEntry.objects.create(
                daily_log=daily_log,
                start_time=status_start_time,
                end_time=day_end,
                status=current_status,
                location=stops.filter(departure_time__date=current_date).last().location.name,
                remarks="End of day"
            )
        
        # Generate the visual log
        generate_log_image(daily_log)
        
        daily_logs.append(daily_log)
        
        # Move to the next day
        current_date += datetime.timedelta(days=1)
        
        # If we have stops on the next day, set the start time to midnight
        if current_date <= end_date:
            status_start_time = datetime.datetime.combine(
                current_date,
                datetime.time(0, 0, 0)
            ).replace(tzinfo=status_start_time.tzinfo)
    
    return daily_logs

# Import models at the end to avoid circular imports
from .models import DailyLog, LogEntry