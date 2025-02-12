
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.mail import send_mail
from django.conf import settings
import random
from django.core.exceptions import ObjectDoesNotExist
from .models import CustomUser
from .serializers import UserRegistrationSerializer
from django.views.decorators.csrf import csrf_exempt

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
        
         # After saving OTP to session
        request.session[f'otp_{email}'] = str(otp)
        request.session.modified = True  # ← Ensure session is marked modified
        print(f"Session ID: {request.session.session_key}")
        print(f"Cookie Domain: {settings.SESSION_COOKIE_DOMAIN}")
        print(f"Secure Flag: {settings.SESSION_COOKIE_SECURE}")
        print(f"SameSite: {settings.SESSION_COOKIE_SAMESITE}")
        

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

@csrf_exempt        
class VerifyOTPView(APIView):
    def post(self, request):
        
        email = request.data.get('email')
        entered_otp = request.data.get('otp')

        if not email or not entered_otp:
            return Response({'error': 'Email and OTP are required'}, status=status.HTTP_400_BAD_REQUEST)

        # In VerifyOTPView
        print(f"Session Engine: {request.session.__class__.__module__}")
        print(f"Session Store: {request.session.__class__.__name__}")
        # print(f"Session ID: {request.session.session_key}")
        #     print(f"Session Data: {request.session.items()}")  # Print all session data
        #     print(f"Stored OTP for {email}: {request.session.get(email)}")
        #     print(f"Provided OTP: {otp}")
        # make debug statements like above 
        print(f"Session ID: {request.session.session_key}")
        print(f"Session data for {email}: {request.session.items()}")  # Log session contents
        print(f"Entered OTP for {email}: {entered_otp}")  # Log the OTP entered by user
        print(f"Stored OTP for {email}: {request.session.get(f'otp_{email}')}")  # Log the OTP retrieved from session
        print(f"Email: {email}")  # Log the email entered by user
            
            
        # Normalize email to avoid any discrepancies (spaces, case sensitivity)
        email = email.strip().lower()
        
        # Debug: Print session contents to ensure OTP is stored
        print(f"Session data for {email}: {request.session.items()}")  # Log session contents

        # Retrieve stored OTP from session
        stored_otp = request.session.get(f'otp_{email}')
        print(f"Stored OTP for {email}: {stored_otp}")  # Log the OTP retrieved from session


        if not stored_otp:
            return Response({'error': 'OTP expired or not found. Please register again.'}, 
                            status=status.HTTP_400_BAD_REQUEST)

        if entered_otp != stored_otp:
            return Response({'error': 'Invalid OTP. Please try again.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = CustomUser.objects.get(email=email)
            user.is_verified = True  # Mark the user as verified
            user.save()

            # Remove OTP from session after successful verification
            del request.session[f'otp_{email}']
            request.session.save()

            return Response({'message': 'OTP verified successfully. Account activated!'}, 
                            status=status.HTTP_200_OK)

        except ObjectDoesNotExist:
            return Response({'error': 'User not found. Please register again.'}, status=status.HTTP_400_BAD_REQUEST)