from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.urls import reverse
from django_extensions.db.fields import AutoSlugField
import uuid
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


class CustomUserManager(BaseUserManager):
    def _create_user(self, email, phone, password, **extra_fields):
        if not (email or phone):
            raise ValueError(_("Either email or phone number must be provided"))

        email = self.normalize_email(email) if email else None
        user = self.model(email=email, phone=phone, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email=None, phone=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, phone, password, **extra_fields)

    def create_superuser(
        self, email=None, phone=None, password=None, **extra_fields
    ):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError(_("Superuser must have is_staff=True."))
        if extra_fields.get("is_superuser") is not True:
            raise ValueError(_("Superuser must have is_superuser=True."))

        return self._create_user(email, phone, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(
        _("email address"),
        unique=True,
        null=True,
        blank=True,
        error_messages={
            "unique": _("A user with that email already exists."),
        },
    )
    phone = models.CharField(
        _("phone number"),
        max_length=15,
        unique=True,
        null=True,
        blank=True,
        error_messages={
            "unique": _("A user with that phone number already exists."),
        },
    )
    first_name = models.CharField(_("first name"), max_length=50, blank=True)
    last_name = models.CharField(_("last name"), max_length=50, blank=True)
    is_active = models.BooleanField(_("active"), default=True)
    is_staff = models.BooleanField(_("staff status"), default=False)
    date_joined = models.DateTimeField(_("date joined"), auto_now_add=True)
    phone_verified = models.BooleanField(default=False)

    objects = CustomUserManager()

    USERNAME_FIELD = "email"  
    EMAIL_FIELD = "email"
    PHONE_FIELD = "phone_number"

    class Meta:
        verbose_name = _("user")
        verbose_name_plural = _("users")

    def clean(self):
        super().clean()
        if not self.email and not self.phone:
            raise ValidationError(_("Either email or phone number must be provided."))

    def __str__(self):
        if self.email:
            return self.email
        elif self.phone:
            return self.phone
        return str(self.id)

    def get_full_name(self):
        full_name = "%s %s" % (self.first_name, self.last_name)
        return full_name.strip()

    def get_short_name(self):
        return self.first_name

    def get_username(self):
        return self.email or self.phone


class WeddingPlanner(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField("User", on_delete=models.CASCADE)
    company_name = models.CharField(max_length=100)
    slug = AutoSlugField(max_length=100, populate_from="company_name", unique=True)
    phone = models.CharField(max_length=15)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.company_name} - {self.user.get_full_name() or self.user}"


class WeddingEvent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    planner = models.ForeignKey(
        WeddingPlanner, on_delete=models.CASCADE, related_name="events"
    )
    title = models.CharField(max_length=255)
    couple = models.CharField(max_length=255, blank=True, null=True)
    date = models.DateTimeField()
    venue = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.title} at {self.venue}"


class Invitation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey(
        WeddingEvent, on_delete=models.CASCADE, related_name="invitations"
    )
    card_image = models.ImageField(upload_to="invitation_cards/", blank=True, null=True)
    qr_code = models.ImageField(upload_to="qr_codes/", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Invitation {self.id} for {self.event.title}"


    def get_absolute_url(self):
        return reverse("verify_invitation", args=[str(self.id)])


class Guest(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invitation = models.ForeignKey(
        Invitation, on_delete=models.CASCADE, related_name="guests"
    )
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=15, blank=True)
    is_attending = models.BooleanField(default=False)
    checked_in = models.BooleanField(default=False)
    check_in_time = models.DateTimeField(null=True, blank=True)

    card_image = models.ImageField(upload_to="guest_cards/", blank=True, null=True)

    class Meta:
        unique_together = ["invitation", "email"]

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class QRVerification(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invitation = models.ForeignKey(
        Invitation, on_delete=models.CASCADE, related_name="verifications"
    )
    scanned_at = models.DateTimeField(auto_now_add=True)
    is_valid = models.BooleanField(default=False)
    scanned_by = models.ForeignKey("User", on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"Verification for {self.invitation.id} at {self.scanned_at}"
