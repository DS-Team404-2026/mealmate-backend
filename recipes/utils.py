import os
import requests
import urllib.parse
from pathlib import Path
from dotenv import load_dotenv
from .models import Recipe

# .env 경로 찾기 및 로드
BASE_DIR = Path(__file__).resolve().parent.parent
env_path = os.path.join(BASE_DIR, '.env')
load_dotenv(dotenv_path=env_path)

def fetch_and_save_public_recipes():
    # 1. 키 불러오기
    raw_api_key = os.environ.get('FOOD_API_KEY') 
    
    if not raw_api_key:
        print("에러: .env 파일에 FOOD_API_KEY가 설정되지 않았습니다!")
        return

    # 2. 키값의 특수문자 안전하게 변환 (url 인코딩)
    safe_api_key = urllib.parse.quote(raw_api_key)
    
    # 3. URL에 변환된 safe_api_key 넣기 (여기가 수정된 부분!)
    url = f"http://openapi.foodsafetykorea.go.kr/api/{safe_api_key}/COOKRCP01/json/1/50" 
    
    try:
        response = requests.get(url)
        
        # 4. JSON 파싱 에러(HTML 반환 등) 상세 확인
        try:
            data = response.json()
        except Exception as e:
            print("🚨 JSON 파싱 에러! 서버가 보낸 원본 메시지:")
            print(response.text[:500])
            return
            
        rows = data.get('COOKRCP01', {}).get('row', [])
        
        # 5. 데이터가 없을 경우
        if not rows:
            print(f"🚨 식약처 서버에서 데이터를 주지 않았습니다. 응답: {data}")
            return
            
        # 6. DB 저장 로직
        saved_count = 0
        for row in rows:
            recipe, created = Recipe.objects.get_or_create(
                title=row.get('RCP_NM'), 
                defaults={
                    'difficulty': 1,      
                    'cooking_time': 20,   
                    'calories': float(row.get('INFO_ENG', 0) or 0), 
                    'protein': float(row.get('INFO_PRT', 0) or 0),  
                    'carbs': float(row.get('INFO_CAR', 0) or 0),    
                    'fat': float(row.get('INFO_FAT', 0) or 0),      
                    'ingredient_lines': row.get('RCP_PARTS_DTLS', '') 
                }
            )
            if created:
                saved_count += 1
        
        print(f"✅ 성공적으로 {saved_count}개의 새로운 레시피를 식약처에서 가져와 저장했습니다!")
        
    except Exception as e:
        print(f"데이터 수집 중 오류 발생: {e}")