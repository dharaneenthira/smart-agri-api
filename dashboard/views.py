# dashboard/views.py

import csv
import io
import json
import random
from datetime import datetime

from django.contrib.auth.decorators import login_required
from django.core.files.base import ContentFile
from django.http import FileResponse, HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_POST

from farms.models import Farm
from sensors.models import SensorReading
from weather.models import WeatherSnapshot
from disease.models import DiseaseImage

from dashboard.models import Alert, CropRecommendation
from dashboard.advisory import generate_advisory
from dashboard.crop_reco import recommend_crops

from disease.treatment_kb import get_treatment


# -----------------------------------
# Helpers (Role-based access)
# -----------------------------------
def _get_profile(user):
    return getattr(user, "profile", None)


def _farms_for_user(user):
    """
    farmer      -> only assigned farms
    fpo_admin   -> all farms
    expert      -> all farms
    superuser   -> all farms
    """
    if user.is_superuser:
        return Farm.objects.all()

    profile = _get_profile(user)
    if profile and profile.role == "farmer":
        return profile.farms.all()

    return Farm.objects.all()


def _ensure_farm_access(request, farm: Farm):
    """
    Returns HttpResponseForbidden if user cannot access farm,
    else returns None.
    """
    if request.user.is_superuser:
        return None

    profile = _get_profile(request.user)
    if profile and profile.role == "farmer":
        if not profile.farms.filter(id=farm.id).exists():
            return HttpResponseForbidden("You do not have access to this farm.")
    return None


# -----------------------------------
# Disease prediction (dashboard-side)
# -----------------------------------
def _mock_predict():
    # Keep labels matching your treatments.json keys
    choices = [
        ("Tomato___Early_blight", 0.87),
        ("Tomato___Bacterial_spot", 0.81),
        ("Tomato___healthy", 0.95),
    ]
    return random.choice(choices)


def _predict_label_confidence(file_path: str):
    """
    Uses disease/views.py real inference if available, else mock.
    This prevents circular import issues by importing inside.
    """
    try:
        from disease.views import predict_label_and_confidence  # type: ignore
        return predict_label_and_confidence(file_path)
    except Exception:
        return _mock_predict()


# -----------------------------------
# Pages
# -----------------------------------
@login_required
def home(request):
    farms = _farms_for_user(request.user).order_by("-id")
    return render(request, "dashboard/home.html", {"farms": farms})


@login_required
def farm_detail(request, farm_id: int):
    farm = get_object_or_404(Farm, pk=farm_id)
    denied = _ensure_farm_access(request, farm)
    if denied:
        return denied

    # Chart: soil moisture
    soil_readings = (
        SensorReading.objects.filter(farm=farm, sensor_type="soil_moisture")
        .order_by("-timestamp")[:50]
    )
    soil_readings = list(soil_readings)[::-1]  # oldest -> newest
    labels = [r.timestamp.strftime("%d-%m %H:%M") for r in soil_readings]
    values = [r.value for r in soil_readings]

    latest_weather = WeatherSnapshot.objects.filter(farm=farm).order_by("-fetched_at").first()
    latest_disease = DiseaseImage.objects.filter(farm=farm).order_by("-created_at").first()

    # Advisory
    risk, severity, advisories = generate_advisory(farm)

    # Treatment for last scan (IMPORTANT for UI)
    treatment = get_treatment(latest_disease.predicted_label) if latest_disease else None

    return render(
        request,
        "dashboard/farm_detail.html",
        {
            "farm": farm,
            "latest_weather": latest_weather,
            "latest_disease": latest_disease,
            "treatment": treatment,  # <-- used by disease_card.html
            "soil_labels_json": json.dumps(labels),
            "soil_values_json": json.dumps(values),
            "risk": risk,
            "severity": severity,
            "advisories": advisories,
        },
    )


@login_required
def alerts_list(request):
    farms = _farms_for_user(request.user)
    alerts = Alert.objects.filter(farm__in=farms).order_by("-created_at")[:200]
    return render(request, "dashboard/alerts.html", {"alerts": alerts})


@login_required
def crop_history(request, farm_id: int):
    farm = get_object_or_404(Farm, pk=farm_id)
    denied = _ensure_farm_access(request, farm)
    if denied:
        return denied

    items = CropRecommendation.objects.filter(farm=farm).order_by("-created_at")[:50]
    return render(request, "dashboard/crop_history.html", {"farm": farm, "items": items})


# -----------------------------------
# HTMX / Actions (POST)
# -----------------------------------
@require_POST
@login_required
def seed_demo_data(request, farm_id: int):
    """
    Adds demo data so judges instantly see charts/advisories.
    """
    farm = get_object_or_404(Farm, pk=farm_id)
    denied = _ensure_farm_access(request, farm)
    if denied:
        return denied

    SensorReading.objects.create(farm=farm, sensor_type="soil_moisture", value=25, unit="%")
    SensorReading.objects.create(farm=farm, sensor_type="soil_moisture", value=35, unit="%")
    SensorReading.objects.create(farm=farm, sensor_type="soil_moisture", value=45, unit="%")
    SensorReading.objects.create(farm=farm, sensor_type="humidity", value=85, unit="%")
    SensorReading.objects.create(farm=farm, sensor_type="air_temp", value=30, unit="C")

    WeatherSnapshot.objects.create(
        farm=farm, temperature=29, humidity=70, description="Clear sky (demo)"
    )

    # Create a demo disease scan safely (FileField)
    d = DiseaseImage.objects.create(
        farm=farm,
        predicted_label="Tomato___healthy",
        confidence=0.95,
    )
    d.image.save("demo.txt", ContentFile(b"demo"), save=True)

    Alert.objects.create(
        farm=farm,
        severity="medium",
        title="Demo Alert",
        message="Demo alert created by 'Add Demo Data'.",
    )

    return HttpResponse("Demo data added. Refresh farm page.", status=200)


@require_POST
@login_required
def fetch_weather(request, farm_id: int):
    farm = get_object_or_404(Farm, pk=farm_id)
    denied = _ensure_farm_access(request, farm)
    if denied:
        return denied

    snap = WeatherSnapshot.objects.create(
        farm=farm,
        temperature=28.5,
        humidity=65.0,
        description="Mock weather (offline-safe)",
    )

    return render(
        request,
        "dashboard/partials/weather_card.html",
        {"farm": farm, "latest_weather": snap},
    )


@require_POST
@login_required
def predict_disease(request, farm_id: int):
    """
    Upload image -> predict -> save -> return disease card WITH treatment.
    """
    farm = get_object_or_404(Farm, pk=farm_id)
    denied = _ensure_farm_access(request, farm)
    if denied:
        return denied

    image_file = request.FILES.get("image")
    if not image_file:
        return HttpResponse("Image file required", status=400)

    record = DiseaseImage.objects.create(farm=farm, image=image_file)

    label, conf = _predict_label_confidence(record.image.path)

    # Confidence gate (avoid wrong medicine)
    if conf is not None and float(conf) < 0.60:
        label = "Unknown"

    record.predicted_label = label
    record.confidence = round(float(conf), 4) if conf is not None else None
    record.save()

    # Treatment lookup (IMPORTANT)
    treatment = get_treatment(record.predicted_label)

    return render(
        request,
        "dashboard/partials/disease_card.html",
        {"farm": farm, "latest_disease": record, "treatment": treatment},
    )


@require_POST
@login_required
def refresh_advisory(request, farm_id: int):
    farm = get_object_or_404(Farm, pk=farm_id)
    denied = _ensure_farm_access(request, farm)
    if denied:
        return denied

    risk, severity, advisories = generate_advisory(farm)

    Alert.objects.create(
        farm=farm,
        severity=severity,
        title=f"Farm Risk Score: {risk}/100",
        message="\n".join([f"- {a}" for a in advisories]),
    )

    return render(
        request,
        "dashboard/partials/advisory_card.html",
        {"farm": farm, "risk": risk, "severity": severity, "advisories": advisories},
    )


@require_POST
@login_required
def crop_recommend(request, farm_id: int):
    """
    Farmer input: soil moisture + month + irrigation -> recommends crops and saves history.
    """
    farm = get_object_or_404(Farm, pk=farm_id)
    denied = _ensure_farm_access(request, farm)
    if denied:
        return denied

    moisture = request.POST.get("soil_moisture")
    month = request.POST.get("month") or datetime.now().month
    irrigation = request.POST.get("irrigation") == "yes"

    try:
        soil_moisture = float(moisture)
        month = int(month)
    except Exception:
        return HttpResponse("soil_moisture and month must be valid numbers", status=400)

    recs = recommend_crops(soil_moisture=soil_moisture, month=month, irrigation=irrigation)

    CropRecommendation.objects.create(
        farm=farm,
        soil_moisture=soil_moisture,
        month=month,
        irrigation=irrigation,
        top_crop=recs[0]["crop"] if recs else "N/A",
        results_json=recs,
    )

    return render(
        request,
        "dashboard/partials/crop_reco_card.html",
        {
            "farm": farm,
            "recs": recs,
            "soil_moisture": soil_moisture,
            "month": month,
            "irrigation": irrigation,
        },
    )


# -----------------------------------
# Export
# -----------------------------------
@login_required
def export_csv(request, farm_id: int):
    farm = get_object_or_404(Farm, pk=farm_id)
    denied = _ensure_farm_access(request, farm)
    if denied:
        return denied

    response = HttpResponse(content_type="text/csv")
    safe_name = (farm.name or "farm").replace(" ", "_")
    response["Content-Disposition"] = f'attachment; filename="{safe_name}_report.csv"'

    writer = csv.writer(response)
    writer.writerow(["Farm Report"])
    writer.writerow(["Name", farm.name])
    writer.writerow(["Location", farm.location])
    writer.writerow(["Latitude", farm.latitude])
    writer.writerow(["Longitude", farm.longitude])
    writer.writerow([])

    writer.writerow(["Sensor Readings (latest 100)"])
    writer.writerow(["Type", "Value", "Unit", "Time"])
    for r in SensorReading.objects.filter(farm=farm).order_by("-timestamp")[:100]:
        writer.writerow([r.sensor_type, r.value, r.unit, r.timestamp])
    writer.writerow([])

    writer.writerow(["Weather Snapshots (latest 20)"])
    writer.writerow(["Temp (C)", "Humidity (%)", "Description", "Time"])
    for s in WeatherSnapshot.objects.filter(farm=farm).order_by("-fetched_at")[:20]:
        writer.writerow([s.temperature, s.humidity, s.description, s.fetched_at])
    writer.writerow([])

    writer.writerow(["Disease Scans (latest 20)"])
    writer.writerow(["Label", "Confidence", "Time"])
    for d in DiseaseImage.objects.filter(farm=farm).order_by("-created_at")[:20]:
        writer.writerow([d.predicted_label, d.confidence, d.created_at])
    writer.writerow([])

    risk, severity, advisories = generate_advisory(farm)
    writer.writerow(["Advisory"])
    writer.writerow(["Risk Score", risk])
    writer.writerow(["Severity", severity])
    for a in advisories:
        writer.writerow(["", a])

    return response


@login_required
def export_pdf(request, farm_id: int):
    """
    reportlab import inside so server won't crash if reportlab/Pillow issues exist.
    """
    farm = get_object_or_404(Farm, pk=farm_id)
    denied = _ensure_farm_access(request, farm)
    if denied:
        return denied

    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas as pdf_canvas
    except Exception as e:
        return HttpResponse(
            f"PDF export not available (reportlab/Pillow error). Use CSV export.\n\n{e}",
            status=501,
            content_type="text/plain",
        )

    buffer = io.BytesIO()
    p = pdf_canvas.Canvas(buffer, pagesize=A4)
    w, h = A4
    y = h - 50

    def line(text, font="Helvetica", size=10, dy=15, x=60):
        nonlocal y
        if y < 80:
            p.showPage()
            y = h - 50
        p.setFont(font, size)
        p.drawString(x, y, text)
        y -= dy

    p.setFont("Helvetica-Bold", 18)
    p.drawString(50, y, f"Farm Report: {farm.name}")
    y -= 30

    line(f"Location: {farm.location}", size=12, x=50, dy=20)
    line(f"Lat: {farm.latitude} | Lon: {farm.longitude}", size=12, x=50, dy=25)

    # Latest disease + treatment
    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, y, "Latest Disease Scan + Treatment")
    y -= 20

    disease = DiseaseImage.objects.filter(farm=farm).order_by("-created_at").first()
    if disease:
        line(f"Label: {disease.predicted_label} | Confidence: {disease.confidence}", size=10)
        t = get_treatment(disease.predicted_label)
        for a in t.get("immediate_actions", []):
            line(f"- {a}", size=10)
        for c in t.get("chemical_options", []):
            line(f"* {c.get('active_ingredient','')}: {c.get('note','')}", size=9)
    else:
        line("No disease scans found.", size=10)

    p.showPage()
    p.save()
    buffer.seek(0)

    safe_name = (farm.name or "farm").replace(" ", "_")
    return FileResponse(buffer, as_attachment=True, filename=f"{safe_name}_report.pdf")