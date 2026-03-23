from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import SensorReadingViewSet

router = DefaultRouter()
router.register(r"sensor-readings", SensorReadingViewSet, basename="sensorreading")

urlpatterns = [
    path("", include(router.urls)),
]