from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from rest_framework.authtoken.models import Token

User = get_user_model()


class CustomAuthTokenSerializer(serializers.Serializer):
    email = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    phone = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    password = serializers.CharField(write_only=True, required=True)

    def validate(self, data):
        email = data.get("email", "").strip()
        phone = data.get("phone", "").strip()
        password = data.get("password")

        if not email and not phone:
            raise serializers.ValidationError(
                {
                    "field_errors": {
                        "email": [_("Either email or phone number must be provided.")],
                        "phone": [_("Either email or phone number must be provided.")],
                    }
                }
            )

        user = None
        if email:
            user = User.objects.filter(email=email).first()
        elif phone:
            user = User.objects.filter(phone=phone).first()

        if user and user.check_password(password):
            if not user.is_active:
                raise serializers.ValidationError(
                    {"non_field_errors": [_("User account is disabled.")]}
                )
            token, created = Token.objects.get_or_create(user=user)
            return {"user": user, "token": token.key}
        raise serializers.ValidationError(
            {"non_field_errors": [_("Invalid credentials.")]}
        )
