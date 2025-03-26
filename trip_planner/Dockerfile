FROM python:3.9-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBUG=0
ENV SECRET_KEY=XX2hByOdctNWDJ0WNA_fuVNC9kBT26MTBtsU_xvQbsCrVic9cdEj9sfhiK2xQr3nPlo
ENV DATABASE_URL=postgresql://neondb_owner:npg_0TUYk5wLOMAC@ep-shrill-term-a82kk0f2-pooler.eastus2.azure.neon.tech/neondb?sslmode=require

# Set work directory
WORKDIR /app

# Install system dependencies including fonts
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir --upgrade pip

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Collect static files
RUN python manage.py collectstatic --noinput

# Run the application
CMD ["sh", "-c", "gunicorn trip_planner.wsgi:application --bind 0.0.0.0:8000"]