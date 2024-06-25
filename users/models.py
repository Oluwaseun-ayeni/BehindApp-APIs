from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.db import models
from datetime import timedelta
from django.utils import timezone

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, location=None, DOB=None, gender=None, bio=None, profile_picture=None):
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, location=location, DOB=DOB, gender=gender, bio=bio, profile_picture=profile_picture)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)

class User(AbstractBaseUser):
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=30, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_locked = models.BooleanField(default=False)
    failed_login_attempts = models.IntegerField(default=0)
    lockout_time = models.DateTimeField(null=True, blank=True)
    location = models.CharField(max_length=100, blank=True, null=True)
    DOB = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    profile_picture = models.URLField(blank=True, null=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def lock_account(self):
        self.is_locked = True
        self.lockout_time = timezone.now() + timedelta(minutes=15)
        self.save()

    def unlock_account(self):
        self.is_locked = False
        self.failed_login_attempts = 0
        self.lockout_time = None
        self.save()

    def __str__(self):
        return self.email

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(blank=True, null=True)
    photo_url = models.URLField(blank=True, null=True)
    preferences = models.JSONField(blank=True, null=True)

    def __str__(self):
        return self.user.email


