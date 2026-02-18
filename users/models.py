from django.db import models
from django.contrib.auth.models import AbstractUser


class CustomUser(AbstractUser):
    email = models.EmailField(unique=True, verbose_name="Email")
    email_verified = models.BooleanField(
        default=False, verbose_name="Email подтвержден"
    )
    verification_token = models.CharField(max_length=100, blank=True, null=True)
    verification_token_created = models.DateTimeField(null=True, blank=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = [
        "username",
    ]

    def __str__(self):
        return self.email
