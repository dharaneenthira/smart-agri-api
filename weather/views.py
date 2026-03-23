import os
import requests
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from farms.models import Farm
from .models import WeatherSnapshot
from .serializers import WeatherSnapshotSerializer

class WeatherViewSet(viewsets.ModelViewSet):
    queryset = WeatherSnapshot.objects.all().order_by("-fetched_at")
    serializer_class = WeatherSnapshotSerializer

    @action(detail=False, methods=["post"])
    def fetch(self, request):
        farm_id = request.data.get("farm_id") or request.data.get("farm")
        if not farm_id:
         return Response({"error": "Send farm_id (JSON) or farm (HTML form dropdown)."}, status=400)

        try:
            farm = Farm.objects.get(pk=farm_id)
        except Farm.DoesNotExist:
            return Response({"error": "Farm not found"}, status=404)

        # OFFLINE-SAFE fallback
        api_key = os.getenv("OPENWEATHER_API_KEY", "")
        if not api_key or farm.latitude is None or farm.longitude is None:
            snap = WeatherSnapshot.objects.create(
                farm=farm,
                temperature=28.5,
                humidity=65,
                description="Mock weather (offline-safe)"
            )
            return Response(WeatherSnapshotSerializer(snap).data, status=201)

        # Online mode
        try:
            url = "https://api.openweathermap.org/data/2.5/weather"
            params = {
                "lat": farm.latitude,
                "lon": farm.longitude,
                "appid": api_key,
                "units": "metric",
            }
            data = requests.get(url, params=params, timeout=10).json()
            snap = WeatherSnapshot.objects.create(
                farm=farm,
                temperature=data.get("main", {}).get("temp"),
                humidity=data.get("main", {}).get("humidity"),
                description=(data.get("weather", [{}])[0].get("description", "")),
            )
            return Response(WeatherSnapshotSerializer(snap).data, status=201)
        except Exception as e:
            # fallback if internet fails at venue
            snap = WeatherSnapshot.objects.create(
                farm=farm,
                temperature=28.0,
                humidity=60,
                description=f"Fallback due to API error: {e}"
            )
            return Response(WeatherSnapshotSerializer(snap).data, status=201)