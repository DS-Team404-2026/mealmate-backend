import re
import math
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Recipe, RecipeRecommendation

class RecipeRecommendationView(APIView):
    def post(self, request):
        # 1. 프론트엔드가 보낸 '보유 식재료' 목록 받기 (예: ["닭가슴살", "양파", "계란"])
        user_ingredients = request.data.get('available_ingredients', [])
        recommendation_type = request.data.get('recommendation_type', 'cosine')
        
        if not user_ingredients:
            return Response({"message": "보유 식재료를 최소 하나 이상 선택해주세요."}, status=status.HTTP_400_BAD_REQUEST)

        # 2. DB에 저장된 식약처 레시피 전체 가져오기
        all_recipes = Recipe.objects.all()
        
        if not all_recipes.exists():
            return Response({"message": "추천 후보 레시피가 DB에 없습니다. API 수집을 먼저 진행해주세요."}, status=status.HTTP_404_NOT_FOUND)

        best_recipe = None
        highest_similarity = -1.0
        final_missing_ingredients = []

        # 3. 모든 레시피를 순회하며 '코사인 유사도' 기반 가중치 연산 실행
        for recipe in all_recipes:
            raw_ingredient_text = getattr(recipe, 'ingredient_lines', '') 
            
            if not raw_ingredient_text:
                continue


            # [텍스트 마이닝] 정규식을 이용해 순수 재료명만 추출 및 중복 제거
            recipe_ingredients = re.findall(r'[가-힣]{2,}', raw_ingredient_text)
            recipe_ingredients = list(set(recipe_ingredients)) 

            if not recipe_ingredients:
                continue

            # [핵심 기술: 코사인 유사도 연산]
            # 유저의 냉장고 재료와 레시피 필요 재료의 '전체 고유 단어 사전(Vocabulary)' 생성
            all_words = list(set(user_ingredients + recipe_ingredients))
            
            # 단어 사전을 바탕으로 유저 벡터와 레시피 벡터(원-핫 인코딩 형식) 생성
            user_vector = [1 if word in user_ingredients else 0 for word in all_words]
            recipe_vector = [1 if word in recipe_ingredients else 0 for word in all_words]
            
            # 수학적 코사인 유사도 공식 분자분모 계산 (Dot Product / (Norm_A * Norm_B))
            dot_product = sum(u * r for u, r in zip(user_vector, recipe_vector))
            norm_user = math.sqrt(sum(u ** 2 for u in user_vector))
            norm_recipe = math.sqrt(sum(r ** 2 for r in recipe_vector))
            
            # 분모가 0이 되는 예외 방지 및 유사도 도출
            if norm_user == 0 or norm_recipe == 0:
                similarity = 0.0
            else:
                similarity = dot_product / (norm_user * norm_recipe)

            # 미포함(부족한) 재료 분석
            missing_ingredients = list(set(recipe_ingredients) - set(user_ingredients))
            
            # 가장 코사인 유사도(매칭률)가 높은 레시피를 최종 후보로 갱신
            if similarity > highest_similarity:
                highest_similarity = similarity
                best_recipe = recipe
                final_missing_ingredients = missing_ingredients

        # 4. 매칭 결과 예외 처리
        if not best_recipe or highest_similarity <= 0:
            return Response({"message": "보유하신 재료와 연관성이 높은 레시피를 찾지 못했습니다."}, status=status.HTTP_404_NOT_FOUND)

        # 5. 추천 기록을 DB에 저장 (스냅샷 생성, 로그인 유저용 예외 처리 포함)
        user_instance = request.user if request.user.is_authenticated else None
        recommendation = RecipeRecommendation.objects.create(
            user=user_instance,
            recipe=best_recipe,
            available_ingredients=user_ingredients,
            recommendation_type=recommendation_type
        )

        # 6. 명세서(12번 엔티티) 규격에 완벽히 맞춘 100% 만족 Response 반환
        return Response({
            "recommendation_id": recommendation.id,
            "recipe_id": best_recipe.id,
            "title": best_recipe.title,
            "difficulty": best_recipe.difficulty,
            "cooking_time": best_recipe.cooking_time,
            "calories": best_recipe.calories,
            "ingredient_match_percent": round(highest_similarity * 100, 1), # 백분율 환산
            "missing_ingredients": final_missing_ingredients,
            "status": "success",
            "message": "코사인 유사도 기반 알고리즘으로 레시피 추천이 완료되었습니다."
        }, status=status.HTTP_200_OK)