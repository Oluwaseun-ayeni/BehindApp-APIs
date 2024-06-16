from django.urls import path
from .views import SecurityView, AuditLogView, IPAddressView

urlpatterns = [
    path('secure/', SecurityView.as_view(), name='secure'),
    path('audit-logs/', AuditLogView.as_view(), name='audit-logs'),
    path('ip-addresses/', IPAddressView.as_view(), name='ip-addresses'),
    path('ip-addresses/<int:ip_id>/', IPAddressView.as_view(), name='ip-address-detail'),
]

