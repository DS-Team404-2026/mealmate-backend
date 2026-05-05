from django.db import models
from django.contrib.auth.models import AbstractUser

# 1. 기본 유저 모델 (엔티티 1번)
class User(AbstractUser):
    nickname = models.CharField(max_length=50)
    
    def __str__(self):
        return self.email

# 2. 마이페이지 프로필 (엔티티 2~3번)
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    cooking_level = models.IntegerField(default=1)
    housing = models.CharField(max_length=50, default="자취")
    preference = models.JSONField(default=list)  # ["한식", "양식"] 형태

# 3. 건강 정보 (엔티티 4~5번)
class UserHealthProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='health')
    height = models.IntegerField(null=True, blank=True)
    weight = models.IntegerField(null=True, blank=True)
    bmi = models.FloatField(null=True, blank=True)
    blood_pressure = models.CharField(max_length=50, null=True, blank=True)
    diseases = models.JSONField(default=list)
    allergies = models.TextField(null=True, blank=True)
    diets = models.JSONField(default=list)

# 4. 조리 환경 (엔티티 6~7번)
class UserEnvironment(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='environment')
    induction = models.BooleanField(default=False)
    microwave = models.BooleanField(default=False)
    airfryer = models.BooleanField(default=False)
    blender = models.BooleanField(default=False)