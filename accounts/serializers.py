from rest_framework import serializers
from .models import User, UserProfile, UserHealthProfile, UserEnvironment


class SignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ["id", "email", "password", "nickname"]

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("이미 사용 중인 이메일입니다.")
        return value

    def create(self, validated_data):
        email = validated_data["email"]
        password = validated_data["password"]
        nickname = validated_data["nickname"]

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