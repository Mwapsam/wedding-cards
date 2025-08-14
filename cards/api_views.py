from rest_framework import viewsets, status, permissions, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.authtoken.views import ObtainAuthToken
from django.shortcuts import get_object_or_404
from django.utils.timezone import now
from django.db.models import Count

from .models import (
    WeddingEvent, WeddingPlanner, Invitation, Guest, 
    EventSchedule, QRVerification, User
)
from .serierizers import (
    CustomAuthTokenSerializer, WeddingEventSerializer, WeddingEventCreateSerializer,
    WeddingPlannerSerializer, InvitationSerializer, GuestSerializer, GuestCreateSerializer,
    EventScheduleSerializer, EventScheduleCreateSerializer, QRVerificationSerializer,
    UserSerializer
)


class CustomAuthToken(ObtainAuthToken):
    serializer_class = CustomAuthTokenSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        token = serializer.validated_data["token"]
        return Response({
            "token": token,
            "user": UserSerializer(user).data
        })


class WeddingPlannerViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = WeddingPlannerSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return WeddingPlanner.objects.filter(user=self.request.user)


class WeddingEventViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return WeddingEventCreateSerializer
        return WeddingEventSerializer

    def get_queryset(self):
        try:
            planner = WeddingPlanner.objects.get(user=self.request.user)
            return WeddingEvent.objects.filter(planner=planner).annotate(
                guest_count=Count("invitations__guests", distinct=True)
            ).order_by("-date")
        except WeddingPlanner.DoesNotExist:
            return WeddingEvent.objects.none()

    def perform_create(self, serializer):
        planner = get_object_or_404(WeddingPlanner, user=self.request.user)
        serializer.save(planner=planner)

    @action(detail=True, methods=['get'])
    def guests(self, request, pk=None):
        """Get all guests for a specific event"""
        event = self.get_object()
        guests = Guest.objects.filter(invitation__event=event)
        serializer = GuestSerializer(guests, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        """Get event statistics"""
        event = self.get_object()
        total_guests = Guest.objects.filter(invitation__event=event).count()
        checked_in_guests = Guest.objects.filter(
            invitation__event=event, checked_in=True
        ).count()
        attending_guests = Guest.objects.filter(
            invitation__event=event, is_attending=True
        ).count()
        
        return Response({
            'total_guests': total_guests,
            'attending_guests': attending_guests,
            'checked_in_guests': checked_in_guests,
            'check_in_rate': round((checked_in_guests / total_guests * 100) if total_guests > 0 else 0, 2)
        })


class EventScheduleViewSet(viewsets.ModelViewSet):
    serializer_class = EventScheduleSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        event_id = self.request.query_params.get('event_id')
        if event_id:
            # Check if user owns this event
            try:
                planner = WeddingPlanner.objects.get(user=self.request.user)
                event = WeddingEvent.objects.get(id=event_id, planner=planner)
                return EventSchedule.objects.filter(wedding_event=event).order_by('order', 'date')
            except (WeddingPlanner.DoesNotExist, WeddingEvent.DoesNotExist):
                return EventSchedule.objects.none()
        return EventSchedule.objects.none()

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return EventScheduleCreateSerializer
        return EventScheduleSerializer

    def perform_create(self, serializer):
        event_id = self.request.data.get('wedding_event_id')
        if not event_id:
            raise serializers.ValidationError({'wedding_event_id': 'This field is required.'})
        
        planner = get_object_or_404(WeddingPlanner, user=self.request.user)
        event = get_object_or_404(WeddingEvent, id=event_id, planner=planner)
        serializer.save(wedding_event=event)


class InvitationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = InvitationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        try:
            planner = WeddingPlanner.objects.get(user=self.request.user)
            return Invitation.objects.filter(event__planner=planner).annotate(
                guest_count=Count('guests')
            )
        except WeddingPlanner.DoesNotExist:
            return Invitation.objects.none()


class GuestViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return GuestCreateSerializer
        return GuestSerializer

    def get_queryset(self):
        try:
            planner = WeddingPlanner.objects.get(user=self.request.user)
            return Guest.objects.filter(invitation__event__planner=planner)
        except WeddingPlanner.DoesNotExist:
            return Guest.objects.none()

    def perform_create(self, serializer):
        invitation_id = self.request.data.get('invitation_id')
        if not invitation_id:
            raise serializers.ValidationError({'invitation_id': 'This field is required.'})
        
        planner = get_object_or_404(WeddingPlanner, user=self.request.user)
        invitation = get_object_or_404(
            Invitation, id=invitation_id, event__planner=planner
        )
        serializer.save(invitation=invitation)

    @action(detail=True, methods=['post'])
    def check_in(self, request, pk=None):
        """Check in a guest"""
        guest = self.get_object()
        if guest.checked_in:
            return Response(
                {'error': 'Guest is already checked in'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        guest.checked_in = True
        guest.check_in_time = now()
        guest.save()
        
        # Create QR verification record
        QRVerification.objects.get_or_create(
            guest=guest,
            defaults={'is_valid': True, 'scanned_at': now()}
        )
        
        return Response(GuestSerializer(guest).data)

    @action(detail=True, methods=['get'])
    def card_info(self, request, pk=None):
        """Get card generation information for a guest"""
        guest = self.get_object()
        
        # Get multiple events if available
        event_schedules = guest.invitation.event.event_schedules.all()
        events_data = []
        
        if event_schedules.exists():
            for schedule in event_schedules:
                events_data.append({
                    'name': schedule.event_name,
                    'date': schedule.date.strftime("%A, %B %d, %Y"),
                    'time': schedule.date.strftime("%I:%M %p"),
                    'location': schedule.location,
                    'description': schedule.description or ''
                })
        
        # Get invitee name
        invitee_name = None
        if guest.guest_name:
            invitee_name = guest.guest_name
        elif guest.first_name and guest.last_name:
            invitee_name = f"{guest.first_name} {guest.last_name}"
        elif guest.first_name:
            invitee_name = guest.first_name
        
        return Response({
            'guest': GuestSerializer(guest).data,
            'invitee_name': invitee_name,
            'events': events_data if len(events_data) > 1 else None,
            'payment_amount': float(guest.payment_amount) if guest.payment_amount else None,
            'card_image_url': guest.card_image.url if guest.card_image else None,
            'qr_code_url': guest.qr_code.url if guest.qr_code else None
        })


class QRVerificationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = QRVerificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        try:
            planner = WeddingPlanner.objects.get(user=self.request.user)
            return QRVerification.objects.filter(
                guest__invitation__event__planner=planner
            ).order_by('-scanned_at')
        except WeddingPlanner.DoesNotExist:
            return QRVerification.objects.none()

    @action(detail=False, methods=['post'])
    def verify_guest(self, request):
        """Verify a guest by QR code scan"""
        guest_id = request.data.get('guest_id')
        if not guest_id:
            return Response(
                {'error': 'guest_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            guest = Guest.objects.get(id=guest_id)
        except Guest.DoesNotExist:
            return Response(
                {'error': 'Guest not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if already verified
        if QRVerification.objects.filter(guest=guest).exists():
            return Response(
                {'error': 'Guest already verified', 'guest': GuestSerializer(guest).data},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create verification and update guest
        QRVerification.objects.create(
            guest=guest,
            is_valid=True,
            scanned_at=now()
        )
        guest.checked_in = True
        guest.check_in_time = now()
        guest.save()
        
        return Response({
            'message': 'Guest verified successfully',
            'guest': GuestSerializer(guest).data
        })