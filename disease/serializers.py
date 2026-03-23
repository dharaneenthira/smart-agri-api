from rest_framework import serializers
from .models import DiseaseImage

class DiseaseImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = DiseaseImage
        fields = "__all__"