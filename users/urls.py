from django.urls import path, include
from .views import (
    UserRegisterView,
    UserLoginView,
    UserProfileView,
    UserLogoutView,
    
)

urlpatterns = [
    path('register/', UserRegisterView.as_view(), name='user-register'),
    path('login/', UserLoginView.as_view(), name='user-login'),
    path('profile/', UserProfileView.as_view(), name='user-profile'),
    path('logout/', UserLogoutView.as_view(), name='user-logout'),
    # path('keycloak/callback/', KeycloakLoginCallbackView.as_view(), name='keycloak-callback'),
    path('', include('django_keycloak.urls')),
]
