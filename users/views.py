from django.shortcuts import get_object_or_404
from rest_framework import status, views
from rest_framework.response import Response
from .serializers import UserRegisterSerializer, UserLoginSerializer, ProfileSerializer
from .models import Profile,User
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import  RefreshToken
from django_ratelimit.decorators import ratelimit
from django.utils import timezone
from security.models import AuditLog,Security,IPAddress
from django.utils.decorators import method_decorator

# User Registration View
# views.py

# views.py

class UserRegisterView(views.APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        # Get the IP address from the request or use a default (e.g., '127.0.0.1' for local development)
        ip_address = request.data.get('ip_address', '127.0.0.1')

        serializer = UserRegisterSerializer(data=request.data)
        if serializer.is_valid():
            user, profile = serializer.save()

            # Save the IP address associated with the user
            IPAddress.objects.create(user=user, ip_address=ip_address)
            
            Security.objects.create(user=user, auth_log={}, settings={}) 
            return Response({"message": "User registered successfully!"}, 
                            status=status.HTTP_201_CREATED)
        
        return Response({"error": "Invalid data", "details": serializer.errors}, 
                        status=status.HTTP_400_BAD_REQUEST)



class UserLoginView(views.APIView):
    permission_classes = [AllowAny]

    @method_decorator(ratelimit(key='ip', rate='5/m', method=['POST'], block=True))
    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.context['user']
            if user.is_locked:
                if timezone.now() > user.lockout_time:
                    user.unlock_account()
                else:
                    AuditLog.objects.create(user=user, action='Account lockout attempt')
                    return Response({"error": "Account locked. Try again later."}, status=status.HTTP_403_FORBIDDEN)

            tokens = serializer.create({'user': user})
            user.failed_login_attempts = 0
            user.save()
            AuditLog.objects.create(user=user, action='Successful login')
            return Response({"tokens": tokens}, status=status.HTTP_200_OK)
        else:
            user = User.objects.filter(email=request.data.get('email')).first()
            if user:
                user.failed_login_attempts += 1
                if user.failed_login_attempts >= 5:
                    user.lock_account()
                    AuditLog.objects.create(user=user, action='Account locked due to failed login attempts')
                    return Response({"error": "Account locked due to too many failed login attempts. Try again later."}, status=status.HTTP_403_FORBIDDEN)
                user.save()
                AuditLog.objects.create(user=user, action='Failed login attempt')
        return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)
class UserLogoutView(views.APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Retrieve the refresh token from the request
        refresh_token = request.data.get("refresh_token")

        if not refresh_token:
            return Response({"error": "Refresh token not provided."}, status=status.HTTP_400_BAD_REQUEST)

        # Parse the refresh token and mark it as blacklisted
        token = RefreshToken(refresh_token)
        token.blacklist()

        return Response({"message": "Successfully logged out."}, status=status.HTTP_200_OK)
    
# Profile Management View
class UserProfileView(views.APIView):
    authentication_classes = [JWTAuthentication]
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
            return Response({"message": "Profile updated successfully!"}, 
                            status=status.HTTP_200_OK)
        
        return Response({"error": "Invalid data", "details": serializer.errors}, 
                        status=status.HTTP_400_BAD_REQUEST)

