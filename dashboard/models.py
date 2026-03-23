from django.db import models
from farms.models import Farm


class Alert(models.Model):
    SEVERITY = [
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
    ]

    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name="alerts")
    severity = models.CharField(max_length=10, choices=SEVERITY, default="low")
    title = models.CharField(max_length=120)
    message = models.TextField()

    resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["farm", "created_at"]),
            models.Index(fields=["severity", "created_at"]),
        ]

    def __str__(self):
        return f"{self.farm.name} [{self.severity}] {self.title}"


class CropRecommendation(models.Model):
    """
    Stores crop recommendation requests + top results (history).
    """
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name="crop_recommendations")

    soil_moisture = models.FloatField(help_text="Soil moisture (%) entered by farmer or from sensor")
    month = models.IntegerField(help_text="1-12")
    irrigation = models.BooleanField(default=False)

    top_crop = models.CharField(max_length=120)
    results_json = models.JSONField(help_text="Top N recommendations with scores/reasons")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["farm", "created_at"]),
        ]

    def __str__(self):
        return f"{self.farm.name} -> {self.top_crop} ({self.created_at:%Y-%m-%d})"