# Trip Planner & ELD Logger Backend

![License](https://img.shields.io/badge/license-MIT-blue.svg)

A Django-based backend API for the Trip Planner & ELD Logger application. This service provides route planning, trip optimization, and automatic generation of ELD (Electronic Logging Device) logs that comply with Hours of Service (HOS) regulations.

## 🚚 Features

- **Intelligent Route Planning**: Calculates optimal routes between locations
- **HOS Compliance**: Automatically schedules required rest periods and breaks
- **ELD Log Generation**: Creates digital log entries for driver activities
- **Location Management**: Stores and manages location data
- **Trip Tracking**: Manages trips and their associated stops and logs

## 🖥️ Tech Stack

- **Django 3.2+**: Core web framework
- **Django REST Framework**: API development
- **PostgreSQL**: Database storage
- **OSRM**: Open Source Routing Machine for route calculations
- **WhiteNoise**: Static file serving
- **Gunicorn**: WSGI HTTP Server

## 🏗️ Project Structure

```
trip_planner/
├── logs/                # App for ELD log management
│   ├── log_generator.py # Logic for generating daily logs
│   ├── models.py        # DailyLog and LogEntry models
│   ├── serializers.py   # API serializers
│   └── views.py         # API endpoints
├── routes/              # App for route planning
│   ├── models.py        # Location, Trip, and RouteStop models
│   ├── route_planning.py # Route calculation logic
│   ├── serializers.py   # API serializers
│   └── views.py         # API endpoints
├── trip_planner/        # Project configuration
│   ├── settings.py      # Django settings
│   ├── urls.py          # URL routing
│   └── wsgi.py          # WSGI configuration
├── Dockerfile           # Container configuration
├── manage.py            # Django management script
└── requirements.txt     # Python dependencies
```

## 📝 Models

### Location
- **Fields**: `name`, `latitude`, `longitude`, `address`
- **Purpose**: Stores geographic locations for trip planning

### Trip
- **Fields**: `driver`, `current_location`, `pickup_location`, `dropoff_location`, `current_cycle_hours`, `status`, `client_timezone`
- **Relations**: User, multiple Locations
- **Purpose**: Represents a planned or ongoing trip

### RouteStop
- **Fields**: `trip`, `location`, `arrival_time`, `departure_time`, `stop_type`, `notes`
- **Relations**: Trip, Location
- **Purpose**: Individual stops along a trip route

### DailyLog
- **Fields**: `trip`, `date`, `log_image`, `json_data`
- **Relations**: Trip
- **Purpose**: Electronic logs for each day of a trip

### LogEntry
- **Fields**: `daily_log`, `start_time`, `end_time`, `status`, `location`, `remarks`
- **Relations**: DailyLog
- **Purpose**: Individual status entries within a daily log

## 🔌 API Endpoints

### Locations
- `GET /api/locations/` - List all locations
- `POST /api/locations/` - Create a new location
- `GET /api/locations/{id}/` - Retrieve a location
- `PUT /api/locations/{id}/` - Update a location
- `DELETE /api/locations/{id}/` - Delete a location

### Trips
- `GET /api/trips/` - List all trips
- `POST /api/trips/` - Create a new trip
- `GET /api/trips/{id}/` - Retrieve a trip
- `PUT /api/trips/{id}/` - Update a trip
- `DELETE /api/trips/{id}/` - Delete a trip
- `GET /api/trips/{id}/calculate_route/` - Calculate route and generate stops

### Route Stops
- `GET /api/stops/` - List all route stops
- `GET /api/stops/{id}/` - Retrieve a route stop

### Daily Logs
- `GET /api/daily-logs/` - List all daily logs
- `GET /api/daily-logs/{id}/` - Retrieve a daily log
- `GET /api/daily-logs/{id}/generate_image/` - Generate an ELD log image

### Log Entries
- `GET /api/log-entries/` - List all log entries
- `GET /api/log-entries/{id}/` - Retrieve a log entry

## ⚙️ Route Planning Logic

The backend uses a sophisticated algorithm to plan routes considering:

1. **Route Calculation**: Uses OSRM (Open Source Routing Machine) to calculate routes between locations
2. **Hours of Service Rules**:
   - Maximum 11 hours driving time per day
   - Maximum 14 hours on-duty time per day
   - Required 10-hour rest periods
   - 30-minute breaks after 8 hours of driving
   - 70-hour limit over 8 days
3. **Stop Generation**:
   - Creates rest stops at appropriate intervals
   - Schedules fuel stops approximately every 1000 miles
   - Adds required sleep periods according to HOS regulations
4. **Log Generation**:
   - Creates daily logs for each day of the trip
   - Records status changes (driving, on-duty, off-duty, sleeper berth)
   - Tracks locations and remarks for each status change

## 🚀 Getting Started

### Prerequisites
- Python 3.9+
- PostgreSQL

### Installation

1. Clone the repository
```bash
git clone https://github.com/yourname/trip-planner-backend.git
cd trip-planner-backend
```

2. Create and activate a virtual environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

4. Configure environment variables

Create a `.env` file in the root directory:
```
DEBUG=1
SECRET_KEY=your_secret_key
DATABASE_URL=postgresql://user:password@localhost/trip_planner
```

5. Run migrations
```bash
python manage.py migrate
```

6. Create a superuser
```bash
python manage.py createsuperuser
```

7. Start the development server
```bash
python manage.py runserver
```

The API will be available at http://localhost:8000/api/

### Docker Deployment

```bash
docker build -t trip-planner-backend .
docker run -p 8000:8000 -e DATABASE_URL=postgresql://user:password@host/trip_planner trip-planner-backend
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

