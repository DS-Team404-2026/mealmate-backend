from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import User
from .serializers import SignupSerializer


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