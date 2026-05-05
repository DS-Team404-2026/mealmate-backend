from django.db import models
from accounts.models import User
from ingredients.models import Ingredient

# 1. 레시피 기본 정보 (엔티티 13번)
class Recipe(models.Model):
    title = models.CharField(max_length=200)
    difficulty = models.IntegerField()
    cooking_time = models.IntegerField()
    calories = models.FloatField()
    protein = models.FloatField()
    carbs = models.FloatField()
    fat = models.FloatField()

# 2. 조리 단계 (엔티티 14번)
class RecipeStep(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='steps')
    step_order = models.IntegerField()
    description = models.TextField()

# 3. AI 추천 기록 (엔티티 12번)
class RecipeRecommendation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    available_ingredients = models.JSONField() # 당시 보유 재료 스냅샷
    recommendation_type = models.CharField(max_length=20) # gpt, search 등
    created_at = models.DateTimeField(auto_now_add=True)

# 4. 레시피 북마크/평가 (엔티티 15번)
class RecipeBook(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    is_favorite = models.BooleanField(default=False)
    preference = models.CharField(max_length=10) # 상, 중, 하

# 5. 레시피 후기/피드백 (엔티티 16번)
class RecipeFeedback(models.Model):
    recommendation = models.OneToOneField(RecipeRecommendation, on_delete=models.CASCADE)
    like_dislike = models.IntegerField() # 1:좋아요, 0:싫어요
    difficulty_result = models.IntegerField()
    comment = models.TextField(blank=True)