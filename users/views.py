
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.mail import send_mail
from django.conf import settings
import random
from django.core.exceptions import ObjectDoesNotExist
from .models import CustomUser
from .serializers import UserRegistrationSerializer , VerifyUserSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from django.middleware.csrf import get_token

class GetCSRFToken(APIView):
    def get(self, request):
        csrf_token = get_token(request)
        return Response({'csrfToken': csrf_token})
    
class RegisterView(APIView):
    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data['email']
        
        # Check if the user already exists
        existing_user = CustomUser.objects.filter(email=email).first()
        
        if existing_user:
            if existing_user.is_verified:  # If already verified, reject re-registration
                return Response({'error': 'User already registered and verified. Please log in.'}, 
                                status=status.HTTP_400_BAD_REQUEST)
            
            # If user is not verified, resend OTP instead of creating a new account
            otp = random.randint(100000, 999999)
            request.session[f'otp_{email}'] = str(otp)
            request.session.save()

            try:
                send_mail(
                    'Disaster Sentinel - Account Verification (Resent)',
                    f'Your new OTP is {otp}',
                    settings.DEFAULT_FROM_EMAIL,
                    [email],
                    fail_silently=False,
                )
                return Response({'message': 'OTP resent successfully. Please verify your email.'}, 
                              status=status.HTTP_200_OK)
            except Exception as e:
                return Response({'error': 'Failed to send OTP'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # If user doesn't exist, create a new one
        user = CustomUser(
            email=email,
            full_name=serializer.validated_data['full_name'],
            contact=serializer.validated_data['contact'],
            role=serializer.validated_data['role'],
            agency_pan=serializer.validated_data.get('agency_pan')
        )
        user.set_password(serializer.validated_data['password'])
        user.save()

        # Generate OTP and send email
        otp = random.randint(100000, 999999)
        request.session[f'otp_{email}'] = str(otp)
        request.session.save()
        print(f"OTP for {email} stored in session: {request.session[f'otp_{email}']}")  # Debug: Log OTP stored

        try:
            send_mail(
                'Disaster Sentinel - Account Verification',
                f'Your OTP is {otp}',
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
            )
        except Exception as e:
            return Response({'error': 'Failed to send OTP'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({'message': 'User created successfully. OTP sent to email.'}, 
                        status=status.HTTP_201_CREATED)


class VerifyOTPView(APIView):
    def post(self, request):
        serializer = VerifyUserSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        email = serializer.validated_data['email']
        otp = serializer.validated_data['otp']
        
        # Debug: Log received email and OTP
        print(f"Received email: {email}, OTP: {otp}")
        
        # Check if OTP is correct
        session_otp = request.session.get(f'otp_{email}')
        print(f"Session OTP for {email}: {session_otp}")  # Debug: Log session OTP
        
        if session_otp != otp:
            return Response({'error': 'Invalid OTP'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Verify user
        try:
            user = CustomUser.objects.get(email=email)
            user.is_verified = True
            user.save()
        except ObjectDoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Clear OTP from session
        del request.session[f'otp_{email}']
        request.session.save()
        
        # Debug: Confirm OTP removal
        print(f"OTP for {email} removed from session")
        
        return Response({'message': 'User verified successfully'}, status=status.HTTP_200_OK)