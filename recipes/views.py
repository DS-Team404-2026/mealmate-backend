from django.shortcuts import render

# Create your views here.
import re
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Recipe, RecipeRecommendation

class RecipeRecommendationView(APIView):
    def post(self, request):
        # 1. 프론트엔드가 보낸 '보유 식재료' 목록 받기 (예: ["닭가슴살", "양파", "계란"])
        user_ingredients = request.data.get('available_ingredients', [])
        recommendation_type = request.data.get('recommendation_type', 'gpt')
        
        if not user_ingredients:
            return Response({"message": "보유 식재료를 최소 하나 이상 선택해주세요."}, status=status.HTTP_400_BAD_REQUEST)

        # 2. DB에 저장된 식약처 레시피 전체 가져오기
        all_recipes = Recipe.objects.all()
        
        if not all_recipes.exists():
            return Response({"message": "추천 후보 레시피가 DB에 없습니다. API 수집을 먼저 진행해주세요."}, status=status.HTTP_404_NOT_FOUND)

        best_recipe = None
        highest_match_percent = -1
        final_missing_ingredients = []

        # 3. 모든 레시피를 순회하며 내 냉장고 재료와 매칭률 계산 (알고리즘)
        for recipe in all_recipes:
            #팁: 실제 구현 시에는 recipe와 연결된 재료(RecipeIngredient) 목록을 가져와야
            # 식약처 API의 재료 문자열 (예: "닭가슴살 150g, 양파 1/2개, 후추 약간")
            # 만약 모델에 해당 필드가 없다면 텍스트 필드를 추가하거나 아래 로직을 참고하세요.
            raw_ingredient_text = getattr(recipe, 'ingredient_lines', '') 
            
            if not raw_ingredient_text:
                continue

            # 💡 [핵심 기술] 텍스트에서 숫자, 단위(g, 개, 컵), 특수문자를 제거하고 순수 재료명만 추출
            # 정규식을 이용해 한글 2글자 이상 단어만 추출합니다.
            recipe_ingredients = re.findall(r'[가-힣]{2,}', raw_ingredient_text)
            # 중복 제거 (예: '양파'가 소스에도 들어가고 고명에도 들어갈 경우 하나로 합침)
            recipe_ingredients = list(set(recipe_ingredients)) 

            if not recipe_ingredients:
                continue

            # 내 냉장고 재료와 레시피 필요 재료 비교
            matched_ingredients = set(user_ingredients) & set(recipe_ingredients)
            missing_ingredients = list(set(recipe_ingredients) - set(user_ingredients))
            
            # 일치율(%) 계산
            match_percent = (len(matched_ingredients) / len(recipe_ingredients)) * 100

            # 가장 매칭률이 높은 레시피를 최종 후보로 선택
            if match_percent > highest_match_percent:
                highest_match_percent = match_percent
                best_recipe = recipe
                final_missing_ingredients = missing_ingredients

        # 4. 매칭 결과 처리
        if not best_recipe or highest_match_percent == 0:
            return Response({"message": "보유하신 재료로 추천할 수 있는 레시피가 없습니다."}, status=status.HTTP_404_NOT_FOUND)

        # 5. 추천 기록을 DB에 저장 (스냅샷 생성)
        recommendation = RecipeRecommendation.objects.create(
            user=request.user,
            recipe=best_recipe,
            available_ingredients=user_ingredients,
            recommendation_type=recommendation_type
        )

        # 6. 명세서(12번 엔티티) 규격에 완벽히 맞춘 Response 반환
        return Response({
            "recommendation_id": recommendation.id,
            "recipe_id": best_recipe.id,
            "title": best_recipe.title,
            "difficulty": best_recipe.difficulty,
            "cooking_time": best_recipe.cooking_time,
            "calories": best_recipe.calories,
            "ingredient_match_percent": round(highest_match_percent, 1),
            "missing_ingredients": final_missing_ingredients,
            "status": "success",
            "message": "AI 레시피 추천이 완료되었습니다."
        }, status=status.HTTP_200_OK)