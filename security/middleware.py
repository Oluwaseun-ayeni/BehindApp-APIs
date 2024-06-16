from django.utils.deprecation import MiddlewareMixin
from django.conf import settings
from rest_framework import status
from rest_framework.response import Response
from django.utils import timezone
from datetime import timedelta

class RateLimitMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if request.path == "/users/login/":
            user = request.user
            if user.failed_login_attempts >= settings.ACCOUNT_LOCKOUT_THRESHOLD:
                if user.locked_out_until and user.locked_out_until > timezone.now():
                    return Response(
                        {"error": "Account locked due to multiple failed login attempts."},
                        status=status.HTTP_403_FORBIDDEN
                    )

    def process_response(self, request, response):
        if request.path == "/users/login/" and response.status_code == status.HTTP_401_UNAUTHORIZED:
            user = request.user
            if user:
                user.failed_login_attempts += 1
                if user.failed_login_attempts >= settings.ACCOUNT_LOCKOUT_THRESHOLD:
                    user.locked_out_until = timezone.now() + timedelta(minutes=settings.ACCOUNT_LOCKOUT_TIME)
                user.save()

        if request.path == "/users/login/" and response.status_code == status.HTTP_200_OK:
            user = request.user
            if user:
                user.failed_login_attempts = 0
                user.locked_out_until = None
                user.save()

        return response

