from django.db import models
from users.models import User

class Security(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    auth_log = models.JSONField()
    settings = models.JSONField()
