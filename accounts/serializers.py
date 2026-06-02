from rest_framework import serializers
from .models import User, UserProfile, UserHealthProfile, UserEnvironment


class SignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ["id", "email", "password", "password_confirm", "nickname"]

    def validate(self, data):
        if data["password"] != data["password_confirm"]:
            raise serializers.ValidationError({
                "password_confirm": "비밀번호가 일치하지 않습니다."
            })
        return data

    def create(self, validated_data):
        email = validated_data["email"]
        password = validated_data["password"]
        nickname = validated_data["nickname"]

        # password_confirm은 User 모델에 저장하는 값이 아니므로 제거
        validated_data.pop("password_confirm")

        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            nickname=nickname
        )

        UserProfile.objects.create(user=user)
        UserHealthProfile.objects.create(user=user)
        UserEnvironment.objects.create(user=user)

        return user