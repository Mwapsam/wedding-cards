from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from rest_framework.authtoken.models import Token
from .models import WeddingEvent, WeddingPlanner, Invitation, Guest, EventSchedule, QRVerification

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
            token, _ = Token.objects.get_or_create(user=user)
            return {"user": user, "token": token.key}
        raise serializers.ValidationError(
            {"non_field_errors": [_("Invalid credentials.")]}
        )


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'phone', 'first_name', 'last_name', 'is_active', 'date_joined']
        read_only_fields = ['id', 'date_joined']


class WeddingPlannerSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = WeddingPlanner
        fields = ['id', 'user', 'company_name', 'slug', 'phone', 'created_at']
        read_only_fields = ['id', 'slug', 'created_at']


class EventScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventSchedule
        fields = ['id', 'event_name', 'date', 'location', 'description', 'order']
        read_only_fields = ['id']


class WeddingEventSerializer(serializers.ModelSerializer):
    planner = WeddingPlannerSerializer(read_only=True)
    event_schedules = EventScheduleSerializer(many=True, read_only=True)
    
    class Meta:
        model = WeddingEvent
        fields = [
            'id', 'planner', 'title', 'couple', 'date', 'venue', 
            'description', 'status', 'event_schedules'
        ]
        read_only_fields = ['id']


class GuestSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Guest
        fields = [
            'id', 'guest_name', 'first_name', 'last_name', 'full_name',
            'email', 'phone', 'is_attending', 'checked_in', 'check_in_time',
            'payment_amount', 'card_image', 'qr_code'
        ]
        read_only_fields = ['id', 'card_image', 'qr_code', 'checked_in', 'check_in_time']
    
    def get_full_name(self, obj):
        if obj.guest_name:
            return obj.guest_name
        elif obj.first_name and obj.last_name:
            return f"{obj.first_name} {obj.last_name}"
        elif obj.first_name:
            return obj.first_name
        return ""


class InvitationSerializer(serializers.ModelSerializer):
    event = WeddingEventSerializer(read_only=True)
    guests = GuestSerializer(many=True, read_only=True)
    guest_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Invitation
        fields = ['id', 'event', 'created_at', 'guests', 'guest_count']
        read_only_fields = ['id', 'created_at']
    
    def get_guest_count(self, obj):
        return obj.guests.count()


class QRVerificationSerializer(serializers.ModelSerializer):
    guest = GuestSerializer(read_only=True)
    
    class Meta:
        model = QRVerification
        fields = ['id', 'guest', 'scanned_at', 'is_valid']
        read_only_fields = ['id', 'scanned_at']


# Serializers for creating/updating with nested relationships
class EventScheduleCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventSchedule
        fields = ['event_name', 'date', 'location', 'description', 'order']


class WeddingEventCreateSerializer(serializers.ModelSerializer):
    event_schedules = EventScheduleCreateSerializer(many=True, required=False)
    
    class Meta:
        model = WeddingEvent
        fields = ['title', 'couple', 'date', 'venue', 'description', 'status', 'event_schedules']
    
    def create(self, validated_data):
        event_schedules_data = validated_data.pop('event_schedules', [])
        event = WeddingEvent.objects.create(**validated_data)
        
        for schedule_data in event_schedules_data:
            EventSchedule.objects.create(wedding_event=event, **schedule_data)
        
        return event
    
    def update(self, instance, validated_data):
        event_schedules_data = validated_data.pop('event_schedules', [])
        
        # Update event fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update event schedules
        if event_schedules_data:
            # Clear existing schedules and create new ones
            instance.event_schedules.all().delete()
            for schedule_data in event_schedules_data:
                EventSchedule.objects.create(wedding_event=instance, **schedule_data)
        
        return instance


class GuestCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Guest
        fields = [
            'guest_name', 'first_name', 'last_name', 'email', 
            'phone', 'is_attending', 'payment_amount'
        ]
