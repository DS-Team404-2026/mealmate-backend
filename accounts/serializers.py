from django.contrib.auth import authenticate
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

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        email = data["email"]
        password = data["password"]

        user = authenticate(
            username=email,
            password=password
        )

        if user is None:
            raise serializers.ValidationError("이메일 또는 비밀번호가 일치하지 않습니다.")

        data["user"] = user
        return data
    
class UserProfileSerializer(serializers.Serializer):
    profile_id = serializers.IntegerField(source="id", read_only=True)
    user_id = serializers.IntegerField(source="user.id", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)
    nickname = serializers.CharField(source="user.nickname", read_only=True)
    cooking_level = serializers.IntegerField(read_only=True)
    housing = serializers.CharField(read_only=True)
    preference = serializers.SerializerMethodField()

    def get_preference(self, obj):
        if not obj.preference:
            return []

        if isinstance(obj.preference, list):
            return obj.preference

        return [
            item.strip()
            for item in obj.preference.split(",")
            if item.strip()
        ]
    
class UserProfileUpdateSerializer(serializers.Serializer):
    nickname = serializers.CharField(required=False, allow_blank=True)
    cooking_level = serializers.IntegerField(required=False)
    housing = serializers.CharField(required=False, allow_blank=True)
    preference = serializers.ListField(
        child=serializers.CharField(),
        required=False
    )