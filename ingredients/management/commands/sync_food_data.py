import time

import requests
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from ingredients.models import Ingredients
from ingredients.services import RAW_MATERIAL_URL


class Command(BaseCommand):
    help = "식약처 원재료 목록을 ingredients 테이블에 중복 없이 적재합니다."

    def add_arguments(self, parser):
        parser.add_argument("--pages", type=int, default=1, help="조회할 최대 페이지 수 (기본 1)")
        parser.add_argument("--page-size", type=int, default=100, help="페이지당 요청 건수 (기본 100)")
        parser.add_argument("--start-page", type=int, default=1, help="시작 페이지 (기본 1)")
        parser.add_argument("--delay", type=float, default=0.2, help="요청 사이 대기 초 (기본 0.2)")
        parser.add_argument("--commit", action="store_true", help="실제 DB에 저장 (미지정 시 미리보기)")

    def handle(self, *args, **options):
        pages = options["pages"]
        page_size = options["page_size"]
        start_page = options["start_page"]
        delay = options["delay"]
        commit = options["commit"]
        if pages < 1 or page_size < 1 or start_page < 1 or delay < 0:
            raise CommandError("pages, page-size, start-page는 양수, delay는 0 이상이어야 합니다.")
        if not getattr(settings, "PUBLIC_DATA_API_KEY", None):
            raise CommandError("settings.PUBLIC_DATA_API_KEY가 설정되지 않았습니다.")

        session = requests.Session()
        seen = set(Ingredients.objects.exclude(name__isnull=True).values_list("name", flat=True))
        created = duplicates = invalid = 0
        for page in range(start_page, start_page + pages):
            params = {
                "serviceKey": settings.PUBLIC_DATA_API_KEY,
                "pageNo": page,
                "numOfRows": page_size,
                "type": "json",
            }
            try:
                response = session.get(RAW_MATERIAL_URL, params=params, timeout=20)
                response.raise_for_status()
                payload = response.json()
            except (requests.RequestException, ValueError) as exc:
                raise CommandError(f"페이지 {page} API 요청 실패: {exc}") from exc

            root = payload.get("response", payload)
            header = root.get("header", {}) if isinstance(root, dict) else {}
            result_code = str(header.get("resultCode", "00"))
            if result_code not in {"00", "0", "NORMAL_SERVICE"}:
                raise CommandError(f"페이지 {page} API 오류: {header}")
            body = root.get("body", {}) if isinstance(root, dict) else {}
            items = body.get("items", []) if isinstance(body, dict) else []
            if isinstance(items, dict):
                items = items.get("item", [])
            if not isinstance(items, list):
                raise CommandError(f"페이지 {page}: 예상하지 못한 items 구조: {type(items).__name__}")
            if not items:
                self.stdout.write(f"페이지 {page}: 결과 없음, 종료")
                break

            page_created = 0
            for item in items:
                if not isinstance(item, dict):
                    invalid += 1
                    continue
                name = " ".join(str(item.get("RPRSNT_RAWMTRL_NM") or "").split())
                category = " ".join(str(item.get("LCLAS_NM") or "").split())
                if not name or len(name) > 20:
                    invalid += 1
                    continue
                if name in seen:
                    duplicates += 1
                    continue
                seen.add(name)
                if commit:
                    Ingredients.objects.create(name=name, category=category[:20] or None)
                created += 1
                page_created += 1
            self.stdout.write(f"페이지 {page}: {len(items)}건 수신, 신규 {page_created}건")
            if len(items) < page_size:
                break
            if page < start_page + pages - 1 and delay:
                time.sleep(delay)

        mode = "저장 완료" if commit else "미리보기 (DB 변경 없음)"
        self.stdout.write(self.style.SUCCESS(
            f"{mode}: 신규 {created}건, 중복 {duplicates}건, 이름 누락/길이 초과 {invalid}건"
        ))
