from rest_framework import serializers
from .models import DailyLog, LogEntry

class LogEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = LogEntry
        fields = ['id', 'start_time', 'end_time', 'status', 'location', 'remarks']

class DailyLogSerializer(serializers.ModelSerializer):
    entries = LogEntrySerializer(many=True, read_only=True)
    
    class Meta:
        model = DailyLog
        fields = ['id', 'trip', 'date', 'log_image', 'json_data', 'entries']