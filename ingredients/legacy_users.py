"""JWT accounts.User -> legacy users mapping (temporary compatibility layer)."""
from django.db import IntegrityError, transaction
from rest_framework.exceptions import PermissionDenied
from .models import Users


def resolve_legacy_user(auth_user):
    if not getattr(auth_user, "is_authenticated", False):
        raise PermissionDenied("로그인이 필요합니다.")
    email = (auth_user.email or "").strip()
    if not email:
        raise PermissionDenied("로그인 계정에 이메일이 없습니다.")

    # users.email has a UNIQUE index. get_or_create is race-safe with that index.
    # Never copy the authentication password/hash to the legacy table.
    try:
        with transaction.atomic():
            legacy_user, _ = Users.objects.get_or_create(
                email=email,
                defaults={
                    "nickname": (auth_user.nickname or "")[:50],
                    "password": "!legacy-login-disabled",
                },
            )
    except Users.MultipleObjectsReturned:
        raise PermissionDenied("중복된 사용자 이메일을 확인해주세요.")
    return legacy_user
