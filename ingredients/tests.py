from contextlib import nullcontext
from types import SimpleNamespace
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase, override_settings
from rest_framework.test import APIRequestFactory, force_authenticate

from .serializers import IngredientValidationSerializer
from .services import (
    IngredientNormalizationError,
    _get_image_format,
    normalize_ingredient_names,
    parse_receipt_text,
)
from .views import IngredientViewSet


class IngredientValidationSerializerTests(SimpleTestCase):
    def test_accepts_ingredient_name_and_quantity(self):
        serializer = IngredientValidationSerializer(data={
            "user_confirmed_ingredients": [
                {
                    "ingredient_name": "깐파",
                    "quantity": 2,
                },
                {
                    "ingredient_name": "계란 1판",
                    "quantity": 1,
                    "unit": "판",
                },
            ]
        })

        self.assertTrue(serializer.is_valid())

        confirmed_items = serializer.validated_data[
            "user_confirmed_ingredients"
        ]

        self.assertEqual(confirmed_items[0]["ingredient_name"], "깐파")
        self.assertEqual(confirmed_items[0]["quantity"], 2)
        self.assertEqual(confirmed_items[0]["unit"], "개")
        self.assertEqual(confirmed_items[1]["unit"], "판")

    def test_rejects_empty_ingredient_list(self):
        serializer = IngredientValidationSerializer(data={
            "user_confirmed_ingredients": []
        })

        self.assertFalse(serializer.is_valid())
        self.assertIn("user_confirmed_ingredients", serializer.errors)

    def test_rejects_zero_quantity(self):
        serializer = IngredientValidationSerializer(data={
            "user_confirmed_ingredients": [
                {
                    "ingredient_name": "우유",
                    "quantity": 0,
                }
            ]
        })

        self.assertFalse(serializer.is_valid())
        self.assertIn("user_confirmed_ingredients", serializer.errors)


class ReceiptServiceTests(SimpleTestCase):
    def test_parses_purchase_date_and_ingredients(self):
        receipt_data = parse_receipt_text([
            "2026/09/04 10:30",
            "상품명 단가 수량 금액",
            "01 우유 1L 3,000 2 6,000",
            "02 달걀 10구 4,500 1 4,500",
        ])

        self.assertEqual(receipt_data["purchase_date"], "2026-09-04")
        self.assertEqual(len(receipt_data["results"]), 2)
        self.assertEqual(
            receipt_data["results"][0]["ingredient_name"],
            "우유 1L",
        )
        self.assertEqual(receipt_data["results"][0]["quantity"], 2)

    def test_converts_jfif_format_to_jpg(self):
        image = SimpleUploadedFile(
            "receipt.jfif",
            b"test-image",
            content_type="image/jpeg",
        )

        self.assertEqual(_get_image_format(image), "jpg")

    @override_settings(OPENAI_API_KEY="")
    def test_normalization_requires_api_key(self):
        with self.assertRaises(IngredientNormalizationError):
            normalize_ingredient_names(["깐파"])


class IngredientValidationViewTests(SimpleTestCase):
    def test_saves_normalized_ingredient_with_quantity(self):
        request = APIRequestFactory().post(
            "/api/v1/ingredients/validate/",
            {
                "user_confirmed_ingredients": [
                    {
                        "ingredient_name": "우유 1L",
                        "quantity": 2,
                    }
                ]
            },
            format="json",
        )

        force_authenticate(
            request,
            user=SimpleNamespace(
                pk=7,
                is_authenticated=True,
            ),
        )

        ingredient = SimpleNamespace(name="우유")

        with (
            patch(
                "ingredients.views.normalize_ingredient_names",
                return_value=["우유"],
            ) as normalize_mock,
            patch(
                "ingredients.views.Ingredients.objects.filter"
            ) as ingredient_filter_mock,
            patch(
                "ingredients.views.Ingredients.objects.create",
                return_value=ingredient,
            ) as ingredient_create_mock,
            patch(
                "ingredients.views.UserRefrigerators.objects.create"
            ) as refrigerator_create_mock,
            patch(
                "ingredients.views.transaction.atomic",
                return_value=nullcontext(),
            ),
        ):
            ingredient_filter_mock.return_value.first.return_value = None

            view = IngredientViewSet.as_view({
                "post": "validate_ingredients"
            })
            response = view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data["data"]["saved_ingredients"],
            ["우유"],
        )

        normalize_mock.assert_called_once_with(["우유 1L"])

        ingredient_create_mock.assert_called_once_with(
            name="우유",
            category=None,
            unit="개",
            amount=0,
        )

        refrigerator_create_mock.assert_called_once_with(
            user_id=7,
            ingredient=ingredient,
            quantity=2,
            expired_at=None,
            storage_type=None,
        )