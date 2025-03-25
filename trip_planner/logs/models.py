from django.db import models
from routes.models import Trip

class DailyLog(models.Model):
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='logs')
    date = models.DateField()
    log_image = models.ImageField(upload_to='eld_logs/', null=True, blank=True)
    json_data = models.JSONField(default=dict)
    
    class Meta:
        unique_together = ('trip', 'date')
    
    def __str__(self):
        return f"Log for {self.trip} on {self.date}"

class LogEntry(models.Model):
    STATUS_CHOICES = (
        ('off_duty', 'Off Duty'),
        ('sleeper', 'Sleeper Berth'),
        ('driving', 'Driving'),
        ('on_duty', 'On Duty Not Driving'),
    )
    
    daily_log = models.ForeignKey(DailyLog, on_delete=models.CASCADE, related_name='entries')
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    location = models.CharField(max_length=255, blank=True, null=True)
    remarks = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.get_status_display()} from {self.start_time} to {self.end_time}"
    
    
