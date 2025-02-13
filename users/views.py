
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

        # session info
        print(request.session.items())
        print(f"Session ID: {request.session.session_key}")
        print(f"Session expiry age: {request.session.get_expiry_age()}")
        print(f"Session expiry date: {request.session.get_expiry_date()}")
        print(f"Session modified: {request.session.modified}")
        print(f"Session has been modified at: {request.session.get('_session_expiry_age', 'N/A')}")
        
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
        
        print(f"Session ID: {request.session.session_key}")
        print(f"Session Data: {request.session.items()}")  # Print all session data
        print(f"Stored OTP for {email}: {request.session.get(email)}")
        print(f"Provided OTP: {otp}")
        
        # Verify OTP
        if request.session.get(f'otp_{email}') == str(otp): 
            user = CustomUser.objects.get(email=email)
            user.is_verified = True
            user.save()
        else:
            return Response({'error': 'Invalid OTP'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Remove OTP from session
        del request.session[f'otp_{email}']
        request.session.save()
        
        # Debug: Confirm OTP removal
        print(f"OTP for {email} removed from session")
        
        return Response({'message': 'User verified successfully'}, status=status.HTTP_200_OK)