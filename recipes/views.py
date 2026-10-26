import os
import re  # 🚨 텍스트에서 한글 재료명만 뽑아내기 위해 꼭 필요해!
import numpy as np
from openai import OpenAI
from sklearn.metrics.pairwise import cosine_similarity
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from .models import Recipe, RecipeRecommendation, RecipeBook, RecipeFeedback

# ---------------------------------------------------------
# 1. AI 하이브리드 추천 뷰
# ---------------------------------------------------------
class RecipeRecommendationView(APIView):

    permission_classes = [IsAuthenticated]


    def post(self, request):

        # 🚨 프론트가 보낸 토큰이 누군지 VS Code 터미널에 찍어보기!
        print("====================================")
        print("👤 현재 요청 유저:", request.user)
        print("🔑 인증 성공 여부:", request.user.is_authenticated)
        print("====================================")

        
        raw_ingredients = request.data.get('available_ingredients', [])
        
        if not raw_ingredients:
            return Response({"message": "보유 식재료를 최소 하나 이상 선택해주세요."}, status=status.HTTP_400_BAD_REQUEST)

        api_key = os.getenv("OPENAI_API_KEY", "a2186034bae948678800")
        client = OpenAI(api_key=api_key)
        prompt = f"다음 사용자가 입력한 식재료 리스트에서 특수문자와 단위를 제거하고, 식약처 표준 식품명으로 치환해줘. 파이썬 리스트 형태로만 결과(예: ['달걀', '대파', '두부'])를 반환해줘. 입력: {raw_ingredients}"

        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}]
            )
            clean_ingredients = eval(response.choices[0].message.content.strip())
        except Exception:
            clean_ingredients = raw_ingredients

        all_recipes = Recipe.objects.all()
        if not all_recipes.exists():
            return Response({"message": "추천 후보 레시피가 DB에 없습니다."}, status=status.HTTP_404_NOT_FOUND)

        # 🚨 [수정됨] DB의 통짜 텍스트(ingredient_lines)에서 한글 재료 단어만 쏙쏙 뽑아 모으기!
        all_recipe_ingredients = []
        for recipe in all_recipes:
            raw_text = getattr(recipe, 'ingredient_lines', '')
            words = re.findall(r'[가-힣]{2,}', raw_text)
            all_recipe_ingredients.extend(words)

        vocab = list(set(all_recipe_ingredients + clean_ingredients))
        vocab_dim = len(vocab)

        if vocab_dim == 0:
            return Response({"message": "분석할 수 있는 재료 데이터가 부족합니다."}, status=status.HTTP_400_BAD_REQUEST)

        user_vector = np.zeros(vocab_dim)
        for ing in clean_ingredients:
            if ing in vocab:
                user_vector[vocab.index(ing)] = 1

        recommendation_list = []

        for recipe in all_recipes:
            # 🚨 [수정됨] 추천 돌릴 때도 똑같이 텍스트에서 한글 단어만 뽑아줌
            raw_text = getattr(recipe, 'ingredient_lines', '')
            recipe_ingredients = list(set(re.findall(r'[가-힣]{2,}', raw_text)))

            if not recipe_ingredients:
                continue

            recipe_vector = np.zeros(vocab_dim)
            for ing in recipe_ingredients:
                if ing in vocab:
                    recipe_vector[vocab.index(ing)] = 1

            cos_sim = cosine_similarity([user_vector], [recipe_vector])[0][0]
            matched_count = len(set(clean_ingredients) & set(recipe_ingredients))
            match_weight = matched_count / len(recipe_ingredients) if recipe_ingredients else 0
            
            taste_weight = 1.0 

            total_score = (cos_sim * 0.4) + (match_weight * 0.4) + (taste_weight * 0.2)
            missing_ingredients = list(set(recipe_ingredients) - set(clean_ingredients))

            recommendation_list.append({
                'recipe_id': recipe.id,
                'recipe': recipe,
                'recipe_name': recipe.title,
                'difficulty': getattr(recipe, 'difficulty', '중'),
                'cooking_time': getattr(recipe, 'cooking_time', 30),
                'calories': getattr(recipe, 'calories', 500),
                'total_score': float(total_score),
                'missing_ingredients': missing_ingredients
            })

        recommendation_list.sort(key=lambda x: x['total_score'], reverse=True)
        top_recommendations = recommendation_list[:10]

        if not top_recommendations:
            return Response({"message": "조건에 맞는 추천 레시피를 찾지 못했습니다."}, status=status.HTTP_404_NOT_FOUND)

        best_item = top_recommendations[0]
        user_instance = request.user if request.user.is_authenticated else None
        
        recommendation = RecipeRecommendation.objects.create(
            user=user_instance,
            recipe=best_item['recipe'],
            available_ingredients=raw_ingredients,
            recommendation_type='hybrid_cosine_openai'
        )

        return Response({
            "recommendation_id": recommendation.id,
            "top_recipes": [
                {
                    "recipe_id": item['recipe_id'],
                    "title": item['recipe_name'],
                    "difficulty": item['difficulty'],
                    "cooking_time": item['cooking_time'],
                    "calories": item['calories'],
                    "match_score": round(item['total_score'] * 100, 1),
                    "missing_ingredients": item['missing_ingredients']
                } for item in top_recommendations
            ],
            "status": "success"
        }, status=status.HTTP_200_OK)

# ---------------------------------------------------------
# 2. 북마크 목록 조회 뷰
# ---------------------------------------------------------
class UserBookmarkListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        bookmarks = RecipeBook.objects.filter(user=request.user, is_favorite=True).select_related('recipe')
        bookmark_list = []
        for b in bookmarks:
            recipe = b.recipe
            bookmark_list.append({
                "recipe_id": recipe.id,
                "title": recipe.title,
                "difficulty": getattr(recipe, 'difficulty', '중'),
                "cooking_time": getattr(recipe, 'cooking_time', 30),
                "preference": b.preference,
            })

        return Response({
            "count": len(bookmark_list),
            "bookmarks": bookmark_list
        }, status=status.HTTP_200_OK)



    # 🚨 [추가] POST (레시피 저장/평가)
    def post(self, request):
        recipe_id = request.data.get('recipe_id')
        preference = request.data.get('preference', '')
        is_favorite = request.data.get('is_favorite', True)

        if not recipe_id:
            return Response({"message": "recipe_id가 필요합니다."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            recipe = Recipe.objects.get(id=recipe_id)
        except Recipe.DoesNotExist:
            return Response({"message": "해당 레시피가 없습니다."}, status=status.HTTP_404_NOT_FOUND)

        bookmark, created = RecipeBook.objects.update_or_create(
            user=request.user,
            recipe=recipe,
            defaults={
                'preference': preference,
                'is_favorite': is_favorite
            }
        )
        msg = "북마크 저장 완료" if created else "북마크 수정 완료"
        return Response({"status": "success", "message": msg}, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

# ---------------------------------------------------------
# 3. 레시피 후기/피드백 등록 뷰
# ---------------------------------------------------------
class RecipeFeedbackCreateView(APIView):
    def post(self, request):
        recommendation_id = request.data.get('recommendation_id')
        like_dislike = request.data.get('like_dislike')
        difficulty_result = request.data.get('difficulty_result')
        comment = request.data.get('comment', '')

        if recommendation_id is None or like_dislike is None or difficulty_result is None:
            return Response({"message": "필수 항목이 누락되었습니다."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            recommendation = RecipeRecommendation.objects.get(id=recommendation_id)
        except RecipeRecommendation.DoesNotExist:
            return Response({"message": "해당 추천 기록을 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)

        feedback, created = RecipeFeedback.objects.update_or_create(
            recommendation=recommendation,
            defaults={
                'like_dislike': like_dislike,
                'difficulty_result': difficulty_result,
                'comment': comment
            }
        )

        msg = "등록 성공" if created else "수정 성공"
        return Response({"status": "success", "message": msg}, status=status.HTTP_200_OK if not created else status.HTTP_201_CREATED)




    # ---------------------------------------------------------
# 4. 레시피 상세 조회 뷰 (GET /api/v1/recipes/{id}/)
# ---------------------------------------------------------
class RecipeDetailView(APIView):
    def get(self, request, pk):
        try:
            recipe = Recipe.objects.get(pk=pk)
            return Response({
                "id": recipe.id,
                "title": recipe.title,
                "ingredient_lines": getattr(recipe, 'ingredient_lines', ''),
                "difficulty": getattr(recipe, 'difficulty', '중'),
                "cooking_time": getattr(recipe, 'cooking_time', 30),
                "calories": getattr(recipe, 'calories', 500),
            }, status=status.HTTP_200_OK)
        except Recipe.DoesNotExist:
            return Response({"message": "해당 레시피를 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)

# ---------------------------------------------------------
# 5. 조리 단계 조회 뷰 (GET /api/v1/recipes/{id}/steps/)
# ---------------------------------------------------------
class RecipeStepView(APIView):
    def get(self, request, pk):
        try:
            recipe = Recipe.objects.get(pk=pk)
            # Recipe 모델에 조리 단계 필드명(instructions 또는 steps)에 맞춰 불러옴
            steps = getattr(recipe, 'instructions', getattr(recipe, 'steps', '조리 단계 정보가 없습니다.'))
            return Response({
                "recipe_id": recipe.id,
                "steps": steps
            }, status=status.HTTP_200_OK)
        except Recipe.DoesNotExist:
            return Response({"message": "해당 레시피를 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)