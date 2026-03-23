from django.db import models
from farms.models import Farm

class WeatherSnapshot(models.Model):
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name="weather_snapshots")
    temperature = models.FloatField(null=True, blank=True)
    humidity = models.FloatField(null=True, blank=True)
    description = models.CharField(max_length=255, blank=True)
    fetched_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.farm.name} @ {self.fetched_at}"