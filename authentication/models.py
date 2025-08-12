# authentication/models.py

from django.db import models
from django.contrib.auth.models import User
import random
from django.utils import timezone
from datetime import timedelta

class OTP(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def save(self, *args, **kwargs):
        # Set the expiration time to 5 minutes from creation
        if not self.id:
            self.expires_at = timezone.now() + timedelta(minutes=5)
        super(OTP, self).save(*args, **kwargs)

    def __str__(self):
        return f"OTP for {self.user.username}"

    @staticmethod
    def generate_otp(user):
        """Generate a new OTP, save it, and return the code."""
        code = str(random.randint(100000, 999999))
        # Get or create an OTP instance for the user, updating the code and expiration
        otp_instance, _ = OTP.objects.update_or_create(
            user=user,
            defaults={'code': code, 'expires_at': timezone.now() + timedelta(minutes=5)}
        )
        return code
