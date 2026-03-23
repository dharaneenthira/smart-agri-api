from rest_framework import viewsets
from .models import SensorReading
from .serializers import SensorReadingSerializer

class SensorReadingViewSet(viewsets.ModelViewSet):
    queryset = SensorReading.objects.all().order_by("-timestamp")
    serializer_class = SensorReadingSerializer