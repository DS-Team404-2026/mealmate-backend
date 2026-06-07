from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication

from .models import User, UserProfile, UserHealthProfile
from .serializers import (
    SignupSerializer,
    LoginSerializer,
    UserProfileSerializer,
    UserProfileUpdateSerializer,
    UserHealthProfileSerializer,
    UserHealthProfileUpdateSerializer,
)

class SignupView(APIView):
    def post(self, request):
        email = request.data.get("email")

        if User.objects.filter(email=email).exists():
            return Response(
                {
                    "email": ["이미 사용 중인 이메일입니다."]
                },
                status=status.HTTP_409_CONFLICT
            )

        serializer = SignupSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.save()

            return Response(
                {
                    "message": "회원가입이 완료되었습니다.",
                    "user": {
                        "user_id": user.id,
                        "email": user.email,
                        "nickname": user.nickname,
                    }
                },
                status=status.HTTP_201_CREATED
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class LoginView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.validated_data["user"]

            refresh = RefreshToken.for_user(user)

            return Response(
                {
                    "message": "로그인에 성공했습니다.",
                    "access_token": str(refresh.access_token),
                    "refresh_token": str(refresh),
                    "user": {
                        "user_id": user.id,
                        "email": user.email,
                        "nickname": user.nickname,
                    }
                },
                status=status.HTTP_200_OK
            )

        return Response(
            {
                "detail": "이메일 또는 비밀번호가 일치하지 않습니다."
            },
            status=status.HTTP_401_UNAUTHORIZED
        )
    
class UserProfileView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            profile = UserProfile.objects.get(user=request.user)
        except UserProfile.DoesNotExist:
            return Response(
                {
                    "detail": "프로필이 존재하지 않습니다."
                },
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = UserProfileSerializer(profile)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request):
        try:
            profile = UserProfile.objects.get(user=request.user)
        except UserProfile.DoesNotExist:
            return Response(
                {
                    "detail": "프로필이 존재하지 않습니다."
                },
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = UserProfileUpdateSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        user = request.user

        if "nickname" in data:
            user.nickname = data["nickname"]
            user.save(update_fields=["nickname"])

        if "cooking_level" in data:
            profile.cooking_level = data["cooking_level"]

        if "housing" in data:
            profile.housing = data["housing"]

        if "preference" in data:
            profile.preference = ",".join(data["preference"])

        profile.save()

        return Response(
            {
                "message": "마이페이지 정보가 수정되었습니다.",
                "profile": {
                    "profile_id": profile.id,
                    "user_id": user.id,
                    "nickname": user.nickname,
                    "cooking_level": profile.cooking_level,
                    "housing": profile.housing,
                    "preference": [
                        item.strip()
                        for item in profile.preference.split(",")
                        if item.strip()
                    ] if profile.preference else []
                }
            },
            status=status.HTTP_200_OK
        )
    
class UserHealthProfileView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            health_profile = UserHealthProfile.objects.get(user=request.user)
        except UserHealthProfile.DoesNotExist:
            return Response(
                {"detail": "건강정보가 존재하지 않습니다."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = UserHealthProfileSerializer(health_profile)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def patch(self, request):
        try:
            health_profile = UserHealthProfile.objects.get(user=request.user)
        except UserHealthProfile.DoesNotExist:
            return Response(
                {"detail": "건강정보가 존재하지 않습니다."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = UserHealthProfileUpdateSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data

        if "blood_pressure" in data:
            health_profile.blood_pressure = data["blood_pressure"]

        if "diseases" in data:
            health_profile.diseases = data["diseases"]

        if "allergies" in data:
            health_profile.allergies = data["allergies"]

        if "height" in data:
            health_profile.height = data["height"]

        if "weight" in data:
            health_profile.weight = data["weight"]

        if "diets" in data:
            health_profile.diets = data["diets"]

        if health_profile.height and health_profile.weight:
            height_m = health_profile.height / 100
            health_profile.bmi = round(health_profile.weight / (height_m ** 2), 1)

        health_profile.save()

        return Response(
            {
                "message": "건강정보가 수정되었습니다.",
                "health_profile": UserHealthProfileSerializer(health_profile).data
            },
            status=status.HTTP_200_OK
        )