from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="dash_home"),
    path("alerts/", views.alerts_list, name="alerts_list"),

    path("farms/<int:farm_id>/", views.farm_detail, name="farm_detail"),
    path("farms/<int:farm_id>/fetch-weather/", views.fetch_weather, name="fetch_weather"),
    path("farms/<int:farm_id>/predict-disease/", views.predict_disease, name="predict_disease"),
    path("farms/<int:farm_id>/refresh-advisory/", views.refresh_advisory, name="refresh_advisory"),

    path("farms/<int:farm_id>/export-csv/", views.export_csv, name="export_csv"),
    path("farms/<int:farm_id>/export-pdf/", views.export_pdf, name="export_pdf"),
    path("farms/<int:farm_id>/crop-recommend/", views.crop_recommend, name="crop_recommend"),
    path("farms/<int:farm_id>/crop-history/", views.crop_history, name="crop_history"),
    path("farms/<int:farm_id>/seed-demo-data/", views.seed_demo_data, name="seed_demo_data"),
]