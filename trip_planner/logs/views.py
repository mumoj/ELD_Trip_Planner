from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from .models import DailyLog, LogEntry
from .serializers import DailyLogSerializer, LogEntrySerializer
from .log_generator import generate_log_image
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator


@method_decorator(csrf_exempt, name='dispatch')
class DailyLogViewSet(viewsets.ModelViewSet):
    queryset = DailyLog.objects.all()
    serializer_class = DailyLogSerializer
    permission_classes = [AllowAny]
    
    @action(detail=True, methods=['get'])
    def generate_image(self, request, pk=None):
        daily_log = self.get_object()
        
        # Generate the ELD log image
        log_image_path = generate_log_image(daily_log)
        
        # Update the model with the image path
        daily_log.log_image = log_image_path
        daily_log.save()
        
        return Response({
            'status': 'success',
            'image_url': daily_log.log_image.url
        })
        
@method_decorator(csrf_exempt, name='dispatch')
class LogEntryViewSet(viewsets.ModelViewSet):
    queryset = LogEntry.objects.all()
    serializer_class = LogEntrySerializer
    permission_classes = [AllowAny]