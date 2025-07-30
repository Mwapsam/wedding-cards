from rest_framework import serializers, viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth import get_user_model

from cards.serierizers import CustomAuthTokenSerializer
from .models import WeddingPlanner, WeddingEvent, Invitation, Guest, QRVerification
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.utils.translation import gettext_lazy as _

User = get_user_model()


# Serializers
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "phone",
            "first_name",
            "last_name",
            "is_active",
            "is_staff",
            "date_joined",
            "phone_verified",
        ]
        read_only_fields = ["id", "date_joined", "is_staff"]

    def validate(self, data):
        if not data.get("email") and not data.get("phone"):
            raise serializers.ValidationError(
                _("Either email or phone number must be provided.")
            )
        return data


class WeddingPlannerSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    user_id = serializers.UUIDField(write_only=True)

    class Meta:
        model = WeddingPlanner
        fields = [
            "id",
            "user",
            "user_id",
            "company_name",
            "slug",
            "phone",
            "created_at",
        ]
        read_only_fields = ["id", "slug", "created_at"]


class WeddingEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = WeddingEvent
        fields = [
            "id",
            "title",
            "couple",
            "date",
            "venue",
            "description",
            "status",
            "planner",
        ]
        read_only_fields = ["id", "planner"]

    def validate(self, data):
        if not data.get("title"):
            raise serializers.ValidationError(
                {"field_errors": {"title": _("This field may not be blank.")}}
            )
        if not data.get("date"):
            raise serializers.ValidationError(
                {"field_errors": {"date": _("This field may not be blank.")}}
            )
        if not data.get("venue"):
            raise serializers.ValidationError(
                {"field_errors": {"venue": _("This field may not be blank.")}}
            )
        return data


class InvitationSerializer(serializers.ModelSerializer):
    event = WeddingEventSerializer(read_only=True)
    event_id = serializers.UUIDField(write_only=True)

    class Meta:
        model = Invitation
        fields = ["id", "event", "event_id", "created_at"]
        read_only_fields = ["id", "created_at"]


class GuestSerializer(serializers.ModelSerializer):
    invitation = InvitationSerializer(read_only=True)
    invitation_id = serializers.UUIDField(write_only=True)

    class Meta:
        model = Guest
        fields = [
            "id",
            "invitation",
            "invitation_id",
            "first_name",
            "last_name",
            "email",
            "phone",
            "is_attending",
            "checked_in",
            "check_in_time",
            "card_image",
            "qr_code",
            "guest_name",
        ]
        read_only_fields = [
            "id",
            "check_in_time",
            "card_image",
            "qr_code",
            "first_name",
            "last_name",
            "email",
            "phone",
        ]


class QRVerificationSerializer(serializers.ModelSerializer):
    guest = GuestSerializer(read_only=True)
    guest_id = serializers.UUIDField(write_only=True)

    class Meta:
        model = QRVerification
        fields = ["id", "guest", "guest_id", "scanned_at", "is_valid"]
        read_only_fields = ["id", "scanned_at"]


# Viewsets
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.action in ["create"]:
            return [AllowAny()]
        return super().get_permissions()

    @action(detail=False, methods=["post"], permission_classes=[AllowAny])
    def register(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        token, created = Token.objects.get_or_create(user=user)
        return Response(
            {"user": serializer.data, "token": token.key},
            status=status.HTTP_201_CREATED,
        )

    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated])
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)


class WeddingPlannerViewSet(viewsets.ModelViewSet):
    queryset = WeddingPlanner.objects.all()
    serializer_class = WeddingPlannerSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class WeddingEventViewSet(viewsets.ModelViewSet):
    queryset = WeddingEvent.objects.all()
    serializer_class = WeddingEventSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(planner__user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(planner=self.request.user.weddingplanner)

class InvitationViewSet(viewsets.ModelViewSet):
    queryset = Invitation.objects.all()
    serializer_class = InvitationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(event__planner__user=self.request.user)


class GuestViewSet(viewsets.ModelViewSet):
    queryset = Guest.objects.all()
    serializer_class = GuestSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(invitation__event__planner__user=self.request.user)

    def perform_create(self, serializer):
        invitation_id = self.request.data.get("invitation_id")
        invitation = Invitation.objects.filter(
            id=invitation_id, event__planner=self.request.user.weddingplanner
        ).first()
        if not invitation:
            raise serializers.ValidationError(
                {
                    "non_field_errors": [
                        _("Invalid invitation ID or you do not have permission.")
                    ]
                }
            )
        serializer.save(invitation=invitation) 

    def perform_update(self, serializer):
        invitation_id = self.request.data.get("invitation_id")
        invitation = (
            Invitation.objects.filter(
                id=invitation_id, event__planner=self.request.user.weddingplanner
            ).first()
            if invitation_id
            else serializer.instance.invitation
        )
        if not invitation:
            raise serializers.ValidationError(
                {
                    "non_field_errors": [
                        _("Invalid invitation ID or you do not have permission.")
                    ]
                }
            )
        serializer.save(invitation=invitation)

    def get_serializer(self, *args, **kwargs):
        if self.action in ["update", "partial_update"]:
            kwargs["context"] = self.get_serializer_context()
            return GuestSerializer(*args, **kwargs, read_only_fields=["id"])
        return super().get_serializer(*args, **kwargs)


class QRVerificationViewSet(viewsets.ModelViewSet):
    queryset = QRVerification.objects.all()
    serializer_class = QRVerificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(
            guest__invitation__event__planner__user=self.request.user
        )

    @action(detail=True, methods=["post"])
    def verify(self, request, pk=None):
        verification = self.get_object()
        verification.is_valid = True
        verification.guest.checked_in = True
        verification.guest.check_in_time = verification.scanned_at
        verification.guest.save()
        verification.save()
        return Response(
            {"status": "verified", "guest": GuestSerializer(verification.guest).data}
        )


class CustomObtainAuthToken(ObtainAuthToken):
    serializer_class = CustomAuthTokenSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        token, created = Token.objects.get_or_create(user=user)
        return Response({"token": token.key, "user": UserSerializer(user).data})
