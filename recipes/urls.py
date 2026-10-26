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

# from django.urls import path
# # 🚨 뷰 3개를 빠짐없이 불러오기!
# from .views import RecipeRecommendationView, UserBookmarkListView, RecipeFeedbackCreateView

# urlpatterns = [
#     path('recommend/', RecipeRecommendationView.as_view(), name='recipe-recommendation'),
#     path('bookmarks/', UserBookmarkListView.as_view(), name='user-bookmarks'),
#     path('feedback/', RecipeFeedbackCreateView.as_view(), name='recipe-feedback'),
# ]

from django.urls import path
from .views import RecipeRecommendationView, UserBookmarkListView, RecipeFeedbackCreateView

urlpatterns = [
    # 1. AI 레시피 추천 (명세서: /api/v1/recipe-recommendations/)
    path('recipe-recommendations/', RecipeRecommendationView.as_view(), name='recipe-recommendation'),
    
    # 2. 레시피 후기 등록 (명세서: /api/v1/recipe-feedback/)
    path('recipe-feedback/', RecipeFeedbackCreateView.as_view(), name='recipe-feedback'),
    
    # 3. 저장한 레시피 목록 조회 (명세서: /api/recipes/saved/ -> 팀원과 합의 후 v1을 넣기로 했다면 recipes/saved/ 로 쓴다)
    # 만약 최상위에 /api/v1/이 걸려있다면 path('recipes/saved/', ...) 형태로 맞춰주면 됨.
    path('recipes/saved/', UserBookmarkListView.as_view(), name='user-bookmarks'),
]