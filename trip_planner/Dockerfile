FROM python:3.9-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBUG=0

# Set work directory
WORKDIR /app

# Install system dependencies including fonts
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libjpeg-dev \
    zlib1g-dev \
    fonts-liberation \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir --upgrade pip

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Make sure the directory for SQLite exists and is writable
RUN mkdir -p /app/data && chmod 777 /app/data

# Create fonts directory and copy Liberation fonts
RUN mkdir -p /app/logs/fonts
RUN cp /usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf /app/logs/fonts/
RUN cp /usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf /app/logs/fonts/

# Create media directory with proper permissions
RUN mkdir -p /app/media && chmod 777 /app/media

# Collect static files
RUN python manage.py collectstatic --noinput

# Run the application
CMD ["sh", "-c", "python manage.py migrate && gunicorn trip_planner.wsgi:application --bind 0.0.0.0:8000"]