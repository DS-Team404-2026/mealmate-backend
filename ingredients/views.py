from datetime import date, timedelta

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Ingredients, UserRefrigerators, Users
from .serializers import IngredientSerializer, UserRefrigeratorSerializer
from .services import search_raw_material


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