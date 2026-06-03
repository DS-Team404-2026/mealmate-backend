from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User
from .serializers import SignupSerializer, LoginSerializer


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