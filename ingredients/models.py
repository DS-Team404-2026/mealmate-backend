from django.db import models
from accounts.models import User  # 유저 모델 가져오기

# 1. 식재료 사전 (엔티티 9번)
class Ingredient(models.Model):
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=50)
    unit = models.CharField(max_length=20)  # g, ml, 개 등

    def __str__(self):
        return self.name

# 2. 냉장고 재료 (엔티티 10~11번)
class UserRefrigerator(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=10, decimal_places=1)
    unit = models.CharField(max_length=20)
    storage_type = models.CharField(max_length=20) # 냉장, 냉동, 상온
    expired_at = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)