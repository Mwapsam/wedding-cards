from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse
import qrcode
from PIL import Image
from io import BytesIO
from django.core.files.base import ContentFile

from utils.generators import generate_wedding_card
from .models import Guest, Invitation, User, WeddingEvent, WeddingPlanner, EventSchedule


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

        # Prepare invitee name from guest information
        invitee_name = None
        if instance.guest_name:
            invitee_name = instance.guest_name
        elif instance.first_name and instance.last_name:
            invitee_name = f"{instance.first_name} {instance.last_name}"
        elif instance.first_name:
            invitee_name = instance.first_name
        
        # Get multiple events if available
        event_schedules = instance.invitation.event.event_schedules.all()
        events_data = []
        
        if event_schedules.exists():
            # Convert EventSchedule objects to dictionaries for the generator
            for schedule in event_schedules:
                events_data.append({
                    'name': schedule.event_name,
                    'date': schedule.date.strftime("%A, %B %d, %Y"),
                    'time': schedule.date.strftime("%I:%M %p"),
                    'location': schedule.location,
                    'description': schedule.description or ''
                })
        
        # Use multiple events if available, otherwise None for single event
        events = events_data if len(events_data) > 1 else None
        
        # Get payment amount from guest
        payment_amount = instance.payment_amount
        
        # Generate card with new features
        card_file = generate_wedding_card(
            event=instance.invitation.event, 
            invitation=instance.invitation, 
            qr_image=qr_image,
            invitee_name=invitee_name,
            events=events,
            payment_amount=payment_amount
        )
        instance.card_image.save(card_file.name, card_file, save=False)

        instance.save()
