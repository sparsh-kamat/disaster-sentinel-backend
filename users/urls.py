from django.urls import path
from .views import RegisterView, VerifyOTPView , LoginView , LogoutView , ForgotPasswordView , ResetPasswordView

urlpatterns = [
    path('signup/', RegisterView.as_view(), name='signup'),
    path('verify-otp/', VerifyOTPView.as_view(), name='verify-otp'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('forgot-password/', ForgotPasswordView.as_view(), name='forgot-password'),
    path('reset-password/', ResetPasswordView.as_view(), name='reset-password'),
   
]