from rest_framework import viewsets
from .models import Farm
from .serializers import FarmSerializer

class FarmViewSet(viewsets.ModelViewSet):
    queryset = Farm.objects.all().order_by("-id")
    serializer_class = FarmSerializer