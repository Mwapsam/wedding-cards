from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import profile, send_invitations
from cards import views
from .api_views import (
    CustomAuthToken, WeddingPlannerViewSet, WeddingEventViewSet,
    EventScheduleViewSet, InvitationViewSet, GuestViewSet, QRVerificationViewSet
)

# API Router setup
router = DefaultRouter()
router.register(r'wedding-planners', WeddingPlannerViewSet, basename='weddingplanner')
router.register(r'events', WeddingEventViewSet, basename='weddingevent')
router.register(r'event-schedules', EventScheduleViewSet, basename='eventschedule')
router.register(r'invitations', InvitationViewSet, basename='invitation')
router.register(r'guests', GuestViewSet, basename='guest')
router.register(r'verifications', QRVerificationViewSet, basename='qrverification')

# Web interface URLs
urlpatterns = [
    path(
        "invitation/<uuid:invitation_id>/send/",
        send_invitations,
        name="send_invitations",
    ),
    path("", profile, name="profile"),
    path("profile/add-event/", views.add_event, name="add_event"),
    path("profile/add-guest/", views.add_guest, name="add_guest"),
    path("profile/load-event-form/", views.load_event_form, name="load_event_form"),
    path("profile/load-guest-form/", views.load_guest_form, name="load_guest_form"),
    path("event/<uuid:event_id>/", views.event_detail, name="event_detail"),
    path("verify/<uuid:guest_id>/", views.verify_invitation, name="verify_invitation"),
    path("invitation/<uuid:pk>/", views.invitation_card_view, name="invitation_card"),
    
    # API URLs
    path("api/auth/", CustomAuthToken.as_view(), name="api_auth"),
    path("api/", include(router.urls)),
]
