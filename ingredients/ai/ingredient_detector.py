from pathlib import Path

from ultralytics import YOLO


# 현재 ai 폴더
AI_DIR = Path(__file__).resolve().parent

# 학습된 YOLO 모델
MODEL_PATH = AI_DIR / "best.pt"


# YOLO 클래스명 → 앱에서 사용할 한글 식재료명
DISPLAY_NAMES = {
    "apple": "사과",
    "banana": "바나나",
    "bean": "콩",
    "blueberry": "블루베리",
    "broccoli": "브로콜리",
    "cabbage": "양배추",
    "carrot": "당근",
    "corn": "옥수수",
    "cucumber": "오이",
    "egg": "계란",
    "garlic": "마늘",
    "grape": "포도",
    "kiwi": "키위",
    "lemon": "레몬",
    "lettuce": "상추",
    "lime": "라임",
    "mushroom": "버섯",
    "onion": "양파",
    "orange": "오렌지",
    "pepper": "파프리카",
    "potato": "감자",
    "spinach": "시금치",
    "strawberry": "딸기",
    "sweet potato": "고구마",
    "tomato": "토마토",
}


class IngredientDetector:
    def __init__(self, confidence=0.35):
        """
        YOLO 식재료 탐지 모델 초기화
        """

        if not MODEL_PATH.exists():
            raise FileNotFoundError(
                f"YOLO 모델 파일을 찾을 수 없습니다: {MODEL_PATH}"
            )

        self.confidence = confidence

        # 모델 로드
        self.model = YOLO(str(MODEL_PATH))

    def predict(self, image):
        """
        이미지에서 식재료 탐지

        image:
        - 이미지 파일 경로
        - OpenCV numpy 이미지

        반환:
        [
            {
                "label": "tomato",
                "display_name": "토마토",
                "confidence": 0.85,
                "bbox": {...}
            }
        ]

        같은 식재료가 여러 번 검출되면
        confidence가 가장 높은 결과 하나만 반환
        """

        results = self.model.predict(
            source=image,
            conf=self.confidence,
            iou=0.5,
            verbose=False,
        )

        detected = {}

        for result in results:
            for box in result.boxes:

                # 클래스 ID
                class_id = int(
                    box.cls[0].item()
                )

                # confidence
                confidence = float(
                    box.conf[0].item()
                )

                # 클래스명
                label = self.model.names[
                    class_id
                ]

                # Bounding Box
                coordinates = (
                    box.xyxy[0]
                    .cpu()
                    .tolist()
                )

                bbox = {
                    "x1": round(coordinates[0], 2),
                    "y1": round(coordinates[1], 2),
                    "x2": round(coordinates[2], 2),
                    "y2": round(coordinates[3], 2),
                }

                detection = {
                    "label": label,
                    "display_name": DISPLAY_NAMES.get(
                        label,
                        label,
                    ),
                    "confidence": round(
                        confidence,
                        4,
                    ),
                    "bbox": bbox,
                }

                # 처음 발견한 클래스
                if label not in detected:
                    detected[label] = detection

                # 이미 발견한 클래스라면
                # confidence가 더 높은 것만 저장
                elif (
                    confidence
                    > detected[label]["confidence"]
                ):
                    detected[label] = detection

        # confidence 높은 순으로 정렬
        detections = sorted(
            detected.values(),
            key=lambda item: item["confidence"],
            reverse=True,
        )

        return detections


# 모델을 요청마다 다시 로드하지 않기 위한 변수
_detector = None


def get_detector():
    """
    IngredientDetector 싱글톤 반환

    최초 API 요청에서만 모델을 로드하고
    이후 요청에서는 같은 모델을 재사용
    """

    global _detector

    if _detector is None:
        _detector = IngredientDetector()

    return _detector