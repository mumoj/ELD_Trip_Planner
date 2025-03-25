from rest_framework import serializers
from .models import DailyLog, LogEntry

class LogEntrySerializer(serializers.ModelSerializer):
    # Convert UTC times to strings, frontend will handle timezone conversion
    start_time = serializers.DateTimeField(format="%Y-%m-%dT%H:%M:%SZ")
    end_time = serializers.DateTimeField(format="%Y-%m-%dT%H:%M:%SZ")
                                         
    class Meta:
        model = LogEntry
        fields = ['id', 'start_time', 'end_time', 'status', 'location', 'remarks']

class DailyLogSerializer(serializers.ModelSerializer):
    entries = LogEntrySerializer(many=True, read_only=True)
    # Format date consistently for frontend 
    date = serializers.DateField(format="%Y-%m-%d")
    
    class Meta:
        model = DailyLog
        fields = ['id', 'trip', 'date', 'log_image', 'json_data', 'entries']