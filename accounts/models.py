from django.db import models
from django.contrib.auth.models import User
from farms.models import Farm


class UserProfile(models.Model):
    ROLES = [
        ("farmer", "Farmer"),
        ("fpo_admin", "FPO Admin"),
        ("expert", "Agronomist / Expert"),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    role = models.CharField(max_length=20, choices=ROLES, default="farmer")
    farms = models.ManyToManyField(Farm, blank=True, related_name="users")

    def __str__(self):
        return f"{self.user.username} ({self.role})"