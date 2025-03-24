from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from .models import Location, Trip, RouteStop
from .serializers import LocationSerializer, TripSerializer, RouteStopSerializer
from .route_planning import calculate_route, generate_stops
from logs.log_generator import generate_daily_logs_for_trip
from logs.serializers import DailyLogSerializer
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

@method_decorator(csrf_exempt, name='dispatch')
class LocationViewSet(viewsets.ModelViewSet):
    queryset = Location.objects.all()
    serializer_class = LocationSerializer
    permission_classes = [AllowAny]

@method_decorator(csrf_exempt, name='dispatch')
class TripViewSet(viewsets.ModelViewSet):
    queryset = Trip.objects.all()
    serializer_class = TripSerializer
    permission_classes = [AllowAny]
    
    @action(detail=True, methods=['get'])
    def calculate_route(self, request, pk=None):
        trip = self.get_object()
        
        # Calculate the route between locations
        route_data = calculate_route(
            trip.current_location, 
            trip.pickup_location,
            trip.dropoff_location,
            trip.current_cycle_hours
        )
        
        # Generate stops based on HOS regulations
        stops = generate_stops(trip, route_data)
        daily_logs = generate_daily_logs_for_trip(trip)
        
        
        # Return route data and stops
        return Response({
            'route': route_data,
            'stops': RouteStopSerializer(stops, many=True).data,
            'daily_logs':  DailyLogSerializer(daily_logs, many=True).data
        })
        
@method_decorator(csrf_exempt, name='dispatch')
class RouteStopViewSet(viewsets.ModelViewSet):
    queryset = RouteStop.objects.all()
    serializer_class = RouteStopSerializer
    permission_classes = [AllowAny]
