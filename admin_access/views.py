import random
from django.core.mail import send_mail
from django.contrib.auth import authenticate, login
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from .models import AdminUser
from .serializers import LoginSerializer, OTPVerifySerializer
from django.http import JsonResponse

# ✅ 1. CSRF token setter
@ensure_csrf_cookie
def get_csrf_token(request):
    return JsonResponse({'detail': 'CSRF cookie set'})

# ✅ 2. Class-based CSRF token setter
@method_decorator(ensure_csrf_cookie, name='dispatch')
class GetCSRFTokenView(APIView):
    def get(self, request):
        return Response({'message': 'CSRF cookie set'}, status=status.HTTP_200_OK)

# ✅ 3. Login view with OTP send
@method_decorator(ensure_csrf_cookie, name='dispatch')  # CSRF protection enforced
class LoginView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = authenticate(
                username=serializer.validated_data['username'],
                password=serializer.validated_data['password']
            )
            if user:
                otp = f"{random.randint(100000, 999999)}"
                user.otp_code = otp
                user.is_verified = False
                user.save()

                send_mail(
                    'Your HaruBayan OTP Code',
                    f'Your OTP code is: {otp}',
                    'harubayan.official@gmail.com',
                    [user.email],
                    fail_silently=False,
                )

                login(request, user)
                return Response({'message': 'OTP sent to email.'}, status=status.HTTP_200_OK)

            return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# ✅ 4. OTP verification view
@method_decorator(ensure_csrf_cookie, name='dispatch')  # CSRF protection enforced
class OTPVerifyView(APIView):
    def post(self, request):
        if not request.user.is_authenticated:
            return Response({'error': 'User not authenticated.'}, status=status.HTTP_403_FORBIDDEN)

        serializer = OTPVerifySerializer(data=request.data)
        if serializer.is_valid():
            otp = serializer.validated_data['otp_code']
            user = request.user
            if user.otp_code == otp:
                user.is_verified = True
                user.save()
                return Response({'message': 'Login successful!', 'role': user.role}, status=status.HTTP_200_OK)
            return Response({'error': 'Invalid OTP'}, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
