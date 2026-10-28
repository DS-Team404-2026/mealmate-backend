
from pathlib import Path

import cv2
import numpy as np
from ultralytics import YOLO


AI_DIR = Path(__file__).resolve().parent
MODEL_PATH = AI_DIR / "best.pt"

# 새 Smart Fridge YOLO 모델의 클래스명과 정확히 일치해야 함
DISPLAY_NAMES = {
    "apple": "사과",
    "banana": "바나나",
    "blue berry": "블루베리",
    "bread": "빵",
    "brinjal": "가지",
    "butter": "버터",
    "cabbage": "양배추",
    "capsicum": "파프리카",
    "carrot": "당근",
    "cheese": "치즈",
    "chicken": "닭고기",
    "chocolate": "초콜릿",
    "corn": "옥수수",
    "cucumber": "오이",
    "egg": "계란",
    "flour": "밀가루",
    "fresh cream": "생크림",
    "ginger": "생강",
    "green beans": "그린빈",
    "green chilly": "풋고추",
    "green leaves": "잎채소",
    "lemon": "레몬",
    "meat": "고기",
    "milk": "우유",
    "mushroom": "버섯",
    "potato": "감자",
    "shrimp": "새우",
    "stawberry": "딸기",  # 모델 원본의 오타 유지
    "sweet potato": "고구마",
    "tomato": "토마토",
}


class IngredientDetector:
    def __init__(
        self,
        confidence=0.50,
        image_size=640,
        crop_count=4,
        overlap_ratio=0.04,
    ):
        if not MODEL_PATH.exists():
            raise FileNotFoundError(
                f"YOLO 모델 파일을 찾을 수 없습니다: {MODEL_PATH}"
            )

        self.confidence = confidence
        self.image_size = image_size
        self.crop_count = crop_count
        self.overlap_ratio = overlap_ratio

        self.model = YOLO(str(MODEL_PATH))

    def _load_image(self, image):
        """
        파일 경로, OpenCV ndarray, PIL Image 지원.
        반환값은 OpenCV BGR ndarray.
        """
        if isinstance(image, (str, Path)):
            path = Path(image)

            if not path.is_file():
                raise FileNotFoundError(
                    f"이미지 파일이 없습니다: {path}"
                )

            # Windows 한글 경로도 읽을 수 있도록 처리
            raw = np.fromfile(str(path), dtype=np.uint8)
            loaded = cv2.imdecode(raw, cv2.IMREAD_COLOR)

            if loaded is None:
                raise ValueError("이미지 파일을 읽을 수 없습니다.")

            return loaded

        if isinstance(image, np.ndarray):
            if image.ndim == 2:
                return cv2.cvtColor(
                    image, cv2.COLOR_GRAY2BGR
                )

            if image.ndim != 3:
                raise ValueError("지원하지 않는 이미지 배열입니다.")

            if image.shape[2] == 4:
                return cv2.cvtColor(
                    image, cv2.COLOR_BGRA2BGR
                )

            if image.shape[2] != 3:
                raise ValueError("이미지 채널 수가 올바르지 않습니다.")

            return image

        # PIL Image 지원
        if hasattr(image, "convert"):
            rgb = np.asarray(image.convert("RGB"))
            return cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)

        raise TypeError(
            "이미지는 파일 경로, numpy 배열 또는 PIL Image여야 합니다."
        )

    def _make_regions(self, image):
        """
        세로로 긴 사진은 겹치는 4개 영역으로 분할.
        가로 사진이나 정사각형 사진은 전체 이미지 탐지.

        각 항목: (crop, offset_x, offset_y)
        """
        height, width = image.shape[:2]

        if height <= width or self.crop_count <= 1:
            return [(image, 0, 0)]

        regions = []
        margin = int(height * self.overlap_ratio)

        for i in range(self.crop_count):
            top = height * i // self.crop_count
            bottom = height * (i + 1) // self.crop_count

            top = max(0, top - margin)
            bottom = min(height, bottom + margin)

            crop = image[top:bottom, 0:width]

            if crop.size > 0:
                regions.append((crop, 0, top))

        return regions

    def predict(self, image):
        """
        이미지에서 식재료 탐지.

        반환 형식:
        [
            {
                "label": "tomato",
                "display_name": "토마토",
                "confidence": 0.85,
                "bbox": {
                    "x1": 10.0,
                    "y1": 20.0,
                    "x2": 100.0,
                    "y2": 120.0
                }
            }
        ]

        같은 클래스가 여러 번 탐지되면
        confidence가 가장 높은 결과 하나만 반환.
        bbox 좌표는 원본 이미지 기준.
        """
        original = self._load_image(image)
        height, width = original.shape[:2]

        regions = self._make_regions(original)
        detected = {}

        for crop, offset_x, offset_y in regions:
            results = self.model.predict(
                source=crop,
                conf=self.confidence,
                iou=0.5,
                imgsz=self.image_size,
                verbose=False,
            )

            for result in results:
                for box in result.boxes:
                    class_id = int(box.cls[0].item())
                    score = float(box.conf[0].item())
                    label = str(self.model.names[class_id])

                    coords = (
                        box.xyxy[0]
                        .cpu()
                        .tolist()
                    )

                    # 분할 이미지 좌표 → 원본 이미지 좌표
                    x1 = max(
                        0.0, min(width, coords[0] + offset_x)
                    )
                    y1 = max(
                        0.0, min(height, coords[1] + offset_y)
                    )
                    x2 = max(
                        0.0, min(width, coords[2] + offset_x)
                    )
                    y2 = max(
                        0.0, min(height, coords[3] + offset_y)
                    )

                    detection = {
                        "label": label,
                        "display_name": DISPLAY_NAMES.get(
                            label, label
                        ),
                        "confidence": round(score, 4),
                        "bbox": {
                            "x1": round(x1, 2),
                            "y1": round(y1, 2),
                            "x2": round(x2, 2),
                            "y2": round(y2, 2),
                        },
                    }

                    # 기존 API 동작 유지:
                    # 클래스별 가장 높은 신뢰도 하나만 반환
                    if (
                        label not in detected
                        or score > detected[label]["confidence"]
                    ):
                        detected[label] = detection

        return sorted(
            detected.values(),
            key=lambda item: item["confidence"],
            reverse=True,
        )


_detector = None


def get_detector():
    """
    모델을 최초 요청에서 한 번만 로드하고 재사용.
    """
    global _detector

    if _detector is None:
        _detector = IngredientDetector()

    return _detector
