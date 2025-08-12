# authentication/views.py
# 2e95eac7612d802323ef8f8f77e3559ac8de0036 for talenduser
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.utils import timezone
from django.shortcuts import get_object_or_404

from .models import OTP
from .serializers import (
    RegisterSerializer, OTPSerializer,
    PasswordResetRequestSerializer, PasswordResetConfirmSerializer
)

class RegisterView(generics.GenericAPIView):
    serializer_class = RegisterSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Generate and send OTP
        otp_code = OTP.generate_otp(user)
        send_mail(
            'Your LearnSmart Verification Code',
            f'Your OTP code is: {otp_code}',
            'noreply@learnsmart.com',
            [user.email],
            fail_silently=False,
        )

        return Response({
            "user_id": user.pk,
            "message": "Registration successful. Please check your email for the OTP to verify your account."
        }, status=status.HTTP_201_CREATED)


class VerifyOTPView(generics.GenericAPIView):
    serializer_class = OTPSerializer

    def post(self, request, user_id, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        otp_code = serializer.validated_data['otp']

        user = get_object_or_404(User, pk=user_id)
        otp_instance = get_object_or_404(OTP, user=user)

        if otp_instance.code == otp_code and otp_instance.expires_at > timezone.now():
            user.is_active = True
            user.save()
            otp_instance.delete() # OTP is used, so delete it
            token, _ = Token.objects.get_or_create(user=user)
            return Response({
                "message": "Account verified successfully.",
                "token": token.key
            }, status=status.HTTP_200_OK)

        return Response({"error": "Invalid or expired OTP."}, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetRequestView(generics.GenericAPIView):
    serializer_class = PasswordResetRequestSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        user = get_object_or_404(User, email=email)

        otp_code = OTP.generate_otp(user)
        send_mail(
            'Your Password Reset Code',
            f'Your OTP code for password reset is: {otp_code}',
            'noreply@learnsmart.com',
            [user.email],
            fail_silently=False,
        )
        return Response({
            "user_id": user.pk,
            "message": "OTP for password reset has been sent to your email."
        }, status=status.HTTP_200_OK)


class PasswordResetConfirmView(generics.GenericAPIView):
    serializer_class = PasswordResetConfirmSerializer

    def post(self, request, user_id, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        otp_code = serializer.validated_data['otp']
        new_password = serializer.validated_data['new_password']

        user = get_object_or_404(User, pk=user_id)
        otp_instance = get_object_or_404(OTP, user=user)

        if otp_instance.code == otp_code and otp_instance.expires_at > timezone.now():
            user.set_password(new_password)
            user.save()
            otp_instance.delete()
            return Response({"message": "Password has been reset successfully."}, status=status.HTTP_200_OK)

        return Response({"error": "Invalid or expired OTP."}, status=status.HTTP_400_BAD_REQUEST)

