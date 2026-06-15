import requests
from django.conf import settings


RAW_MATERIAL_URL = (
    "https://apis.data.go.kr/1471000/"
    "FoodRwmatrInfoService01/getFoodRwmatrList01"
)


def search_raw_material(keyword):
    params = {
        "serviceKey": settings.PUBLIC_DATA_API_KEY,
        "pageNo": 1,
        "numOfRows": 100,
        "type": "json",
        "rprsnt_rawmtrl_nm": keyword,
    }

    response = requests.get(RAW_MATERIAL_URL, params=params, timeout=10)

    if response.status_code != 200:
        return {
            "success": False,
            "message": "식품 원재료 API 호출 실패",
            "status_code": response.status_code,
            "raw": response.text[:500],
        }

    data = response.json()

    items = (
        data.get("body", {}).get("items", [])
        or data.get("response", {}).get("body", {}).get("items", [])
        or []
    )

    results = []

    for item in items:
        name = item.get("RPRSNT_RAWMTRL_NM")
        category = item.get("LCLAS_NM") or "기타"
        sub_category = item.get("MLSFC_NM")
        nickname = item.get("RAWMTRL_NCKNM")
        english_name = item.get("ENG_NM")
        part_name = item.get("REGN_CD_NM")
        use_condition = item.get("USE_CND_NM")

        if not name:
            continue

        # 검색어랑 관련 없는 원재료 제외
        if keyword not in name:
            continue

        results.append({
            "name": name,
            "category": category,
            "sub_category": sub_category,
            "nickname": nickname,
            "english_name": english_name,
            "part_name": part_name,
            "use_condition": use_condition,
        })

    return {
        "success": True,
        "keyword": keyword,
        "count": len(results),
        "results": results,
    }