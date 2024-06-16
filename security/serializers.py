from rest_framework import serializers
from .models import Security, AuditLog, IPAddress

class SecuritySerializer(serializers.ModelSerializer):
    class Meta:
        model = Security
        fields = ['id','user', 'auth_log', 'settings']

class AuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditLog
        fields = ['id','user', 'action', 'timestamp']

class IPAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = IPAddress
        fields = ['id','user', 'ip_address', 'is_whitelisted', 'is_blacklisted']
