from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models

class CustomUser(AbstractUser):
    firebase_uid = models.CharField(max_length=255, blank=True, null=True)

    groups = models.ManyToManyField(
        Group,
        related_name="customuser_groups",  # Avoid conflict with default User model
        blank=True,
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name="customuser_permissions",  # Avoid conflict with default User model
        blank=True,
    )


# users/models.py

class Business(models.Model):
    business_name = models.CharField(max_length=100)
    branch_name = models.CharField(max_length=100)
    hours_of_operation = models.CharField(max_length=50)  # e.g., "8:00 to 17:00"
    working_days = models.CharField(max_length=50)  # e.g., "Monday to Friday"

    def __str__(self):
        return f"{self.business_name} - {self.branch_name}"
