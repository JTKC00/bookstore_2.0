from django.db import models
from django.contrib.auth.models import User

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=20, blank=True, null=True)
    favour_category = models.CharField(max_length=20, blank=True, null=True)
    reg_address = models.CharField(max_length=100,blank=True, null =True)

    def __str__(self):
        return f"{self.user.username} Profile"

