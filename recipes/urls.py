# from django.urls import path
# from .views import RecipeRecommendationView

# urlpatterns = [
#     # 프론트엔드가 /api/v1/recipes/recommend/ 로 요청을 보낼 때 내 뷰와 연결해줌
#     path('recommend/', RecipeRecommendationView.as_view(), name='recipe-recommendation'),

#     #10/12 추가 마이페이지 북마크 목록 조회 API
#     path('bookmarks/', UserBookmarkListView.as_view(), name='user-bookmarks'),

#     # 레시피 후기(피드백) 등록/수정 API
#     path('feedback/', RecipeFeedbackCreateView.as_view(), name='recipe-feedback'),
# ]

from django.urls import path
# 🚨 뷰 3개를 빠짐없이 불러오기!
from .views import RecipeRecommendationView, UserBookmarkListView, RecipeFeedbackCreateView

urlpatterns = [
    path('recommend/', RecipeRecommendationView.as_view(), name='recipe-recommendation'),
    path('bookmarks/', UserBookmarkListView.as_view(), name='user-bookmarks'),
    path('feedback/', RecipeFeedbackCreateView.as_view(), name='recipe-feedback'),
]