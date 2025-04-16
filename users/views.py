
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.mail import send_mail
from django.conf import settings
import random
from django.core.exceptions import ObjectDoesNotExist
from .models import CustomUser
from .serializers import UserRegistrationSerializer , VerifyUserSerializer , ForgotPasswordRequestSerializer, UserSearchSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from django.middleware.csrf import get_token
from django.contrib.auth import authenticate, login , logout
from .serializers import LoginSerializer , ResetPasswordSerializer 
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode , urlsafe_base64_decode
from django.core.cache import cache


class PasswordResetTokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        return str(user.pk) + str(timestamp) + str(user.is_active)

password_reset_token_generator = PasswordResetTokenGenerator()

class ForgotPasswordView(APIView):
    def post(self, request):
        serializer = ForgotPasswordRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        email = serializer.validated_data['email']
        
        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            return Response({'error': 'User with this email does not exist'}, status=status.HTTP_404_NOT_FOUND)
        
        # Generate a password reset token
        token = password_reset_token_generator.make_token(user)
        
        # Encode the user's primary key for the reset link
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        
        # Send the token to the user's email
        reset_link = f"http://yourfrontend.com/reset-password?uid={uid}&token={token}"
        
        try:
            send_mail(
                'Password Reset Request',
                f'Click the link to reset your password: {reset_link}',
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
            )
            return Response({'message': 'Password reset link sent to your email'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': 'Failed to send password reset email'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class ResetPasswordView(APIView):
    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        token = serializer.validated_data['token']
        new_password = serializer.validated_data['new_password']
        
        try:
            # Decode the user's primary key
            uid = urlsafe_base64_decode(request.data.get('uid')).decode()
            user = CustomUser.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, CustomUser.DoesNotExist):
            return Response({'error': 'Invalid user'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Verify the token
        if not password_reset_token_generator.check_token(user, token):
            return Response({'error': 'Invalid or expired token'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Update the user's password
        user.set_password(new_password)
        user.save()
        
        return Response({'message': 'Password reset successfully'}, status=status.HTTP_200_OK)
    
    
class LogoutView(APIView):
    def post(self, request):
        logout(request)
        return Response({'message': 'Logout successful'}, status=status.HTTP_200_OK)
    
class LoginView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        email = serializer.validated_data['email']
        password = serializer.validated_data['password']
        
        # Authenticate the user
        user = authenticate(request, email=email, password=password)
        
        if user is not None:
            if user.is_verified:
                # Log the user in
                login(request, user)
                # return Response({'message': 'Login successful'}, status=status.HTTP_200_OK)
                return Response({
                    'message': 'Login successful',
                    'user_id': user.id,
                    'email': user.email,
                    'role': user.role,
                    'full_name': user.full_name
                }, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'User is not verified'}, status=status.HTTP_401_UNAUTHORIZED)
        else:
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
        
        
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
            # request.session[f'otp_{email}'] = str(otp)
            # request.session.save()
            # print(f"OTP for {email} stored in session: {request.session[f'otp_{email}']}")  # Debug: Log OTP stored

            # store in cache too
            #delete old otp
            cache.delete(f'otp_{email}')
            #store new otp
            cache.set(f'otp_{email}', str(otp), timeout=300)
            print(f"OTP for {email} stored in cache: {cache.get(f'otp_{email}')}")
            
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
        # request.session[f'otp_{email}'] = str(otp)
        # request.session.save()
        # print(f"OTP for {email} stored in session: {request.session[f'otp_{email}']}")  # Debug: Log OTP stored
        cache.set(f'otp_{email}', str(otp), timeout=300)
        print(f"OTP for {email} stored in cache: {cache.get(f'otp_{email}')}")
            
        # session info
        # print(request.session.items())
        # print(f"Session ID: {request.session.session_key}")
        # print(f"Session expiry age: {request.session.get_expiry_age()}")
        # print(f"Session expiry date: {request.session.get_expiry_date()}")
        # print(f"Session modified: {request.session.modified}")
        # print(f"Session has been modified at: {request.session.get('_session_expiry_age', 'N/A')}")
        
        
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
        
        # Debug cache directly
        cached_otp = cache.get(f'otp_{email}')
        print(f"Cache lookup for {email}: {cached_otp}")  # Add this line
        
        if cached_otp and cached_otp == str(otp):
            user = CustomUser.objects.get(email=email)
            user.is_verified = True
            user.save()
            cache.delete(f'otp_{email}')
            return Response({'message': 'User verified successfully'}, status=status.HTTP_200_OK)
        
        return Response({'error': 'Invalid OTP'}, status=status.HTTP_400_BAD_REQUEST)
    

# --- View to Search User by Email (No Authentication/Permissions) ---
class SearchUserByEmailView(APIView):
    # """
    # API endpoint to search for users by email.
    # Expects an 'email' query parameter.
    # Example: GET /api/users/search/?email=user@example.com
    # NOTE: This version has no authentication or permission checks.
    # """
    # No authentication_classes defined
    # No permission_classes defined

    def get(self, request):
        # Get the email from the query parameters (e.g., ?email=...)
        email_to_search = request.query_params.get('email', None)

        if not email_to_search:
            return Response(
                {'error': 'Email query parameter is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Perform a case-insensitive search for an exact match
            # Only search for users with the role 'user'
            user = CustomUser.objects.get(email__iexact=email_to_search, role='user')

            # Serialize the user data using the specific serializer
            serializer = UserSearchSerializer(user)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except CustomUser.DoesNotExist:
            # Return 404 if no user is found with that email and role 'user'
            return Response(
                {'error': 'User with this email and role "user" not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            # Generic error handler for unexpected issues
            # Consider logging the error e
            return Response(
                {'error': 'An error occurred during the search.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
# --- End of View ---
    
    
    