from rest_framework import serializers

class CustomAuthTokenSerializer(serializers.Serializer):
    email = serializers.CharField(required=False, allow_null=True)
    phone = serializers.CharField(required=False, allow_null=True)
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        email = data.get("email")
        phone = data.get("phone")
        password = data.get("password")

        if not (email or phone):
            raise serializers.ValidationError(
                _("Either email or phone number must be provided.")
            )

        user = None
        if email:
            user = User.objects.filter(email=email).first()
        elif phone:
            user = User.objects.filter(phone=phone).first()

        if user and user.check_password(password):
            if not user.is_active:
                raise serializers.ValidationError(_("User account is disabled."))
            return {"user": user}
        raise serializers.ValidationError(_("Invalid credentials."))
