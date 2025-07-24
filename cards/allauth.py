# cards/allauth.py
import typing
from django.contrib import messages
from allauth.account.adapter import DefaultAccountAdapter
from django.utils.text import slugify
import uuid
from cards.models import User


class AccountAdapter(DefaultAccountAdapter):
    def generate_unique_username(self, txts, regex=None):
        email = txts[0] if txts else None
        phone = txts[1] if len(txts) > 1 else None

    def set_phone(self, user, phone: str, verified: bool = True):
        user.phone = phone
        user.phone_verified = verified
        user.save(update_fields=["phone"])

    def get_phone(self, user) -> typing.Optional[typing.Tuple[str, bool]]:
        if user.phone:
            return user.phone, user.phone_verified
        return None

    def set_phone_verified(self, user, phone):
        self.set_phone(user, phone, True)

    def send_verification_code_sms(self, user, phone: str, code: str, **kwargs):
        messages.add_message(
            self.request,
            messages.WARNING,
            f"⚠️ SMS demo stub: assume code {code} was sent to {phone}.",
        )

    def send_unknown_account_sms(self, phone: str, **kwargs):
        messages.add_message(
            self.request,
            messages.WARNING,
            f"⚠️ SMS demo stub: Enumeration prevention: texted {phone} informing no account exists.",
        )

    def send_account_already_exists_sms(self, phone: str, **kwargs):
        messages.add_message(
            self.request,
            messages.WARNING,
            f"⚠️ SMS demo stub: Enumeration prevention: texted {phone} informing account already exists.",
        )

    def get_user_by_phone(self, phone):
        return User.objects.filter(phone=phone).order_by("-phone_verified").first()

    def save_user(self, request, user, form, commit=True):
        user = super().save_user(request, user, form, commit=False)
        user.email = form.cleaned_data.get("email", "")
        user.phone = form.cleaned_data.get("phone", "")
        user.first_name = form.cleaned_data.get("first_name", "")
        user.last_name = form.cleaned_data.get("last_name", "")
        user.phone_verified = True
        if commit:
            user.save()
        return user
