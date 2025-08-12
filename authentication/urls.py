# --- authentication/urls.py ---
from django.urls import path
from rest_framework.authtoken.views import obtain_auth_token
from .views import (
    RegisterView, VerifyOTPView,
    PasswordResetRequestView, PasswordResetConfirmView
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('verify-otp/<int:user_id>/', VerifyOTPView.as_view(), name='verify-otp'),
    path('login/', obtain_auth_token, name='login'), # Standard DRF login view
    path('password-reset/', PasswordResetRequestView.as_view(), name='password-reset-request'),
    path('password-reset-confirm/<int:user_id>/', PasswordResetConfirmView.as_view(), name='password-reset-confirm'),
]
