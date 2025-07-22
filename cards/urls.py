from django.urls import path
from .views import profile, send_invitations
from cards import views

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
    path("verify/<uuid:token>/", views.verify_invitation, name="verify_invitation"),
    path("invitation/<uuid:pk>/", views.invitation_card_view, name="invitation_card"),
]
