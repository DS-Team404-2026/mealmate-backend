from django.urls import path
from .views import RecipeRecommendationView

urlpatterns = [
    # 프론트엔드가 /api/v1/recipes/recommend/ 로 요청을 보낼 때 내 뷰와 연결해줌
    path('recommend/', RecipeRecommendationView.as_view(), name='recipe-recommendation'),
]