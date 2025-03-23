from django.db import models
from django.contrib.auth.models import User

class Location(models.Model):
    name = models.CharField(max_length=255)
    latitude = models.FloatField()
    longitude = models.FloatField()
    address = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return self.name

class Trip(models.Model):
    STATUS_CHOICES = (
        ('planned', 'Planned'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    driver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='trips')
    current_location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name='trips_as_current')
    pickup_location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name='trips_as_pickup')
    dropoff_location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name='trips_as_dropoff')
    current_cycle_hours = models.FloatField(help_text="Current cycle hours used (in hours)")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='planned')
    
    def __str__(self):
        return f"Trip from {self.pickup_location} to {self.dropoff_location}"

class RouteStop(models.Model):
    STOP_TYPE_CHOICES = (
        ('rest', 'Required Rest'),
        ('fuel', 'Fuel Stop'),
        ('food', 'Food Break'),
        ('sleep', 'Sleep Break'),
        ('pickup', 'Pickup'),
        ('dropoff', 'Dropoff'),
    )
    
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='stops')
    location = models.ForeignKey(Location, on_delete=models.CASCADE)
    arrival_time = models.DateTimeField()
    departure_time = models.DateTimeField(null=True, blank=True)
    stop_type = models.CharField(max_length=20, choices=STOP_TYPE_CHOICES)
    notes = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.get_stop_type_display()} at {self.location}"

