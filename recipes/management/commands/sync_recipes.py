import requests
from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import transaction
from recipes.models import Recipe, RecipeStep

class Command(BaseCommand):
    help = "식약처 레시피 기본 정보 및 조리 단계를 DB에 적재합니다."

    def handle(self, *args, **options):
        # 1. 키를 직접 적지 말고, 없으면 빈칸("")을 반환하게 두기!
        api_key = getattr(settings, "FOOD_API_KEY", "")
        
        if not api_key:
            self.stdout.write(self.style.ERROR("API 키가 없습니다! .env와 settings.py를 확인해주세요."))
            return
            
        # 2. 주소 중간에 변수 {api_key}를 넣으면 파이썬이 알아서 키 값을 치환해 줌!
        url = f"http://openapi.foodsafetykorea.go.kr/api/{api_key}/COOKRCP01/json/1/1000"
        
        # ... (이하 아까 작성한 코드 그대로)
        
        self.stdout.write("식약처 API 데이터 불러오는 중...")
        try:
            response = requests.get(url, timeout=20)
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"API 요청 실패: {e}"))
            return

        rows = data.get("COOKRCP01", {}).get("row", [])
        if not rows:
            self.stdout.write(self.style.ERROR("데이터를 불러오지 못했습니다. API 키나 주소를 확인해주세요."))
            return

        recipe_count = 0
        step_count = 0

        # 문자열을 Float로 안전하게 변환하는 헬퍼 함수
        def safe_float(val):
            try:
                return float(val)
            except (ValueError, TypeError):
                return 0.0

        # DB 작업 속도 향상 및 중간에 뻗었을 때 롤백을 위해 transaction 적용
        with transaction.atomic():
            for row in rows:
                # 띄어쓰기 뭉개는 replace(" ","") 절대 안 씀! 양옆 공백만 strip()으로 정리
                title = row.get("RCP_NM", "").strip()
                if not title:
                    continue
                
                # 2. Recipe 테이블 저장 (get_or_create로 중복 적재 방지)
                recipe, created = Recipe.objects.get_or_create(
                    title=title,
                    defaults={
                        # 식약처 API에 난이도/시간이 명확한 int가 아니어서 임의 기본값 세팅 (필요시 수정)
                        "difficulty": 1, 
                        "cooking_time": 30, 
                        "calories": safe_float(row.get("INFO_ENG", 0)),
                        "protein": safe_float(row.get("INFO_PRO", 0)),
                        "carbs": safe_float(row.get("INFO_CAR", 0)),
                        "fat": safe_float(row.get("INFO_FAT", 0)),
                        "ingredient_lines": row.get("RCP_PARTS_DTLS", "")
                    }
                )

                # 3. 새로 생성된 레시피라면 조리 단계(RecipeStep) 파싱해서 넣기
                if created:
                    recipe_count += 1
                    steps_to_create = []
                    
                    for i in range(1, 21):
                        step_key = f"MANUAL{i:02d}"
                        step_text = row.get(step_key, "")

                        if step_text: 
                            steps_to_create.append(
                                RecipeStep(
                                    recipe=recipe,
                                    step_order=i,
                                    description=step_text
                                )
                            )
                    
                    # bulk_create로 조리 단계들을 한 번에 DB에 밀어 넣기 (성능 최적화)
                    if steps_to_create:
                        RecipeStep.objects.bulk_create(steps_to_create)
                        step_count += len(steps_to_create)

        self.stdout.write(self.style.SUCCESS(f"적재 완료! 새 레시피 {recipe_count}개, 조리단계 {step_count}개 추가됨."))