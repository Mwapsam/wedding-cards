from rest_framework.routers import SimpleRouter

from cards.api import GuestViewSet, InvitationViewSet, QRVerificationViewSet, UserViewSet, WeddingEventViewSet, WeddingPlannerViewSet

router = SimpleRouter()
router.register(r"users", UserViewSet)
router.register(r"wedding-planners", WeddingPlannerViewSet)
router.register(r"wedding-events", WeddingEventViewSet)
router.register(r"invitations", InvitationViewSet)
router.register(r"guests", GuestViewSet)
router.register(r"qr-verifications", QRVerificationViewSet)


app_name = "api"
urlpatterns = router.urls
