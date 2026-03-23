from django.db import models
from farms.models import Farm

class SensorReading(models.Model):
    SENSOR_TYPES = [
        ("soil_moisture", "Soil Moisture (%)"),
        ("air_temp", "Air Temp (°C)"),
        ("humidity", "Humidity (%)"),
    ]

    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name="readings")
    sensor_type = models.CharField(max_length=32, choices=SENSOR_TYPES)
    value = models.FloatField()
    unit = models.CharField(max_length=16, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.farm_id} {self.sensor_type}={self.value}"