from django.contrib import admin

from django.contrib import admin
from .models import Recipe, RecipeStep, RecipeRecommendation, RecipeBook, RecipeFeedback

# 장고 관리자 페이지에 레시피 관련 테이블들 등록하기
admin.site.register(Recipe)
admin.site.register(RecipeStep)
admin.site.register(RecipeRecommendation)
admin.site.register(RecipeBook)
admin.site.register(RecipeFeedback)