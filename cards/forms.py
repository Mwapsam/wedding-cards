import re
from allauth.account.forms import SignupForm
from allauth.account.forms import LoginForm
from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Guest, User, WeddingEvent, EventSchedule
from phonenumbers import parse, is_valid_number
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.contrib.auth import authenticate


def validate_phone_number(value):
    if value:
        try:
            parsed = parse(value, None)
            if not is_valid_number(parsed):
                raise ValidationError(_("Invalid phone number format."))
        except Exception:
            raise ValidationError(_("Invalid phone number format."))


class CustomSignupForm(SignupForm):
    email = forms.EmailField(
        label=_("Email"),
        required=False,
        widget=forms.EmailInput(attrs={"placeholder": "Enter your email"}),
    )
    phone = forms.CharField(
        label=_("Phone Number"),
        max_length=15,
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "Enter your phone number"}),
    )
    first_name = forms.CharField(
        label=_("First Name"),
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "Enter your first name"}),
    )
    last_name = forms.CharField(
        label=_("Last Name"),
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "Enter your last name"}),
    )

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get("email")
        phone = cleaned_data.get("phone")

        if not (email or phone):
            raise forms.ValidationError(
                _("Either email or phone number must be provided.")
            )

        # Check for unique email
        if email and User.objects.filter(email=email).exists():
            raise forms.ValidationError(_("A user with that email already exists."))

        # Check for unique phone
        if phone and User.objects.filter(phone=phone).exists():
            raise forms.ValidationError(
                _("A user with that phone number already exists.")
            )

        return cleaned_data

    def save(self, request):
        user = super().save(request)
        user.email = self.cleaned_data.get("email")
        user.phone_verified = True
        user.phone = self.cleaned_data.get("phone")
        user.first_name = self.cleaned_data.get("first_name")
        user.last_name = self.cleaned_data.get("last_name")
        user.save()
        return user


class CustomLoginForm(LoginForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["login"].label = "Email or Phone"
        self.fields["login"].help_text = "Enter your email address or phone number."

    def clean_login(self):
        login = self.cleaned_data["login"]
        # Check if the input is an email or phone and validate accordingly
        if "@" in login:
            # Handle as email
            if not User.objects.filter(email=login).exists():
                raise forms.ValidationError("No user found with this email.")
        else:
            # Handle as phone
            if not User.objects.filter(phone=login).exists():
                raise forms.ValidationError("No user found with this phone number.")
        return login


class GuestForm(forms.ModelForm):
    class Meta:
        model = Guest
        fields = ["guest_name", "first_name", "last_name", "email", "phone", "payment_amount"]
        widgets = {
            "guest_name": forms.TextInput(
                attrs={"placeholder": "Enter full guest name (optional)"}
            ),
            "first_name": forms.TextInput(
                attrs={"placeholder": "Enter guest first name"}
            ),
            "last_name": forms.TextInput(
                attrs={"placeholder": "Enter guest last name"}
            ),
            "email": forms.EmailInput(attrs={"placeholder": "Enter guest email"}),
            "phone": forms.TextInput(attrs={"placeholder": "Enter guest phone number"}),
            "payment_amount": forms.NumberInput(
                attrs={"placeholder": "Enter registration fee (optional)", "step": "0.01"}
            ),
        }
        help_texts = {
            "guest_name": _("Use this if you prefer a single name field instead of first/last name."),
            "payment_amount": _("Registration or entry fee for this guest (if applicable)."),
        }

    def __init__(self, *args, **kwargs):
        self.invitation = kwargs.pop("invitation", None)
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get("email")
        if (
            email
            and self.invitation
            and Guest.objects.filter(invitation=self.invitation, email=email).exists()
        ):
            raise forms.ValidationError(
                _("A guest with this email already exists for this invitation.")
            )


class WeddingEventForm(forms.ModelForm):
    class Meta:
        model = WeddingEvent
        fields = ["title", "date", "venue", "description", "couple"]
        widgets = {
            "title": forms.TextInput(attrs={"placeholder": "Enter event title"}),
            "date": forms.DateTimeInput(
                attrs={
                    "type": "datetime-local",
                    "placeholder": "Select event date and time",
                }
            ),
            "venue": forms.TextInput(attrs={"placeholder": "Enter venue name"}),
            "description": forms.Textarea(
                attrs={"placeholder": "Enter event description", "rows": 4}
            ),
        }
        help_texts = {
            "title": _("The name of your wedding event."),
            "date": _("Choose a future date and time for the event."),
            "venue": _("Location where the event will be held."),
            "description": _("Add any important details about the event."),
            "couple": _("Select the couple associated with this event."),
        }

    def clean_date(self):
        date = self.cleaned_data.get("date")
        if date and date < timezone.now():
            raise forms.ValidationError(_("Event date must be in the future."))
        return date


class EventScheduleForm(forms.ModelForm):
    class Meta:
        model = EventSchedule
        fields = ["event_name", "date", "location", "description", "order"]
        widgets = {
            "event_name": forms.TextInput(
                attrs={"placeholder": "e.g., Ceremony, Reception, After Party"}
            ),
            "date": forms.DateTimeInput(
                attrs={
                    "type": "datetime-local",
                    "placeholder": "Select date and time",
                }
            ),
            "location": forms.TextInput(
                attrs={"placeholder": "Enter location/venue"}
            ),
            "description": forms.Textarea(
                attrs={"placeholder": "Additional details (optional)", "rows": 3}
            ),
            "order": forms.NumberInput(
                attrs={"placeholder": "Event order (1, 2, 3...)", "min": "1"}
            ),
        }
        help_texts = {
            "event_name": _("Name of this specific event (e.g., 'Ceremony', 'Reception')."),
            "date": _("Date and time for this specific event."),
            "location": _("Where this specific event will take place."),
            "order": _("Order in which events will occur (1 = first event)."),
        }

    def clean_date(self):
        date = self.cleaned_data.get("date")
        if date and date < timezone.now():
            raise forms.ValidationError(_("Event date must be in the future."))
        return date
