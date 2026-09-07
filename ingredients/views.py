from datetime import date, timedelta

from django.db import DatabaseError, transaction
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication

from .models import Ingredients, UserRefrigerators, Users
from .serializers import IngredientSerializer, IngredientValidationSerializer, ReceiptImageSerializer, UserRefrigeratorSerializer
from .services import ClovaOCRError, IngredientNormalizationError, normalize_ingredient_names, parse_receipt_text, recognize_receipt, search_raw_material


class IngredientViewSet(viewsets.ModelViewSet):
    serializer_class = IngredientSerializer

    def get_queryset(self):
        queryset = Ingredients.objects.all().order_by("id")

        keyword = self.request.query_params.get("keyword")
        category = self.request.query_params.get("category")

        if keyword:
            queryset = queryset.filter(name__icontains=keyword)

        if category:
            queryset = queryset.filter(category=category)

        return queryset

    @action(
        detail=False,
        methods=["post"],
        url_path="receipt-recognize",
        parser_classes=[MultiPartParser],
        authentication_classes=[JWTAuthentication],
        permission_classes=[IsAuthenticated],
    )
    def receipt_recognize(self, request):
        serializer = ReceiptImageSerializer(data=request.data)

        if not serializer.is_valid():
            return Response({
                "success": False,
                "message": "영수증 이미지를 첨부해주세요."
            }, status=status.HTTP_400_BAD_REQUEST)

        image = serializer.validated_data["image"]

        try:
            ocr_text = recognize_receipt(image)
        except ClovaOCRError as error:
            return Response({
                "success": False,
                "message": str(error),
            }, status=status.HTTP_502_BAD_GATEWAY)

        receipt_data = parse_receipt_text(ocr_text)

        return Response({
            "success": True,
            "purchase_date": receipt_data["purchase_date"],
            "results": receipt_data["results"],
        }, status=status.HTTP_200_OK)


    @action(
        detail=False,
        methods=["post"],
        url_path="validate",
        authentication_classes=[JWTAuthentication],
        permission_classes=[IsAuthenticated],
    )
    def validate_ingredients(self, request):
        serializer = IngredientValidationSerializer(data=request.data)

        if not serializer.is_valid():
            return Response({
                "status": "error",
                "message": "확정할 식재료 목록을 올바르게 입력해주세요.",
                "errors": serializer.errors,
            }, status=status.HTTP_400_BAD_REQUEST)

        confirmed_items = serializer.validated_data[
            "user_confirmed_ingredients"
        ]

        ingredient_names = [
            item["ingredient_name"]
            for item in confirmed_items
        ]

        try:
            normalized_names = normalize_ingredient_names(
                ingredient_names
            )
        except IngredientNormalizationError as error:
            return Response({
                "status": "error",
                "message": str(error),
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        try:
            with transaction.atomic():
                saved_ingredients = []

                for item, normalized_name in zip(
                    confirmed_items,
                    normalized_names,
                ):
                    ingredient_name = normalized_name[:20]

                    ingredient = Ingredients.objects.filter(
                        name=ingredient_name
                    ).first()

                    if ingredient is None:
                        ingredient = Ingredients.objects.create(
                            name=ingredient_name,
                            category=None,
                            unit=item["unit"],
                            amount=0,
                        )

                    UserRefrigerators.objects.create(
                        user_id=request.user.pk,
                        ingredient=ingredient,
                        quantity=item["quantity"],
                        expired_at=None,
                        storage_type=None,
                    )

                    saved_ingredients.append(ingredient.name)

        except DatabaseError:
            return Response({
                "status": "error",
                "message": "냉장고 DB 저장에 실패했습니다.",
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        return Response({
            "status": "success",
            "message": (
                "식재료가 표준화되어 냉장고에 "
                "성공적으로 저장되었습니다."
            ),
            "data": {
                "saved_ingredients": saved_ingredients,
                "normalized_count": len(saved_ingredients),
            },
        }, status=status.HTTP_200_OK)


    @action(detail=False, methods=["get"])
    def raw_materials(self, request):
        keyword = request.query_params.get("keyword")

        if not keyword:
            return Response({
                "success": False,
                "message": "keyword가 필요합니다."
            }, status=status.HTTP_400_BAD_REQUEST)

        result = search_raw_material(keyword)
        return Response(result)

    @action(detail=False, methods=["post"])
    def save_raw_material(self, request):
        name = request.data.get("name")
        category = request.data.get("category", "기타")
        unit = request.data.get("unit", "g")

        if not name:
            return Response({
                "success": False,
                "message": "name이 필요합니다."
            }, status=status.HTTP_400_BAD_REQUEST)

        ingredient, created = Ingredients.objects.get_or_create(
            name=name[:20],
            defaults={
                "category": category[:20],
                "unit": unit,
                "amount": 0,
            }
        )

        return Response({
            "success": True,
            "created": created,
            "id": ingredient.id,
            "name": ingredient.name,
            "category": ingredient.category,
            "unit": ingredient.unit,
            "message": "식재료가 저장되었습니다." if created else "이미 존재하는 식재료입니다."
        }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


class UserRefrigeratorViewSet(viewsets.ModelViewSet):
    serializer_class = UserRefrigeratorSerializer

    def get_queryset(self):
        user_id = self.request.query_params.get("user_id", 1)

        queryset = UserRefrigerators.objects.select_related("ingredient").filter(
            user_id=user_id
        ).order_by("expired_at")

        category = self.request.query_params.get("category")
        storage_type = self.request.query_params.get("storage_type")
        expiry_status = self.request.query_params.get("expiry_status")

        if category:
            queryset = queryset.filter(ingredient__category=category)

        if storage_type:
            queryset = queryset.filter(storage_type=storage_type)

        if expiry_status == "expired":
            queryset = queryset.filter(expired_at__lt=date.today())

        if expiry_status == "soon":
            queryset = queryset.filter(
                expired_at__gte=date.today(),
                expired_at__lte=date.today() + timedelta(days=3)
            )

        return queryset

    def perform_create(self, serializer):
        user_id = self.request.data.get("user", 1)
        user = Users.objects.get(id=user_id)
        serializer.save(user=user)

    @action(detail=False, methods=["get"])
    def expiring(self, request):
        user_id = request.query_params.get("user_id", 1)
        days = int(request.query_params.get("days", 3))

        today = date.today()
        target_date = today + timedelta(days=days)

        items = UserRefrigerators.objects.select_related("ingredient").filter(
            user_id=user_id,
            expired_at__gte=today,
            expired_at__lte=target_date,
        ).order_by("expired_at")

        data = []

        for item in items:
            days_left = (item.expired_at - today).days

            data.append({
                "id": item.id,
                "ingredient_id": item.ingredient.id,
                "ingredient_name": item.ingredient.name,
                "category": item.ingredient.category,
                "quantity": item.quantity,
                "unit": item.ingredient.unit,
                "storage_type": item.storage_type,
                "expired_at": item.expired_at,
                "days_left": days_left,
                "message": f"{item.ingredient.name}의 유통기한이 {days_left}일 남았습니다."
            })

        return Response({
            "success": True,
            "count": len(data),
            "results": data,
        })