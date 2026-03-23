from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import DiseaseImageViewSet

router = DefaultRouter()
router.register(r"disease-images", DiseaseImageViewSet, basename="diseaseimage")

urlpatterns = [path("", include(router.urls))]