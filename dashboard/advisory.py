from sensors.models import SensorReading
from weather.models import WeatherSnapshot
from disease.models import DiseaseImage

def _latest_reading(farm, sensor_type: str):
    return (SensorReading.objects
            .filter(farm=farm, sensor_type=sensor_type)
            .order_by("-timestamp")
            .first())

def generate_advisory(farm):
    """
    Returns:
      risk_score (0-100)
      severity: low/medium/high
      advisories: list[str]
    """
    soil = _latest_reading(farm, "soil_moisture")
    temp = _latest_reading(farm, "air_temp")
    hum = _latest_reading(farm, "humidity")

    weather = WeatherSnapshot.objects.filter(farm=farm).order_by("-fetched_at").first()
    disease = DiseaseImage.objects.filter(farm=farm).order_by("-created_at").first()

    advisories = []
    risk = 0

    # Soil moisture rule
    if soil and soil.value < 30:
        advisories.append("Soil moisture is low. Recommend irrigation today (short cycle).")
        risk += 35
    elif soil and soil.value < 45:
        advisories.append("Soil moisture is moderate. Monitor; irrigate if no rain expected.")
        risk += 15
    else:
        advisories.append("Soil moisture looks OK. Avoid over-irrigation.")

    # Weather/humidity fungal risk
    # Use sensor humidity if present, else weather humidity
    humidity_val = hum.value if hum else (weather.humidity if weather and weather.humidity is not None else None)
    temp_val = temp.value if temp else (weather.temperature if weather and weather.temperature is not None else None)

    if humidity_val is not None and temp_val is not None:
        if humidity_val >= 80 and 18 <= temp_val <= 32:
            advisories.append("High fungal risk (high humidity + favorable temperature). Inspect leaves and ensure airflow.")
            risk += 35

    # Disease scan rule (mock or real)
    if disease and disease.predicted_label:
        label = disease.predicted_label.lower()
        if "healthy" not in label:
            advisories.append(f"Disease suspected: {disease.predicted_label}. Isolate affected plants and follow recommended treatment.")
            risk += 40

    # Clamp risk
    risk = max(0, min(100, risk))

    if risk >= 70:
        severity = "high"
    elif risk >= 40:
        severity = "medium"
    else:
        severity = "low"

    return risk, severity, advisories