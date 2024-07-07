from django.shortcuts import get_object_or_404, redirect
from rest_framework import status, views
from rest_framework.response import Response
from .serializers import UserRegisterSerializer, UserLoginSerializer, ProfileSerializer
from .models import Profile, User
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator
from django.utils import timezone
from security.models import AuditLog, Security, IPAddress
from django.contrib.auth import  logout
from keycloak_utils import KeycloakAdmin,generate_keycloak_token
import logging
from keycloak import KeycloakOpenID
from keycloak_utils import get_keycloak_config_value

logger = logging.getLogger(__name__)

class UserRegisterView(views.APIView):
    permission_classes = []

    def post(self, request):
        serializer = UserRegisterSerializer(data=request.data)
        if serializer.is_valid():
            try:
                user = serializer.save()

                # Create user in Keycloak
                keycloak_admin = KeycloakAdmin()
                keycloak_admin.create_user(user.email, request.data.get('password'))

                return Response({"message": "User registered successfully!"}, status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response({"error": f"Error registering user: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response({"error": "Invalid data", "details": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)




class UserLoginView(views.APIView):
    permission_classes = [AllowAny]

    @method_decorator(ratelimit(key='ip', rate='5/m', method=['POST'], block=True))
    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            password = serializer.validated_data['password']

            # Check if user exists
            user = User.objects.filter(email=email).first()
            if user:
                if user.is_locked:
                    if timezone.now() > user.lockout_time:
                        user.failed_login_attempts = 0
                        user.is_locked = False
                        user.lockout_time = None
                        user.save()
                    else:
                        AuditLog.objects.create(user=user, action='Account lockout attempt')
                        return Response({"error": "Account locked. Try again later."}, status=status.HTTP_403_FORBIDDEN)

            try:
                # Authenticate with Keycloak
                token_response = generate_keycloak_token(email, password)
                access_token = token_response.get('access_token')
                refresh_token = token_response.get('refresh_token')

                if not access_token or not refresh_token:
                    logger.error("Failed to obtain tokens from Keycloak.")
                    if user:
                        user.failed_login_attempts += 1
                        if user.failed_login_attempts >= 5:
                            user.is_locked = True
                            user.lockout_time = timezone.now() + timedelta(minutes=15)
                            user.save()
                            AuditLog.objects.create(user=user, action='Account locked due to failed login attempts')
                            return Response({"error": "Account locked due to too many failed login attempts. Try again later."}, status=status.HTTP_403_FORBIDDEN)
                        user.save()
                        AuditLog.objects.create(user=user, action='Failed login attempt')
                    return Response({"error": "Failed to obtain tokens."}, status=status.HTTP_401_UNAUTHORIZED)

                if user:
                    user.failed_login_attempts = 0
                    user.save()

                AuditLog.objects.create(user=user, action='Successful login')
                return Response({"tokens": {"access": access_token, "refresh": refresh_token}}, status=status.HTTP_200_OK)
            except Exception as e:
                logger.exception("Error during login attempt.")
                if user:
                    user.failed_login_attempts += 1
                    if user.failed_login_attempts >= 5:
                        user.is_locked = True
                        user.lockout_time = timezone.now() + timedelta(minutes=15)
                        user.save()
                        AuditLog.objects.create(user=user, action='Account locked due to failed login attempts')
                        return Response({"error": "Account locked due to too many failed login attempts. Try again later."}, status=status.HTTP_403_FORBIDDEN)
                    user.save()
                    AuditLog.objects.create(user=user, action='Failed login attempt')
                return Response({"error": str(e)}, status=status.HTTP_401_UNAUTHORIZED)
        else:
            user = User.objects.filter(email=request.data.get('email')).first()
            if user:
                user.failed_login_attempts += 1
                if user.failed_login_attempts >= 5:
                    user.is_locked = True
                    user.lockout_time = timezone.now() + timedelta(minutes=15)
                    user.save()
                    AuditLog.objects.create(user=user, action='Account locked due to failed login attempts')
                    return Response({"error": "Account locked due to too many failed login attempts. Try again later."}, status=status.HTTP_403_FORBIDDEN)
                user.save()
                AuditLog.objects.create(user=user, action='Failed login attempt')
        return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)
class UserLogoutView(views.APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get("refresh_token")
        if not refresh_token:
            return Response({"error": "Refresh token not provided."}, status=status.HTTP_400_BAD_REQUEST)
        token = RefreshToken(refresh_token)
        token.blacklist()

        # Logout from Keycloak
        try:
            keycloak_openid = KeycloakOpenID(
                server_url=get_keycloak_config_value('KEYCLOAK_SERVER_URL'),
                client_id=get_keycloak_config_value('KEYCLOAK_CLIENT_ID'),
                realm_name=get_keycloak_config_value('KEYCLOAK_REALM'),
                client_secret_key=get_keycloak_config_value('KEYCLOAK_CLIENT_SECRET_KEY'),
            )
            keycloak_openid.logout(refresh_token)
        except Exception as e:
            return Response({"error": f"Error logging out from Keycloak: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Logout from Django
        logout(request)

        return Response({"message": "Successfully logged out."}, status=status.HTTP_200_OK)



class UserProfileView(views.APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        profile = get_object_or_404(Profile, user=user)
        serializer = ProfileSerializer(profile)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request):
        user = request.user
        profile = get_object_or_404(Profile, user=user)
        serializer = ProfileSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Profile updated successfully!"}, status=status.HTTP_200_OK)
        return Response({"error": "Invalid data", "details": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

