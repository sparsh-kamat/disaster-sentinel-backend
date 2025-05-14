from django.urls import path
from .views import RegisterView, VerifyOTPView , LoginView , LogoutView , ForgotPasswordView , ResetPasswordView

from .views import (
    SearchUserByEmailView,
    UserProfileUpdateView,
    UserLocationUpdateView,
    UserDetailView,
    ResendOTPView,
)

# users/urls.py (If you prefer 'signup')

urlpatterns = [
    # --- Authentication Actions ---
    path('auth/signup/', RegisterView.as_view(), name='user-signup'), # Changed back
    path('auth/login/', LoginView.as_view(), name='user-login'),
    path('auth/verify-otp/', VerifyOTPView.as_view(), name='user-verify-otp'),
    path('auth/logout/', LogoutView.as_view(), name='user-logout'),
    path('auth/forgot-password/', ForgotPasswordView.as_view(), name='user-forgot-password'),
    path('auth/reset-password/', ResetPasswordView.as_view(), name='user-reset-password'),
    path('auth/resend-otp/', ResendOTPView.as_view(), name='user-resend-otp'),

    # --- User API Actions ---
    path('api/users/search/', SearchUserByEmailView.as_view(), name='user-search'),
    path('api/users/<int:user_id>/', UserDetailView.as_view(), name='user-detail'),
    path('api/users/<int:user_id>/profile/', UserProfileUpdateView.as_view(), name='user-profile-update'),
    path('api/users/<int:user_id>/location/', UserLocationUpdateView.as_view(), name='user-location-update'),
]