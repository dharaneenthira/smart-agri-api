from django.db import models
from farms.models import Farm

class DiseaseImage(models.Model):
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name="disease_images")
    image = models.FileField(upload_to="disease_images/")  # stable (no Pillow dependency)
    predicted_label = models.CharField(max_length=255, blank=True)
    confidence = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)