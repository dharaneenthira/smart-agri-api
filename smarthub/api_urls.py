from rest_framework.routers import DefaultRouter

from farms.views import FarmViewSet
from sensors.views import SensorReadingViewSet
from weather.views import WeatherViewSet
from disease.views import DiseaseImageViewSet

router = DefaultRouter()
router.register(r"farms", FarmViewSet, basename="farm")
router.register(r"sensor-readings", SensorReadingViewSet, basename="sensorreading")
router.register(r"weather", WeatherViewSet, basename="weather")
router.register(r"disease-images", DiseaseImageViewSet, basename="diseaseimage")

urlpatterns = router.urls