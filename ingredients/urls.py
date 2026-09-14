from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import IngredientViewSet, UserRefrigeratorViewSet

router = DefaultRouter()
router.register(r"ingredients", IngredientViewSet, basename="ingredients")
router.register(r"user-refrigerators", UserRefrigeratorViewSet, basename="user-refrigerators")

urlpatterns = [
    path("", include(router.urls)),
]