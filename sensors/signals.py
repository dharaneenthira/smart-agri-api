from django.db.models.signals import post_save
from django.dispatch import receiver

from sensors.models import SensorReading
from dashboard.advisory import generate_advisory
from dashboard.models import Alert


@receiver(post_save, sender=SensorReading)
def create_alert_on_sensor_update(sender, instance: SensorReading, created, **kwargs):
    if not created:
        return

    farm = instance.farm
    risk, severity, advisories = generate_advisory(farm)

    # Create alert only if medium/high (avoid spamming)
    if severity in ("medium", "high"):
        Alert.objects.create(
            farm=farm,
            severity=severity,
            title=f"Auto Alert: Risk {risk}/100",
            message="\n".join([f"- {a}" for a in advisories]),
        )