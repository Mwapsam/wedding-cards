from django.contrib import admin

from cards.models import (
    Guest,
    Invitation,
    QRVerification,
    User,
    WeddingEvent,
    WeddingPlanner,
)


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    pass


@admin.register(WeddingPlanner)
class WeddingPlannerAdmin(admin.ModelAdmin):
    pass


@admin.register(WeddingEvent)
class WeddingEventAdmin(admin.ModelAdmin):
    pass


@admin.register(Invitation)
class InvitationAdmin(admin.ModelAdmin):
    pass


@admin.register(Guest)
class GuestAdmin(admin.ModelAdmin):
    pass


@admin.register(QRVerification)
class QRVerificationAdmin(admin.ModelAdmin):
    pass
