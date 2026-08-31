import requests
from .models import Recipe

def fetch_and_save_public_recipes():
    # 식약처 조리식품 레시피 오픈 API 주소 (샘플 인증키인 'sample'을 사용해 테스트)
    # 실제 발급받은 인증키가 있다면 'sample' 자리에 팀원분의 인증키를 넣기
    api_key = "sample" 
    url = f"http://openapi.foodsafetykorea.go.kr/api/{api_key}/COOKRCP01/json/1/50" # 우선 50개만 테스트

    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            # 식약처 API 특유의 데이터 감싸기 구조 파싱
            rows = data.get('COOKRCP01', {}).get('row', [])
            
            saved_count = 0
            for row in rows:
                # DB에 이미 같은 제목의 레시피가 있으면 넘어가고, 없으면 새로 만듭니다.
                recipe, created = Recipe.objects.get_or_create(
                    title=row.get('RCP_NM'), # 레시피 이름
                    defaults={
                        'difficulty': 1,      # 식약처에 난이도가 없으므로 기본값 1
                        'cooking_time': 20,   # 조리시간 기본값 20분
                        'calories': float(row.get('INFO_ENG', 0) or 0), # 열량
                        'protein': float(row.get('INFO_PRT', 0) or 0),  # 단백질
                        'carbs': float(row.get('INFO_CAR', 0) or 0),    # 탄수화물
                        'fat': float(row.get('INFO_FAT', 0) or 0),      # 지방
                        # 중요: 식약처의 통짜 재료 텍스트를 ingredient_lines에 저장합니다.
                        'ingredient_lines': row.get('RCP_PARTS_DTLS', '') 
                    }
                )
                if created:
                    saved_count += 1
            
            print(f"성공적으로 {saved_count}개의 새로운 레시피를 식약처에서 가져와 저장했습니다!")
        else:
            print(f"API 호출 실패 (상태 코드: {response.status_code})")
            
    except Exception as e:
        print(f"데이터 수집 중 오류 발생: {e}")