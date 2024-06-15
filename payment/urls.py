from django.urls import path
from .views import CreatePaymentIntentView, ConfirmPaymentIntentView, CreateSubscriptionView, RetrieveSubscriptionView, CancelSubscriptionView

urlpatterns = [
    path('create-payment-intent/', CreatePaymentIntentView.as_view(), name='create-payment-intent'),
    path('confirm-payment-intent/', ConfirmPaymentIntentView.as_view(), name='confirm-payment-intent'),
    path('create-subscription/', CreateSubscriptionView.as_view(), name='create-subscription'),
    path('retrieve-subscription/<str:subscription_id>/', RetrieveSubscriptionView.as_view(), name='retrieve-subscription'),
    path('cancel-subscription/<str:subscription_id>/', CancelSubscriptionView.as_view(), name='cancel-subscription'),
]
