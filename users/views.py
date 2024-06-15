from django.shortcuts import get_object_or_404
from rest_framework import status, views
from rest_framework.response import Response
from .serializers import UserRegisterSerializer, UserLoginSerializer, ProfileSerializer
from .models import Profile
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication

# User Registration View
class UserRegisterView(views.APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = UserRegisterSerializer(data=request.data)
        if serializer.is_valid():
            user, profile = serializer.save()  # Adjusted to handle the tuple
            return Response({"message": "User registered successfully!"}, 
                            status=status.HTTP_201_CREATED)
        
        return Response({"error": "Invalid data", "details": serializer.errors}, 
                        status=status.HTTP_400_BAD_REQUEST)

# User Login View
class UserLoginView(views.APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)

        if serializer.is_valid():
            tokens = serializer.create(validated_data={})
            return Response(
                {"tokens": tokens}, status=status.HTTP_200_OK
            )

        return Response(
            {"error": "Invalid credentials"},
            status=status.HTTP_401_UNAUTHORIZED,
        )

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

