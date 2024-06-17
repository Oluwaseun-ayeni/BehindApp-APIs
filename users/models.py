from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.db import models
from datetime import timedelta
from django.utils import timezone

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, location=None, DOB=None, gender=None, bio=None, profilePicture=None):
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, location=location, DOB=DOB, gender=gender, bio=bio, profilePicture=profilePicture)
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
    profilePicture = models.URLField(blank=True, null=True)

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
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(blank=True, null=True)
    photo_url = models.URLField(blank=True, null=True)
    preferences = models.JSONField(blank=True, null=True)

    def __str__(self):
        return self.user.email


class Match(models.Model):
    user1 = models.ForeignKey(User, related_name='matches_as_user1', on_delete=models.CASCADE)
    user2 = models.ForeignKey(User, related_name='matches_as_user2', on_delete=models.CASCADE)
    match_date = models.DateTimeField(auto_now_add=True)
    is_accepted = models.BooleanField(default=False)

    def __str__(self):
        return f"Match between {self.user1.email} and {self.user2.email}"


class Message(models.Model):
    sender = models.ForeignKey(User, related_name='sent_messages', on_delete=models.CASCADE)
    receiver = models.ForeignKey(User, related_name='received_messages', on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    content = models.TextField()
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"Message from {self.sender.email} to {self.receiver.email}"


class Subscription(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    plan_type = models.CharField(max_length=50)
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Subscription of {self.user.email} for {self.plan_type}"


class Payment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateTimeField(auto_now_add=True)
    payment_method = models.CharField(max_length=50)

    def __str__(self):
        return f"Payment of {self.amount} by {self.user.email}"


class Report(models.Model):
    reported_user = models.ForeignKey(User, related_name='reports_against', on_delete=models.CASCADE)
    reporter_user = models.ForeignKey(User, related_name='reports_by', on_delete=models.CASCADE)
    report_date = models.DateTimeField(auto_now_add=True)
    reason = models.TextField()
    is_resolved = models.BooleanField(default=False)

    def __str__(self):
        return f"Report by {self.reporter_user.email} against {self.reported_user.email}"
