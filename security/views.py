from rest_framework import views, status
from rest_framework.response import Response
from .models import Security, AuditLog, IPAddress
from .serializers import SecuritySerializer, AuditLogSerializer, IPAddressSerializer
from rest_framework.permissions import IsAuthenticated
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .rekognition_utils import compare_faces
from io import BytesIO


class SecurityView(views.APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            security = Security.objects.get(user=request.user)
            serializer = SecuritySerializer(security)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Security.DoesNotExist:
            return Response({"error": "Security settings not found."}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request):
        try:
            security = Security.objects.get(user=request.user)
        except Security.DoesNotExist:
            return Response({"error": "Security settings not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = SecuritySerializer(security, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AuditLogView(views.APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        logs = AuditLog.objects.filter(user=request.user)
        serializer = AuditLogSerializer(logs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class IPAddressView(views.APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        ips = IPAddress.objects.filter(user=request.user)
        if not ips.exists():
            return Response({"message": "No IP addresses found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = IPAddressSerializer(ips, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = IPAddressSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, ip_id):
        try:
            ip = IPAddress.objects.get(id=ip_id, user=request.user)
        except IPAddress.DoesNotExist:
            return Response({"error": "IPAddress not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = IPAddressSerializer(ip, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, ip_id):
        try:
            ip = IPAddress.objects.get(id=ip_id, user=request.user)
        except IPAddress.DoesNotExist:
            return Response({"error": "IPAddress not found."}, status=status.HTTP_404_NOT_FOUND)

        ip.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@csrf_exempt
def verify_kyc(request):
    """
    Endpoint to verify the KYC face using Rekognition.
    """
    if request.method == 'POST':
        # Get images from request
        source_image = request.FILES.get('source_image')
        target_image = request.FILES.get('target_image')

        if not source_image or not target_image:
            return JsonResponse({'error': 'Both images are required'}, status=400)

        # Convert images to bytes
        source_image_bytes = source_image.read()
        target_image_bytes = target_image.read()

        # Compare faces using Rekognition
        result = compare_faces(source_image_bytes, target_image_bytes)

        # Return result as JSON
        return JsonResponse(result)

    else:
        return JsonResponse({'error': 'Invalid request method'}, status=405)