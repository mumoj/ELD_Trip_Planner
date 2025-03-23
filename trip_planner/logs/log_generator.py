import os
import datetime
from PIL import Image, ImageDraw, ImageFont
from django.conf import settings
from django.core.files.base import ContentFile
from io import BytesIO
import math

def generate_log_image(daily_log):
    """Generate an image of the ELD log grid for a specific day, resembling standard DOT driver logs"""
    width, height = 1100, 550  # Increased width from 1000 to 1100
    image = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(image)
    
    # Font configuration - using Liberation Sans instead of Arial
    font_path = os.path.join(settings.BASE_DIR, 'logs', 'fonts')
    
    try:
        # Liberation Sans fonts
        font_regular = ImageFont.truetype(os.path.join(font_path, "LiberationSans-Regular.ttf"), 14)
        font_bold = ImageFont.truetype(os.path.join(font_path, "LiberationSans-Bold.ttf"), 16)
        font_small = ImageFont.truetype(os.path.join(font_path, "LiberationSans-Regular.ttf"), 10)
    except IOError:
        # Fall back to default font if Liberation Sans not available
        print("Liberation Sans fonts not found, using default fonts")
        font_regular = ImageFont.load_default()
        font_bold = ImageFont.load_default()
        font_small = ImageFont.load_default()
    
    # Draw minimal header - without splitting line
    draw.rectangle([(0, 0), (width, 60)], outline='black', width=1)
    
    # Left header - simplified
    draw.text((10, 10), "U.S. DEPARTMENT OF TRANSPORTATION", font=font_small, fill='black')
    
    # Format date as MM DD YYYY
    date_str = daily_log.date.strftime("%m %d %Y")
    date_parts = date_str.split()
    
    # Draw date with minimal boxes
    date_box_left = 50
    date_spacing = 60
    
    draw.text((date_box_left, 30), f"{date_parts[0]}", font=font_bold, fill='black')
    draw.text((date_box_left + date_spacing, 30), f"{date_parts[1]}", font=font_bold, fill='black')
    draw.text((date_box_left + date_spacing*2, 30), f"{date_parts[2]}", font=font_bold, fill='black')
    
    draw.text((date_box_left, 45), "(MONTH)", font=font_small, fill='black')
    draw.text((date_box_left + date_spacing, 45), "(DAY)", font=font_small, fill='black')
    draw.text((date_box_left + date_spacing*2, 45), "(YEAR)", font=font_small, fill='black')
    
    # Center header - with aligned text
    # Calculate position to start both lines at the same position
    subtitle_text = "(ONE CALENDAR DAY — 24 HOURS)"
    title_text = "DRIVER'S DAILY LOG"
    
    # Calculate width of text
    subtitle_width = len(subtitle_text) * 6  # Approximate width based on font
    title_width = len(title_text) * 10  # Approximate width based on font
    
    # Center the text block as a whole, but align the left edges
    text_block_center = width // 2
    text_block_left = text_block_center - (subtitle_width // 2)
    
    # Draw both texts aligned to the left edge
    draw.text((text_block_left, 20), title_text, font=font_bold, fill='black')
    draw.text((text_block_left, 40), subtitle_text, font=font_small, fill='black')
    
    # Right header - simplified
    draw.text((width//2 + 150, 20), "ORIGINAL — Submit to carrier within 13 days", font=font_small, fill='black')
    draw.text((width//2 + 150, 40), "DUPLICATE — Driver retains possession for eight days", font=font_small, fill='black')
    
    # Minimal driver info section
    draw.line([(0, 60), (width, 60)], fill='black', width=1)
    
    # Get carrier name
    carrier_name = f"{daily_log.trip.driver.last_name}'s Transportation"
    draw.text((20, 75), carrier_name, font=font_bold, fill='black')
    draw.text((20, 95), "(NAME OF CARRIER OR CARRIERS)", font=font_small, fill='black')
    
    # Driver signature - simplified
    driver_name = daily_log.trip.driver.get_full_name()
    draw.text((width - 250, 75), driver_name, font=font_bold, fill='black')
    draw.text((width - 250, 95), "(DRIVER'S SIGNATURE IN FULL)", font=font_small, fill='black')
    
    # Hour grid section - increased space between header and grid
    grid_top = 150
    grid_height = 320
    
    # Grid dimensions - adjusted for wider canvas
    grid_left = 100
    grid_right = width - 120  # Increased right margin for time display
    grid_width = grid_right - grid_left
    
    # Draw the time grid header
    draw.line([(0, grid_top), (width, grid_top)], fill='black', width=1)
    
    # Status labels on left side
    statuses = [
        ("Off\nDuty", 0), 
        ("Sleeper\nBerth", 1), 
        ("Driving", 2), 
        ("On Duty\n(Not\nDriving)", 3)
    ]
    
    # Calculate row heights
    row_height = grid_height / 4
    
    # Draw the hour markings across the top - minimal design
    hours_text_y = grid_top - 15
    
    # Draw hour marks (0, 2, 4, 6, ..., 22, 24)
    for i in range(0, 25, 2):
        x = grid_left + (i * grid_width / 24)
        # Draw vertical tick mark
        draw.line([(x, grid_top - 5), (x, grid_top)], fill='black', width=1)
        
        # Hour text
        if i == 0 or i == 24:
            hour_text = "Midnight"
        elif i == 12:
            hour_text = "Noon" 
        else:
            hour_text = str(i)
            
        # Position text to avoid overlap
        text_width = len(hour_text) * 4
        draw.text((x - text_width/2, hours_text_y), hour_text, font=font_small, fill='black')
    
    # Draw the grid for status tracking
    for i in range(5):  # 4 status rows + bottom line
        y = grid_top + (i * row_height)
        draw.line([(grid_left, y), (grid_right, y)], fill='black', width=1)
    
    # Draw vertical grid lines
    for i in range(25):  # 0 to 24 hours
        x = grid_left + (i * grid_width / 24)
        
        # Main lines at even hours
        if i % 2 == 0:
            draw.line([(x, grid_top), (x, grid_top + grid_height)], fill='black', width=1)
        # Short tick marks at odd hours
        else:
            for j in range(4):
                tick_y = grid_top + (j * row_height)
                tick_length = 5
                # Top tick
                draw.line([(x, tick_y), (x, tick_y + tick_length)], fill='black', width=1)
                # Bottom tick
                draw.line([(x, tick_y + row_height - tick_length), (x, tick_y + row_height)], fill='black', width=1)
    
    # Draw status labels
    for i, (label, idx) in enumerate(statuses):
        y = grid_top + (i * row_height) + (row_height / 2) - 15
        draw.text((20, y), label, font=font_regular, fill='black')
    
    
    # Process log entries and draw status lines
    status_map = {
        'off_duty': 0,
        'sleeper': 1,
        'driving': 2,
        'on_duty': 3
    }
    
    # Track hours by status
    hours_by_status = {
        'off_duty': 0,
        'sleeper': 0,
        'driving': 0,
        'on_duty': 0
    }
    
    # Sort log entries by start time
    log_entries = daily_log.entries.all().order_by('start_time')
    
    # Group entries by status to create continuous lines
    status_segments = {
        'off_duty': [],
        'sleeper': [],
        'driving': [],
        'on_duty': []
    }
    
    # Process all entries to identify continuous segments by status
    for entry in log_entries:
        if not entry.end_time:
            continue
            
        # Calculate position on grid
        start_minutes = (entry.start_time.hour * 60) + entry.start_time.minute
        end_minutes = (entry.end_time.hour * 60) + entry.end_time.minute
        
        # Handle entries crossing midnight
        if end_minutes < start_minutes:
            end_minutes = 24 * 60  # End at midnight
        
        start_x = grid_left + (start_minutes * grid_width / (24 * 60))
        end_x = grid_left + (end_minutes * grid_width / (24 * 60))
        
        # Calculate duration in hours with seconds precision
        duration_seconds = (end_minutes - start_minutes) * 60  # Convert minutes to seconds
        duration_hours = duration_seconds / 3600  # Convert seconds to hours
        hours_by_status[entry.status] += duration_hours
        
        # Add segment to appropriate status group
        status_segments[entry.status].append((start_x, end_x))
    
    # Merge adjacent or overlapping segments by status
    for status, segments in status_segments.items():
        if not segments:
            continue
            
        # Sort segments by start time
        sorted_segments = sorted(segments, key=lambda x: x[0])
        
        # Merge overlapping segments
        merged_segments = []
        current_segment = sorted_segments[0]
        
        for next_segment in sorted_segments[1:]:
            # If segments touch or overlap, merge them
            if next_segment[0] <= current_segment[1]:
                current_segment = (current_segment[0], max(current_segment[1], next_segment[1]))
            else:
                # No overlap, add current segment and start a new one
                merged_segments.append(current_segment)
                current_segment = next_segment
                
        # Add the last segment
        merged_segments.append(current_segment)
        
        # Draw continuous blue line for each merged segment
        status_idx = status_map.get(status, 0)
        y_pos = grid_top + (status_idx * row_height) + (row_height / 2)
        
        for start_x, end_x in merged_segments:
            draw.line([(start_x, y_pos), (end_x, y_pos)], fill='blue', width=3)
    
    # Helper function to convert decimal hours to HH:MM:SS format
    def format_hours_to_hhmmss(hours):
        total_seconds = int(hours * 3600)
        hours_part = total_seconds // 3600
        minutes_part = (total_seconds % 3600) // 60
        seconds_part = total_seconds % 60
        return f"{hours_part:02d}:{minutes_part:02d}:{seconds_part:02d}"
    
    # Draw the total hours on right side in HH:MM:SS format
    for i, status in enumerate(['off_duty', 'sleeper', 'driving', 'on_duty']):
        hours = hours_by_status[status]
        y_pos = grid_top + (i * row_height) + (row_height / 2) - 5
        
        # Format hours as HH:MM:SS
        formatted_hours = format_hours_to_hhmmss(hours)
        draw.text((grid_right + 15, y_pos), formatted_hours, font=font_bold, fill='black')
    
    # Draw total of all hours in HH:MM:SS format
    total_hours = sum(hours_by_status.values())
    formatted_total = format_hours_to_hhmmss(total_hours)
    draw.text((grid_right + 15, grid_top + grid_height + 10), f"={formatted_total}", font=font_bold, fill='black')
    
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
    stops = trip.stops.all().order_by('arrival_time')
    
    if not stops:
        return []
    
    # Initialize tracking variables
    current_date = stops.first().arrival_time.date()
    end_date = stops.last().departure_time.date()
    daily_logs = []
    
    # Check if the first stop is the initial "Trip start" rest stop
    first_stop = stops.first()
    if first_stop.stop_type == 'rest' and "Trip start" in (first_stop.notes or ""):
        # This is the initial preparation stop
        current_status = 'off_duty'  # Log as off-duty during preparation
        status_start_time = first_stop.arrival_time
        
        # Get or create the daily log for this date
        daily_log, created = DailyLog.objects.get_or_create(
            trip=trip,
            date=current_date,
            defaults={'json_data': {}}
        )
        
        # Clear existing entries if we're regenerating
        if not created:
            daily_log.entries.all().delete()
        
        # Create log entry for the preparation time
        LogEntry.objects.create(
            daily_log=daily_log,
            start_time=first_stop.arrival_time,
            end_time=first_stop.departure_time,
            status='off_duty',
            location=first_stop.location.name,
            remarks="Pre-trip inspection and preparation"
        )
        
        # Set up for the driving segment that follows
        current_status = 'driving'
        status_start_time = first_stop.departure_time
    else:
        # No initial preparation stop found, start with driving
        current_status = 'driving'
        status_start_time = first_stop.arrival_time
    
    # Process each day
    while current_date <= end_date:
        # Create or get daily log for this date
        daily_log, created = DailyLog.objects.get_or_create(
            trip=trip,
            date=current_date,
            defaults={'json_data': {}}
        )
        
        # Clear existing entries if we're regenerating and we haven't just created entries
        if not created and current_status != 'driving':
            daily_log.entries.all().delete()
        
        # Process stops for this day
        for stop in stops.filter(arrival_time__date=current_date):
            # Create log entry for driving/on-duty to this stop if coming from previous status
            if stop.arrival_time > status_start_time and current_status == 'driving':
                # Driving to this stop
                LogEntry.objects.create(
                    daily_log=daily_log,
                    start_time=status_start_time,
                    end_time=stop.arrival_time,
                    status='driving',
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
            current_status = 'driving'  # Assume driving after each stop unless it's the end of day
        
        # Create log entry for time from last stop of the day until midnight
        day_end = datetime.datetime.combine(
            current_date, 
            datetime.time(23, 59, 59)
        ).replace(tzinfo=status_start_time.tzinfo)
        
        if status_start_time.date() == current_date and status_start_time < day_end:
            # Check if this is the last stop of the entire trip
            is_last_stop = current_date == end_date and status_start_time >= stops.last().departure_time
            
            # If last stop of trip, driver stays at location (off_duty)
            # Otherwise, continue driving to next destination
            end_of_day_status = 'off_duty' if is_last_stop else current_status
            
            LogEntry.objects.create(
                daily_log=daily_log,
                start_time=status_start_time,
                end_time=day_end,
                status=end_of_day_status,
                location=stops.filter(departure_time__date=current_date).last().location.name,
                remarks="End of day" if not is_last_stop else "Trip completed"
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