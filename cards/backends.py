from allauth.account.auth_backends import AuthenticationBackend
from django.contrib.auth import get_user_model

User = get_user_model()


class EmailOrPhoneBackend(AuthenticationBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        login = username or kwargs.get("login")
        user = None

        if login:
            try:
                if "@" in login:
                    user = User.objects.get(email__iexact=login)
                else:
                    user = User.objects.get(phone=login)
            except User.DoesNotExist:
                return None

            if user.check_password(password) and self.user_can_authenticate(user):
                return user

        return None
