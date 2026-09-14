from datetime import date
from rest_framework import serializers

from .models import Ingredients, UserRefrigerators

class ReceiptImageSerializer(serializers.Serializer):
    image = serializers.ImageField()


class ConfirmedIngredientSerializer(serializers.Serializer):
    ingredient_name = serializers.CharField(
        max_length=50,
        allow_blank=False,
        trim_whitespace=True,
    )
    quantity = serializers.IntegerField(min_value=1)
    unit = serializers.CharField(
        max_length=20,
        required=False,
        default="개",
    )


class IngredientValidationSerializer(serializers.Serializer):
    user_confirmed_ingredients = ConfirmedIngredientSerializer(
        many=True,
        allow_empty=False,
    )


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredients
        fields = ["id", "name", "category", "unit", "amount"]


class UserRefrigeratorSerializer(serializers.ModelSerializer):
    ingredient_name = serializers.CharField(source="ingredient.name", read_only=True)
    ingredient_category = serializers.CharField(source="ingredient.category", read_only=True)
    ingredient_unit = serializers.CharField(source="ingredient.unit", read_only=True)

    class Meta:
        model = UserRefrigerators
        fields = [
            "id",
            "quantity",
            "expired_at",
            "storage_type",
            "user",
            "ingredient",
            "ingredient_name",
            "ingredient_category",
            "ingredient_unit",
        ]

    def validate_quantity(self, value):
        if value is not None and value <= 0:
            raise serializers.ValidationError("수량은 0보다 커야 합니다.")
        return value

    def validate_expired_at(self, value):
        if value and value < date.today():
            raise serializers.ValidationError("유통기한은 오늘 이전 날짜로 등록할 수 없습니다.")
        return value