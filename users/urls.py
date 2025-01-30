from django.urls import path
from .views import RegisterView, VerifyOTPView

urlpatterns = [
    path('signup/', RegisterView.as_view(), name='signup'),
    path('verify-otp/', VerifyOTPView.as_view(), name='verify-otp'),
   
]