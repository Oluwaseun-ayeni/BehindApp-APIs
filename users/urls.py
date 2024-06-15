
from django.urls import path, include
from .views import (
    UserRegisterView,   
    UserLoginView,      
    UserProfileView,         
)


urlpatterns = [
    
    path('register/', UserRegisterView.as_view(), name='user-register'),
    path('login/', UserLoginView.as_view(), name='user-login'),
    path('profile/', UserProfileView.as_view(), name='user-profile'),
]