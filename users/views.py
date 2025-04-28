from django.conf import settings
from django.core.cache import cache
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404
import random

from django.contrib.auth import authenticate, login, logout
from django.utils import timezone
import datetime
from django.contrib.auth.tokens import PasswordResetTokenGenerator

from django.middleware.csrf import get_token
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode

from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import CustomUser
from .models import OTPStorage

from .serializers import (
    ForgotPasswordRequestSerializer,
    LoginSerializer,
    ResetPasswordSerializer,
    UserLocationUpdateSerializer,
    UserProfileDetailSerializer,
    UserProfileUpdateSerializer,
    UserRegistrationSerializer,
    UserSearchSerializer,
    VerifyUserSerializer,
    UserPermissionDetailSerializer,
)

from agency.models import AgencyMemberPermission # Assuming permissions model is in agency app
from django.utils.translation import gettext_lazy as _

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
    """
    Handles user login, authenticates credentials, logs the user in (session),
    and returns basic user info along with granted permissions.
    """

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
                # Log the user in (creates a session)
                login(request, user)

                # --- Fetch and Serialize Permissions ---
                permissions_granted = AgencyMemberPermission.objects.filter(
                    member=user # Find permissions where this user is the member
                ).select_related('agency') # Fetch related agency data efficiently

                # Use the serializer created previously for permissions granted TO a user
                permission_serializer = UserPermissionDetailSerializer(permissions_granted, many=True)
                # --- End Fetch and Serialize ---

                # --- Construct Response ---
                response_data = {
                    'message': 'Login successful',
                    'user_id': user.id,
                    'email': user.email,
                    'role': user.role,
                    'full_name': user.full_name,
                    # Add the serialized permissions list to the response
                    'permissions': permission_serializer.data
                }
                # --- End Construct Response ---

                return Response(response_data, status=status.HTTP_200_OK)
            else:
                # User exists but is not verified
                return Response({'error': 'User is not verified'}, status=status.HTTP_401_UNAUTHORIZED)
        else:
            # Authentication failed (invalid email or password)
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

# ... (Rest of your views.py)
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
            # User with this email exists. Check if verified.
            if existing_user.is_verified:
                # Already verified - cannot re-register.
                return Response(
                    {'error': 'User already registered and verified. Please log in.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            else:
                # --- User exists but is NOT verified: Delete and Recreate ---
                 # <<< FIX: Replace self.stdout/stderr with print() >>>
                print(f"INFO: User {email} exists but is not verified. Deleting old record.") # Use print for logging
                try:
                    existing_user.delete() # Delete the old unverified record
                    print(f"INFO: Successfully deleted old record for {email}.") # Use print for logging
                except Exception as e:
                    # Handle potential deletion errors (rare)
                    print(f"ERROR: Error deleting existing unverified user {email}: {e}") # Use print for error logging
                    return Response(
                        {'error': 'Failed to delete existing unverified user. Please try again.'},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
                # --- End Delete and Recreate ---
                # Execution will now continue below to create the new user

        # if existing_user:
        #     if existing_user.is_verified:  # If already verified, reject re-registration
        #         return Response({'error': 'User already registered and verified. Please log in.'}, 
        #                         status=status.HTTP_400_BAD_REQUEST)
            
        #     # If user is not verified, resend OTP instead of creating a new account
        #     otp = random.randint(100000, 999999)
        #     # request.session[f'otp_{email}'] = str(otp)
        #     # request.session.save()
        #     # print(f"OTP for {email} stored in session: {request.session[f'otp_{email}']}")  # Debug: Log OTP stored

        #     # store in cache too
        #     #delete old otp
        #     cache.delete(f'otp_{email}')
        #     #store new otp
        #     cache.set(f'otp_{email}', str(otp), timeout=300)
        #     print(f"OTP for {email} stored in cache: {cache.get(f'otp_{email}')}")
            
        #     try:
        #         send_mail(
        #             'Disaster Sentinel - Account Verification (Resent)',
        #             f'Your new OTP is {otp}',
        #             settings.DEFAULT_FROM_EMAIL,
        #             [email],
        #             fail_silently=False,
        #         )
        #         return Response({'message': 'OTP resent successfully. Please verify your email.'}, 
        #                       status=status.HTTP_200_OK)
        #     except Exception as e:
        #         return Response({'error': 'Failed to send OTP'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
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

        # --- Generate OTP and store in DB ---
        otp = random.randint(100000, 999999)
        otp_expiry_time = timezone.now() + datetime.timedelta(minutes=5) # e.g., 5 minute expiry

        # Delete any old OTP record for this email first
        OTPStorage.objects.filter(email=email).delete()

        # Create the new OTP record
        OTPStorage.objects.create(
            email=email,
            otp=str(otp), # Store OTP as string
            expires_at=otp_expiry_time
        )
        print(f"DEBUG: OTP for {email} stored in DB. Expires at: {otp_expiry_time}")


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


# class VerifyOTPView(APIView):
#     def post(self, request):
#         serializer = VerifyUserSerializer(data=request.data)
        
#         if not serializer.is_valid():
#             return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
#         email = serializer.validated_data['email']
#         otp = serializer.validated_data['otp']
        
#         # Debug cache directly
        
        
#         if cached_otp and cached_otp == str(otp):
#             user = CustomUser.objects.get(email=email)
#             user.is_verified = True
#             user.save()
#             cache.delete(f'otp_{email}')
#             return Response({'message': 'User verified successfully'}, status=status.HTTP_200_OK)
        
#         return Response({'error': 'Invalid OTP'}, status=status.HTTP_400_BAD_REQUEST)
    
class VerifyOTPView(APIView):
    def post(self, request):
        serializer = VerifyUserSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data['email']
        otp_entered = serializer.validated_data['otp']

        try:
            # Find the OTP record for the email
            otp_record = OTPStorage.objects.get(email=email)

            # Check if expired
            if otp_record.is_expired():
                print(f"DEBUG: OTP for {email} found but expired at {otp_record.expires_at}")
                otp_record.delete() # Clean up expired OTP
                return Response({'error': 'OTP has expired'}, status=status.HTTP_400_BAD_REQUEST)

            # Check if OTP matches
            if otp_record.otp == str(otp_entered):
                # OTP is correct and not expired
                user = CustomUser.objects.get(email=email)
                user.is_verified = True
                user.save()
                otp_record.delete() # Delete OTP record after successful verification
                print(f"DEBUG: User {email} verified successfully. OTP record deleted.")
                return Response({'message': 'User verified successfully'}, status=status.HTTP_200_OK)
            else:
                # OTP is incorrect
                print(f"DEBUG: Invalid OTP entered for {email}. Expected {otp_record.otp}, got {otp_entered}")
                return Response({'error': 'Invalid OTP'}, status=status.HTTP_400_BAD_REQUEST)

        except OTPStorage.DoesNotExist:
            # No OTP record found for this email
            print(f"DEBUG: No OTP record found for {email}")
            return Response({'error': 'Invalid OTP or no OTP requested'}, status=status.HTTP_400_BAD_REQUEST)
        except CustomUser.DoesNotExist:
            # Should not happen if OTP record exists, but handle defensively
            print(f"ERROR: User {email} not found during OTP verification despite OTP record existing.")
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print(f"ERROR: Unexpected error during OTP verification for {email}: {e}")
            return Response({'error': 'An error occurred during verification.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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


# --- View to Update Basic Profile Details ---
class UserProfileUpdateView(APIView):
    """
    Updates basic profile information (name, contact, PAN) for a specific user.
    Uses PATCH method. Access via /api/users/<user_id>/profile/
    NO Authentication/Permissions applied.
    """
    # No authentication/permission classes

    def patch(self, request, user_id, *args, **kwargs):
        # Find the user object or return 404
        user = get_object_or_404(CustomUser, pk=user_id)

        # Instantiate serializer for updating the user instance
        # partial=True allows for partial updates (only fields provided are updated)
        serializer = UserProfileUpdateSerializer(user, data=request.data, partial=True)

        try:
            serializer.is_valid(raise_exception=True)

            # --- Custom Validation for agency_pan based on user's role ---
            # Check consistency only if agency_pan is included in the request data
            if 'agency_pan' in serializer.validated_data:
                new_pan = serializer.validated_data.get('agency_pan')
                # Use the existing user's role for validation
                if user.role == 'agency' and not new_pan:
                    raise serializers.ValidationError(
                        {'agency_pan': 'Agency PAN cannot be removed for agency accounts.'}
                        # Or handle as needed - maybe allow removal? Depends on logic.
                        # If allowing removal, remove this check.
                    )
                if user.role != 'agency' and new_pan:
                    raise serializers.ValidationError(
                        {'agency_pan': 'PAN number is only allowed for agency accounts.'}
                    )
            # --- End Custom Validation ---

            # Save the changes
            updated_user = serializer.save()

            # Return the updated user data using the detail serializer
            response_serializer = UserProfileDetailSerializer(updated_user)
            return Response(response_serializer.data, status=status.HTTP_200_OK)

        except serializers.ValidationError as e:
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(f"Error updating profile for user {user_id}: {e}") # Basic logging
            return Response(
                {'error': 'An unexpected error occurred.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# --- View to Update User Location Details ---
class UserLocationUpdateView(APIView):
    """
    Updates location information (state, city, lat, long) for a specific user.
    Uses PATCH method. Access via /api/users/<user_id>/location/
    NO Authentication/Permissions applied.
    """
    # No authentication/permission classes

    def patch(self, request, user_id, *args, **kwargs):
        # Find the user object or return 404
        user = get_object_or_404(CustomUser, pk=user_id)

        # Instantiate serializer for updating location
        serializer = UserLocationUpdateSerializer(user, data=request.data, partial=True)

        try:
            serializer.is_valid(raise_exception=True)
            updated_user = serializer.save()

            # Return the updated user data using the detail serializer
            response_serializer = UserProfileDetailSerializer(updated_user)
            return Response(response_serializer.data, status=status.HTTP_200_OK)

        except serializers.ValidationError as e:
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(f"Error updating location for user {user_id}: {e}") # Basic logging
            return Response(
                {'error': 'An unexpected error occurred.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# --- NEW View to Retrieve User Details ---
class UserDetailView(APIView):
    # """
    # Retrieves profile details for a specific user identified by their ID.
    # Handles GET requests to /api/users/<user_id>/
    # NO Authentication/Permissions applied by default.
    # """

    def get(self, request, user_id, *args, **kwargs):
        """
        Handles GET request to fetch user details.
        """
        # Find the user object by primary key (user_id) or return 404
        user = get_object_or_404(CustomUser, pk=user_id)

        # Serialize the user data using the detail serializer
        serializer = UserProfileDetailSerializer(user)

        # Return the serialized data
        return Response(serializer.data, status=status.HTTP_200_OK)

# ... (rest of your views)
  
    
    