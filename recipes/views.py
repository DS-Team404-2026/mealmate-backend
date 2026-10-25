# import re
# import math
# from django.shortcuts import render
# from rest_framework.views import APIView
# from rest_framework.response import Response
# from rest_framework import status
# from .models import Recipe, RecipeRecommendation

# class RecipeRecommendationView(APIView):
#     def post(self, request):
#         # 1. 프론트엔드가 보낸 '보유 식재료' 목록 받기 (예: ["닭가슴살", "양파", "계란"])
#         user_ingredients = request.data.get('available_ingredients', [])
#         recommendation_type = request.data.get('recommendation_type', 'cosine')
        
#         if not user_ingredients:
#             return Response({"message": "보유 식재료를 최소 하나 이상 선택해주세요."}, status=status.HTTP_400_BAD_REQUEST)

#         # 2. DB에 저장된 식약처 레시피 전체 가져오기
#         all_recipes = Recipe.objects.all()
        
#         if not all_recipes.exists():
#             return Response({"message": "추천 후보 레시피가 DB에 없습니다. API 수집을 먼저 진행해주세요."}, status=status.HTTP_404_NOT_FOUND)

#         best_recipe = None
#         highest_similarity = -1.0
#         final_missing_ingredients = []

#         # 3. 모든 레시피를 순회하며 '코사인 유사도' 기반 가중치 연산 실행
#         for recipe in all_recipes:
#             raw_ingredient_text = getattr(recipe, 'ingredient_lines', '') 
            
#             if not raw_ingredient_text:
#                 continue


#             # [텍스트 마이닝] 정규식을 이용해 순수 재료명만 추출 및 중복 제거
#             recipe_ingredients = re.findall(r'[가-힣]{2,}', raw_ingredient_text)
#             recipe_ingredients = list(set(recipe_ingredients)) 

#             if not recipe_ingredients:
#                 continue

#             # [핵심 기술: 코사인 유사도 연산]
#             # 유저의 냉장고 재료와 레시피 필요 재료의 '전체 고유 단어 사전(Vocabulary)' 생성
#             all_words = list(set(user_ingredients + recipe_ingredients))
            
#             # 단어 사전을 바탕으로 유저 벡터와 레시피 벡터(원-핫 인코딩 형식) 생성
#             user_vector = [1 if word in user_ingredients else 0 for word in all_words]
#             recipe_vector = [1 if word in recipe_ingredients else 0 for word in all_words]
            
#             # 수학적 코사인 유사도 공식 분자분모 계산 (Dot Product / (Norm_A * Norm_B))
#             dot_product = sum(u * r for u, r in zip(user_vector, recipe_vector))
#             norm_user = math.sqrt(sum(u ** 2 for u in user_vector))
#             norm_recipe = math.sqrt(sum(r ** 2 for r in recipe_vector))
            
#             # 분모가 0이 되는 예외 방지 및 유사도 도출
#             if norm_user == 0 or norm_recipe == 0:
#                 similarity = 0.0
#             else:
#                 similarity = dot_product / (norm_user * norm_recipe)

#             # 미포함(부족한) 재료 분석
#             missing_ingredients = list(set(recipe_ingredients) - set(user_ingredients))
            
#             # 가장 코사인 유사도(매칭률)가 높은 레시피를 최종 후보로 갱신
#             if similarity > highest_similarity:
#                 highest_similarity = similarity
#                 best_recipe = recipe
#                 final_missing_ingredients = missing_ingredients

#         # 4. 매칭 결과 예외 처리
#         if not best_recipe or highest_similarity <= 0:
#             return Response({"message": "보유하신 재료와 연관성이 높은 레시피를 찾지 못했습니다."}, status=status.HTTP_404_NOT_FOUND)

#         # 5. 추천 기록을 DB에 저장 (스냅샷 생성, 로그인 유저용 예외 처리 포함)
#         user_instance = request.user if request.user.is_authenticated else None
#         recommendation = RecipeRecommendation.objects.create(
#             user=user_instance,
#             recipe=best_recipe,
#             available_ingredients=user_ingredients,
#             recommendation_type=recommendation_type
#         )

#         # 6. 명세서(12번 엔티티) 규격에 완벽히 맞춘 100% 만족 Response 반환
#         return Response({
#             "recommendation_id": recommendation.id,
#             "recipe_id": best_recipe.id,
#             "title": best_recipe.title,
#             "difficulty": best_recipe.difficulty,
#             "cooking_time": best_recipe.cooking_time,
#             "calories": best_recipe.calories,
#             "ingredient_match_percent": round(highest_similarity * 100, 1), # 백분율 환산
#             "missing_ingredients": final_missing_ingredients,
#             "status": "success",
#             "message": "코사인 유사도 기반 알고리즘으로 레시피 추천이 완료되었습니다."
#         }, status=status.HTTP_200_OK)


# #10/12 추가
# from rest_framework.permissions import IsAuthenticated
# from .models import RecipeBook

# class UserBookmarkListView(APIView):
#     permission_classes = [IsAuthenticated] # 로그인한 유저만 조회 가능

#     def get(self, request):
#         # 현재 로그인한 유저의 북마크 중 is_favorite가 True인 것들 가져오기
#         bookmarks = RecipeBook.objects.filter(user=request.user, is_favorite=True).select_related('recipe')
        
#         bookmark_list = []
#         for b in bookmarks:
#             recipe = b.recipe
#             bookmark_list.append({
#                 "recipe_id": recipe.id,
#                 "title": recipe.title,
#                 "difficulty": recipe.difficulty,
#                 "cooking_time": recipe.cooking_time,
#                 "calories": recipe.calories,
#                 "preference": b.preference, # 상/중/하 평가 내용
#             })

#         return Response({
#             "count": len(bookmark_list),
#             "bookmarks": bookmark_list
#         }, status=status.HTTP_200_OK)



# from .models import RecipeFeedback

# class RecipeFeedbackCreateView(APIView):
#     def post(self, request):
#         recommendation_id = request.data.get('recommendation_id')
#         like_dislike = request.data.get('like_dislike')       # 1: 좋아요, 0: 싫어요
#         difficulty_result = request.data.get('difficulty_result') # 체감 난이도 (숫자)
#         comment = request.data.get('comment', '')             # 후기 텍스트 (선택)

#         # 필수 값 누락 검증
#         if recommendation_id is None or like_dislike is None or difficulty_result is None:
#             return Response(
#                 {"message": "recommendation_id, like_dislike, difficulty_result는 필수 입력 항목입니다."}, 
#                 status=status.HTTP_400_BAD_REQUEST
#             )

#         try:
#             # 추천받았던 기록이 실제로 존재하는지 확인
#             recommendation = RecipeRecommendation.objects.get(id=recommendation_id)
#         except RecipeRecommendation.DoesNotExist:
#             return Response(
#                 {"message": "해당 추천 기록을 찾을 수 없습니다."}, 
#                 status=status.HTTP_404_NOT_FOUND
#             )

#         # OneToOne 관계이므로 이미 후기가 있다면 수정(Update), 없으면 생성(Create)
#         feedback, created = RecipeFeedback.objects.update_or_create(
#             recommendation=recommendation,
#             defaults={
#                 'like_dislike': like_dislike,
#                 'difficulty_result': difficulty_result,
#                 'comment': comment
#             }
#         )

#         status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
#         msg = "레시피 후기가 성공적으로 등록되었습니다." if created else "레시피 후기가 성공적으로 수정되었습니다."

#         return Response({
#             "feedback_id": feedback.id,
#             "recommendation_id": recommendation.id,
#             "like_dislike": feedback.like_dislike,
#             "difficulty_result": feedback.difficulty_result,
#             "comment": feedback.comment,
#             "status": "success",
#             "message": msg


import os
import numpy as np
from openai import OpenAI
from sklearn.metrics.pairwise import cosine_similarity
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Recipe, RecipeRecommendation, UserTasteProfile # UserTasteProfile이 있다면 연동

class RecipeRecommendationView(APIView):
    def post(self, request):
        # 1. 프론트엔드가 보낸 '보유 식재료' 목록 받기
        raw_ingredients = request.data.get('available_ingredients', [])
        
        if not raw_ingredients:
            return Response({"message": "보유 식재료를 최소 하나 이상 선택해주세요."}, status=status.HTTP_400_BAD_REQUEST)

        # 2. OpenAI API를 활용한 식재료 표준화 (동의어 및 단위 제거)
        # .env에 있는 API 키 자동 로드 또는 직접 입력
        api_key = os.getenv("OPENAI_API_KEY", "a2186034bae948678800") # 임시 키 반영
        client = OpenAI(api_key=api_key)

        prompt = f"다음 사용자가 입력한 식재료 리스트에서 특수문자와 단위를 제거하고, 식약처 표준 식품명으로 치환해줘. 파이썬 리스트 형태로만 결과(예: ['달걀', '대파', '두부'])를 반환해줘. 입력: {raw_ingredients}"

        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}]
            )
            # OpenAI가 반환한 텍스트를 파이썬 리스트로 변환
            clean_ingredients = eval(response.choices[0].message.content.strip())
        except Exception as e:
            # 만약 OpenAI 호출에 실패하거나 키 에러가 나면 원본을 그대로 clean_ingredients로 사용 (비상 방어 코드)
            clean_ingredients = raw_ingredients

        # 3. DB에 저장된 식약처 레시피 전체 가져오기
        all_recipes = Recipe.objects.all()
        
        if not all_recipes.exists():
            return Response({"message": "추천 후보 레시피가 DB에 없습니다. API 수집을 먼저 진행해주세요."}, status=status.HTTP_404_NOT_FOUND)

        # 4. 사용자 취향 가중치 로드 (로그인 유저인 경우)
        favorite_categories = {}
        if request.user.is_authenticated:
            user_taste, created = UserTasteProfile.objects.get_or_create(user=request.user)
            favorite_categories = user_taste.category_weights # 예: {'한식': 1.5, '일식': 0.8}

        # 5. 전체 마스터 식재료 사전 생성 (Vocabulary)
        # 레시피 모델에 ingredients_list(또는 파싱된 리스트)가 있다고 가정
        vocab = list(set([ing for recipe in all_recipes for ing in getattr(recipe, 'ingredients_list', [])] + clean_ingredients))
        vocab_dim = len(vocab)

        if vocab_dim == 0:
            return Response({"message": "분석할 수 있는 재료 데이터가 부족합니다."}, status=status.HTTP_400_BAD_REQUEST)

        # 6. 사용자 보유 재료 벡터화 (Binary Vector)
        user_vector = np.zeros(vocab_dim)
        for ing in clean_ingredients:
            if ing in vocab:
                user_vector[vocab.index(ing)] = 1

        recommendation_list = []

        # 7. 하이브리드 스코어링 연산 (Cosine Sim + Match Count + Taste)
        for recipe in all_recipes:
            recipe_ingredients = getattr(recipe, 'ingredients_list', [])
            if not recipe_ingredients:
                continue

            recipe_vector = np.zeros(vocab_dim)
            for ing in recipe_ingredients:
                if ing in vocab:
                    recipe_vector[vocab.index(ing)] = 1

            # 4-1. 코사인 유사도 계산
            cos_sim = cosine_similarity([user_vector], [recipe_vector])[0][0]

            # 4-2. 매칭 재료 개수 가중치 (실용성 보정)
            matched_count = len(set(clean_ingredients) & set(recipe_ingredients))
            match_weight = matched_count / len(recipe_ingredients) if recipe_ingredients else 0

            # 4-3. 개인 선호도(입맛) 가중치 반영 (카테고리가 없는 경우 기본값 1.0)
            recipe_category = getattr(recipe, 'category', '기타')
            taste_weight = favorite_categories.get(recipe_category, 1.0)

            # 최종 하이브리드 점수 산출 (선형 결합: 코사인 40% + 매칭비율 40% + 취향가중치 20%)
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

        # 8. 최종 랭킹 정렬 후 상위 Top-N 반환
        recommendation_list.sort(key=lambda x: x['total_score'], reverse=True)
        top_recommendations = recommendation_list[:10] # 상위 10개

        if not top_recommendations:
            return Response({"message": "조건에 맞는 추천 레시피를 찾지 못했습니다."}, status=status.HTTP_404_NOT_FOUND)

        # 9. 1위 레시피를 대표로 DB 스냅샷 저장 (로그인 유저용)
        best_item = top_recommendations[0]
        user_instance = request.user if request.user.is_authenticated else None
        
        recommendation = RecipeRecommendation.objects.create(
            user=user_instance,
            recipe=best_item['recipe'],
            available_ingredients=raw_ingredients,
            recommendation_type='hybrid_cosine_openai'
        )

        # 10. 프론트엔드 응답 반환
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
            "status": "success",
            "message": "OpenAI 표준화 및 하이브리드 코사인 유사도 추천이 완료되었습니다."
        }, status=status.HTTP_200_OK)