from django.db.models.signals import post_save
from django.dispatch import receiver
import qrcode
from io import BytesIO
from django.core.files import File
from .models import Invitation, User, WeddingEvent, WeddingPlanner


@receiver(post_save, sender=User)
def create_wedding_planner(sender, instance, created, **kwargs):
    if created:
        company_name = f"{instance.get_full_name() or instance.get_username()}'s Events"
        phone = instance.phone or "N/A" 
        WeddingPlanner.objects.create(
            user=instance,
            company_name=company_name,
            phone=phone,
            created_at=instance.date_joined,
        )


@receiver(post_save, sender=WeddingEvent)
def create_invitation_for_event(sender, instance, created, **kwargs):
    if created:
        Invitation.objects.create(
            event=instance,
            card_image=None,  
            qr_code=None,  
        )
