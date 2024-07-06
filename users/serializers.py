from rest_framework import serializers
from .models import User, Profile
from django.contrib.auth.password_validation import validate_password
from security.models import IPAddress
from keycloak_utils import generate_keycloak_token
from rest_framework.exceptions import AuthenticationFailed



class UserRegisterSerializer(serializers.ModelSerializer):
    ip_address = serializers.IPAddressField(write_only=True, required=False, default='127.0.0.1')
    profile_bio = serializers.CharField(max_length=255, required=False)
    profile_picture = serializers.ImageField(required=False)

    class Meta:
        model = User
        fields = ['email', 'password', 'profile_bio', 'profile_picture', 'ip_address', 'gender', 'DOB', 'location']
        extra_kwargs = {
            'password': {'write_only': True},
        }

    def validate_password(self, value):
        validate_password(value)
        return value

    def create(self, validated_data):
        bio = validated_data.pop('profile_bio', None)
        picture = validated_data.pop('profile_picture', None)
        ip_address = validated_data.pop('ip_address', '127.0.0.1')

        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            gender=validated_data.get('gender'),
            DOB=validated_data.get('DOB'),
            location=validated_data.get('location')
        )

        Profile.objects.create(
            user=user,
            bio=bio,
            photo_url=picture.url if picture else None
        )

        IPAddress.objects.create(user=user, ip_address=ip_address)

        return user


class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            raise serializers.ValidationError("Must include 'email' and 'password'.")

        try:
            # Authenticate with Keycloak
            token_response = generate_keycloak_token(email, password)
            access_token = token_response.get('access_token')
            refresh_token = token_response.get('refresh_token')

            if not access_token or not refresh_token:
                raise AuthenticationFailed("Failed to obtain tokens from Keycloak.")

            # Include 'email' and 'password' in validated data if needed
            validated_data = {
                'email': email,
                'password': password,
                'access_token': access_token,
                'refresh_token': refresh_token
            }

            return validated_data

        except AuthenticationFailed as e:
            raise serializers.ValidationError(str(e))
        except Exception as e:
            raise serializers.ValidationError(f"An unexpected error occurred: {str(e)}")


class ProfileSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()

    class Meta:
        model = Profile
        fields = ['user', 'bio', 'photo_url', 'preferences']

    def update(self, instance, validated_data):
        instance.bio = validated_data.get('bio', instance.bio)
        instance.photo_url = validated_data.get('photo_url', instance.photo_url)
        instance.preferences = validated_data.get('preferences', instance.preferences)
        instance.save()
        return instance

