from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse
import qrcode
from PIL import Image
from io import BytesIO
from django.core.files.base import ContentFile

from utils.generators import generate_wedding_card
from .models import Guest, Invitation, User, WeddingEvent, WeddingPlanner


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
            event=instance
        )


@receiver(post_save, sender=Guest)
def generate_qr_and_card(sender, instance, created, **kwargs):
    if created:
        base_url = getattr(settings, "SITE_URL", "http://localhost:8000")
        verify_url = f"{base_url}{reverse('verify_invitation', args=[str(instance.id)])}"

        qr_img = qrcode.make(verify_url)
        qr_buffer = BytesIO()
        qr_img.save(qr_buffer, format="PNG")
        qr_image = Image.open(qr_buffer)

        qr_io = BytesIO()
        qr_img.save(qr_io, format="PNG")
        qr_file_name = f"guest_qr_{instance.id}.png"
        instance.qr_code.save(qr_file_name, ContentFile(qr_io.getvalue()), save=False)

        card_file = generate_wedding_card(
            instance.invitation.event, instance.invitation, qr_image=qr_image
        )
        instance.card_image.save(card_file.name, card_file, save=False)

        instance.save()
