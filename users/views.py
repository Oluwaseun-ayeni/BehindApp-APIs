from django.shortcuts import get_object_or_404, redirect
from rest_framework import status, views
from rest_framework.response import Response
from .serializers import UserRegisterSerializer, UserLoginSerializer, ProfileSerializer
from .models import Profile, User
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django_ratelimit.decorators import ratelimit
from django.utils import timezone
from security.models import AuditLog, Security, IPAddress
from django.utils.decorators import method_decorator
from django.contrib.auth import login, logout
from keycloak_utils import KeycloakAdmin,generate_keycloak_token
import logging

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

    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            try:
                email = serializer.validated_data['email']
                password = serializer.validated_data['password']
                
                # Authenticate with Keycloak
                token_response = generate_keycloak_token(email, password)
                access_token = token_response.get('access_token')
                refresh_token = token_response.get('refresh_token')

                if not access_token or not refresh_token:
                    logger.error("Failed to obtain tokens from Keycloak.")
                    return Response({"error": "Failed to obtain tokens."}, status=status.HTTP_401_UNAUTHORIZED)

                # Example: check if the user exists locally
                user = User.objects.filter(email=email).first()
                if not user:
                    logger.error(f"User not found: {email}")
                    return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

                # Check user lock status, etc.

                return Response({"tokens": {"access": access_token, "refresh": refresh_token}}, status=status.HTTP_200_OK)
            except Exception as e:
                logger.exception("Error during login attempt.")
                return Response({"error": str(e)}, status=status.HTTP_401_UNAUTHORIZED)
        else:
            logger.error(f"Invalid serializer data: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
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





