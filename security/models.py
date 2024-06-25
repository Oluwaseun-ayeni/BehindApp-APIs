from django.db import models
from users.models import User

class Security(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='security')
    auth_log = models.JSONField(default=dict)
    settings = models.JSONField(default=dict)

class AuditLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE,related_name='auditlog')
    action = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)

class IPAddress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE,related_name='ipaddress')
    ip_address = models.GenericIPAddressField()
    is_whitelisted = models.BooleanField(default=False)
    is_blacklisted = models.BooleanField(default=False)

