from rest_framework import serializers
from .models import User, Profile
from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.tokens import RefreshToken

class UserRegisterSerializer(serializers.ModelSerializer):
    profile_bio = serializers.CharField(max_length=255, required=False)
    profile_picture = serializers.ImageField(required=False)

    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'password', 'profile_bio', 'profile_picture']

    def validate_password(self, value):
        validate_password(value)
        return value

    def create(self, validated_data):
        bio = validated_data.pop('profile_bio', None)
        picture = validated_data.pop('profile_picture', None)

        # Create the user instance with hashed password
        user = User(
            email=validated_data['email'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name']
        )
        user.set_password(validated_data['password'])
        user.save()

        # Create the profile associated with the user
        profile = Profile.objects.create(
            user=user,
            bio=bio,
            photo_url=picture.url if picture else None
        )

        return user, profile

class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = User.objects.filter(email=data['email']).first()

        if not user or not user.check_password(data['password']):
            raise serializers.ValidationError("Invalid credentials")

        self.context['user'] = user
        return data

    def create(self, validated_data):
        user = self.context['user']
        refresh = RefreshToken.for_user(user)
        return {
            "access": str(refresh.access_token),
            "refresh": str(refresh)
        }

class ProfileSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()

    class Meta:
        model = Profile
        fields = ['user', 'bio', 'photo_url', 'preferences']

    def create(self, validated_data):
        user_data = validated_data.pop('user')
        user_instance = User.objects.create(
            email=user_data['email'],
            first_name=user_data.get('first_name', ''),
            last_name=user_data.get('last_name', '')
        )

        profile_instance = Profile.objects.create(
            user=user_instance,
            bio=validated_data.get('bio', ''),
            photo_url=validated_data.get('photo_url', ''),
            preferences=validated_data.get('preferences', {})
        )
        return profile_instance

    def update(self, instance, validated_data):
        user_data = validated_data.pop('user')

        instance.user.email = user_data.get('email', instance.user.email)
        instance.user.first_name = user_data.get('first_name', instance.user.first_name)
        instance.user.last_name = user_data.get('last_name', instance.user.last_name)
        instance.user.save()

        instance.bio = validated_data.get('bio', instance.bio)
        instance.photo_url = validated_data.get('photo_url', instance.photo_url)
        instance.preferences = validated_data.get('preferences', instance.preferences)
        instance.save()

        return instance






# from rest_framework import serializers
# from .models import User, Profile
# from rest_framework_simplejwt.tokens import RefreshToken

# class UserSerializer(serializers.ModelSerializer):
#     profile = serializers.StringRelatedField()

#     class Meta:
#         model = User
#         fields = ['id', 'email', 'first_name', 'last_name', 'is_active', 'is_staff', 'profile']

# class UserRegisterSerializer(serializers.ModelSerializer):
#     profile_bio = serializers.CharField(max_length=255, required=False)
#     profile_picture = serializers.ImageField(required=False)

#     class Meta:
#         model = User
#         fields = ['email', 'first_name', 'last_name', 'password', 'profile_bio', 'profile_picture']

#     def create(self, validated_data):
#         bio = validated_data.pop('profile_bio', None)
#         picture = validated_data.pop('profile_picture', None)
#         user = User.objects.create_user(
#             email=validated_data['email'],
#             first_name=validated_data['first_name'],
#             last_name=validated_data['last_name'],
#             password=validated_data['password'],
#         )
#         Profile.objects.create(user=user, bio=bio, profile_picture=picture)
#         return user

# class UserLoginSerializer(serializers.Serializer):
#     email = serializers.EmailField()
#     password = serializers.CharField(write_only=True)

#     def validate(self, data):
#         user = User.objects.filter(email=data['email']).first()
#         if not user or not user.check_password(data['password']):
#             raise serializers.ValidationError("Invalid credentials")
#         self.context['user'] = user
#         return data

#     def create(self, validated_data):
#         user = self.context['user']
#         refresh = RefreshToken.for_user(user)
#         return {
#             'refresh': str(refresh),
#             'access': str(refresh.access_token),
#         }
    

#     from rest_framework import serializers
# from .models import User, Profile

# class UserSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = User
#         fields = ['id', 'email', 'first_name', 'last_name', 'is_active', 'is_staff']

# class ProfileSerializer(serializers.ModelSerializer):
#     user = UserSerializer()

#     class Meta:
#         model = Profile
#         fields = ['user', 'bio', 'photo_url', 'preferences']

#     def create(self, validated_data):
#         user_data = validated_data.pop('user')
#         user_instance = User.objects.create(
#             email=user_data['email'],
#             first_name=user_data.get('first_name', ''),
#             last_name=user_data.get('last_name', '')
#         )
#         profile_instance = Profile.objects.create(
#             user=user_instance,
#             bio=validated_data.get('bio', ''),
#             photo_url=validated_data.get('photo_url', ''),
#             preferences=validated_data.get('preferences', {})
#         )
#         return profile_instance

#     def update(self, instance, validated_data):
#         user_data = validated_data.pop('user')
#         instance.user.email = user_data.get('email', instance.user.email)
#         instance.user.first_name = user_data.get('first_name', instance.user.first_name)
#         instance.user.last_name = user_data.get('last_name', instance.user.last_name)
#         instance.user.save()

#         instance.bio = validated_data.get('bio', instance.bio)
#         instance.photo_url = validated_data.get('photo_url', instance.photo_url)
#         instance.preferences = validated_data.get('preferences', instance.preferences)
#         instance.save()

#         return instance

