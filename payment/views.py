from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
import stripe
from django.conf import settings
from django.utils import timezone
from .models import Subscription

stripe.api_key = settings.STRIPE_SECRET_KEY

class CreatePaymentIntentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            amount = int(request.data.get('amount')) 
            currency = request.data.get('currency', 'usd')  
            payment_method_id = request.data.get('payment_method_id')  

            if not payment_method_id:
                return Response({"error": "Payment method ID is required."}, status=status.HTTP_400_BAD_REQUEST)

            # Create PaymentIntent
            intent = stripe.PaymentIntent.create(
                amount=amount,
                currency=currency,
                payment_method=payment_method_id,  
                automatic_payment_methods={"enabled": True, "allow_redirects": "never"},
            )

            return Response({"payment_intent_id": intent.id, "client_secret": intent.client_secret}, status=status.HTTP_200_OK)

        except stripe.error.StripeError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class ConfirmPaymentIntentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            payment_intent_id = request.data.get('payment_intent_id')

            if not payment_intent_id:
                return Response({"error": "Payment intent ID is required."}, status=status.HTTP_400_BAD_REQUEST)

            # Retrieve the PaymentIntent to check if it already has a payment method
            intent = stripe.PaymentIntent.retrieve(payment_intent_id)

            if not intent.payment_method:
                payment_method = request.data.get('payment_method')
                if not payment_method:
                    return Response({"error": "Payment method is required."}, status=status.HTTP_400_BAD_REQUEST)

                # Update the PaymentIntent with the payment method if not already set
                intent = stripe.PaymentIntent.modify(
                    payment_intent_id,
                    payment_method=payment_method,
                )

            # Confirm the PaymentIntent
            intent = stripe.PaymentIntent.confirm(payment_intent_id)

            return Response({"status": intent.status}, status=status.HTTP_200_OK)

        except stripe.error.StripeError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CreateSubscriptionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            plan_id = request.data.get('plan_id')
            payment_method_id = request.data.get('payment_method_id')

            # Attach the payment method to the customer
            customer = stripe.Customer.create(
                email=request.user.email,
                payment_method=payment_method_id,
                invoice_settings={'default_payment_method': payment_method_id},
            )

            # Create the subscription
            subscription = stripe.Subscription.create(
                customer=customer.id,
                items=[{'plan': plan_id}],
                expand=['latest_invoice.payment_intent'],
            )

            start_date = timezone.now().date()
            end_date = start_date + timezone.timedelta(days=30)  # Assuming a monthly subscription

            Subscription.objects.create(
                user=request.user,
                plan=plan_id,
                start_date=start_date,
                end_date=end_date
            )

            return Response({"subscription_id": subscription.id, "client_secret": subscription.latest_invoice.payment_intent.client_secret}, status=status.HTTP_200_OK)

        except stripe.error.StripeError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class RetrieveSubscriptionView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, subscription_id):
        try:
            # Retrieve the subscription from Stripe
            subscription = stripe.Subscription.retrieve(subscription_id)

            return Response(subscription, status=status.HTTP_200_OK)

        except stripe.error.StripeError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class CancelSubscriptionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, subscription_id):
        try:
            # Cancel the subscription
            subscription = stripe.Subscription.delete(subscription_id)

            # Optionally, update the local database to reflect the cancellation
            Subscription.objects.filter(user=request.user, plan=subscription_id).update(end_date=timezone.now().date())

            return Response({"status": "cancelled"}, status=status.HTTP_200_OK)

        except stripe.error.StripeError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



