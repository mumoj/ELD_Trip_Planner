from rest_framework import serializers
from .models import Location, Trip, RouteStop

class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = ['id', 'name', 'latitude', 'longitude', 'address']

class RouteStopSerializer(serializers.ModelSerializer):
    location_details = LocationSerializer(source='location', read_only=True)
    
    class Meta:
        model = RouteStop
        fields = ['id', 'location', 'location_details', 'arrival_time', 'departure_time', 
                  'stop_type', 'notes']

class TripSerializer(serializers.ModelSerializer):
    stops = RouteStopSerializer(many=True, read_only=True)
    current_location_details = LocationSerializer(source='current_location', read_only=True)
    pickup_location_details = LocationSerializer(source='pickup_location', read_only=True)
    dropoff_location_details = LocationSerializer(source='dropoff_location', read_only=True)
    
    class Meta:
        model = Trip
        fields = ['id', 'driver', 'current_location', 'current_location_details',
                  'pickup_location', 'pickup_location_details',
                  'dropoff_location', 'dropoff_location_details',
                  'current_cycle_hours', 'created_at', 'updated_at',
                  'status', 'stops', 'client_timezone']
        read_only_fields = ['created_at', 'updated_at']
