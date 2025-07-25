from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from django.core.mail import EmailMessage
from django.conf import settings
from django.db.models import Count
from django.template.loader import render_to_string
from django.contrib import messages
from django.http import HttpResponse
from django.utils.timezone import now


from .models import Invitation, Guest, QRVerification, WeddingPlanner, WeddingEvent
from .forms import GuestForm, WeddingEventForm
from PIL import Image
from io import BytesIO


@login_required
def send_invitations(request, invitation_id):
    invitation = get_object_or_404(Invitation, id=invitation_id)
    if invitation.event.planner.user != request.user:
        messages.error(
            request, "You are not authorized to send invitations for this event."
        )
        return redirect("profile")

    if not invitation.card_image or not invitation.qr_code:
        messages.error(request, "Invitation is missing card image or QR code.")
        return redirect("profile")

    card = Image.open(invitation.card_image.path)
    qr = Image.open(invitation.qr_code.path)
    qr = qr.resize((100, 100))
    card.paste(qr, (card.width - 110, card.height - 110))
    buffer = BytesIO()
    card.save(buffer, format="PNG")
    invitation_image = buffer.getvalue()

    guests = invitation.guests.all()
    if not guests:
        messages.error(request, "No guests found for this invitation.")
        return redirect("profile")

    for guest in guests:
        if not guest.email:
            messages.warning(request, f"No email provided for guest {guest}.")
            continue

        context = {
            "guest": guest,
            "invitation": invitation,
            "event": invitation.event,
            "site_name": "Wedding Reservation System",
        }
        email_subject = f"Invitation to {invitation.event.title}"
        email_body = render_to_string("account/email/invitation_email.html", context)

        email = EmailMessage(
            subject=email_subject,
            body=email_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[guest.email],
        )
        email.content_subtype = "html"
        email.attach(f"invitation_{invitation.id}.png", invitation_image, "image/png")

        try:
            email.send()
            messages.success(request, f"Invitation sent to {guest.email}.")
        except Exception as e:
            messages.error(
                request, f"Failed to send invitation to {guest.email}: {str(e)}"
            )

    return redirect("profile")


@login_required
def profile(request):
    try:
        planner = WeddingPlanner.objects.get(user=request.user)
    except WeddingPlanner.DoesNotExist:
        messages.error(request, "You are not registered as a wedding planner.")
        return redirect("profile")

    events = (
        WeddingEvent.objects.filter(planner=planner)
        .annotate(guest_count=Count("invitations__guests", distinct=True))
        .order_by("-date")
    )
    invitations = Invitation.objects.filter(event__planner=planner)
    event_form = WeddingEventForm()

    context = {
        "events": events,
        "invitations": invitations,
        "event_form": event_form,
    }
    return render(request, "profile.html", context)


@login_required
def add_event(request):
    if request.headers.get("HX-Request") != "true":
        return HttpResponse("This endpoint is for HTMX requests only.", status=400)

    try:
        planner = WeddingPlanner.objects.get(user=request.user)
    except WeddingPlanner.DoesNotExist:
        return HttpResponse("You are not registered as a wedding planner.", status=403)

    form = WeddingEventForm(request.POST or None)
    if form.is_valid():
        event = form.save(commit=False)
        event.planner = planner
        event.save()

        event_list_html = render_to_string(
            "partials/event_list.html",
            {
                "events": WeddingEvent.objects.filter(planner=planner)
                .annotate(guest_count=Count("invitations__guests", distinct=True))
                .order_by("-date")
            },
            request=request,
        )

        response_html = f"""
            <div id="event-list" hx-swap-oob="innerHTML">
                {event_list_html}
            </div>
            <div id="modal-body" hx-swap-oob="innerHTML"></div>
            <div class="success-card">{event_list_html}</div>
            <script>
                // Close modal after a short delay
                setTimeout(() => {{
                    document.getElementById("modal").style.display = "none";
                }}, 1000);
                htmx.process(document.body);
            </script>
        """
        return HttpResponse(response_html)

    else:
        html = render_to_string("partials/event_form.html", {"event_form": form}, request=request)
        return HttpResponse(html)


@login_required
def add_guest(request):
    if request.headers.get("HX-Request") != "true":
        return HttpResponse("This endpoint is for HTMX requests only.", status=400)

    try:
        planner = WeddingPlanner.objects.get(user=request.user)
    except WeddingPlanner.DoesNotExist:
        return HttpResponse("You are not registered as a wedding planner.", status=403)

    invitation_id = request.POST.get("invitation")
    invitation = get_object_or_404(Invitation, id=invitation_id, event__planner=planner)

    form = GuestForm(request.POST, invitation=invitation)
    if form.is_valid():
        guest = form.save(commit=False)
        guest.invitation = invitation
        guest.save()

        invitation_list_html = render_to_string(
            "partials/invitation_list.html",
            {
                "invitations": Invitation.objects.filter(
                    event__planner=planner
                ).annotate(guest_count=Count("guests"))
            },
            request=request,
        )

        response_html = f"""
            <div id="invitation-list" hx-swap-oob="innerHTML">
                {invitation_list_html}
            </div>
            <div id="modal-body" hx-swap-oob="innerHTML"></div>
            <div class="success-card">{invitation_list_html}</div>
            <script>
                setTimeout(() => {{
                    document.getElementById("modal").style.display = "none";
                }}, 1000);
                htmx.process(document.body);
            </script>
        """
        return HttpResponse(response_html)

    else:
        invitations = Invitation.objects.filter(event__planner=planner)
        html = render_to_string(
            "partials/guest_form.html",
            {"guest_form": form, "invitations": invitations},
            request=request,
        )
        print("Form: ", form)
        return HttpResponse(html, status=400)


@login_required
def load_event_form(request):
    form = WeddingEventForm()
    html = render_to_string(
        "partials/event_form.html", {"event_form": form}, request=request
    )
    return HttpResponse(html)


@login_required
def load_guest_form(request):
    try:
        planner = WeddingPlanner.objects.get(user=request.user)
    except WeddingPlanner.DoesNotExist:
        return HttpResponse("You are not registered as a wedding planner.", status=403)

    invitations = Invitation.objects.filter(event__planner=planner)
    form = GuestForm()
    html = render_to_string(
        "partials/guest_form.html",
        {"guest_form": form, "invitations": invitations},
        request=request,
    )
    return HttpResponse(html)


@login_required
def event_detail(request, event_id):
    event = get_object_or_404(WeddingEvent, id=event_id, planner__user=request.user)
    guests = Guest.objects.filter(invitation__event=event)

    return render(
        request,
        "event_detail.html",
        {
            "event": event,
            "guests": guests,
        },
    )


def verify_invitation(request, guest_id):
    guest = get_object_or_404(Guest, id=guest_id)
    event = guest.invitation.event  # Get the related event

    # Check if already verified
    if QRVerification.objects.filter(guest=guest).exists():
        return render(
            request,
            "invitations/verification_failed.html",
            {
                "guest": guest,
                "event": event,
                "message": "This invitation has already been used.",
            },
        )

    # Create verification and update check-in status
    QRVerification.objects.create(
        guest=guest,
        is_valid=True,
        scanned_at=now(),
    )
    guest.checked_in = True
    guest.check_in_time = now()
    guest.save()

    return render(
        request,
        "invitations/verification_success.html",
        {
            "guest": guest,
            "event": event,
            "message": "Invitation verified successfully!",
        },
    )


def invitation_card_view(request, pk):
    invitation = get_object_or_404(Guest, pk=pk)

    return render(
        request, "invitations/invitation_card.html", {"invitation": invitation}
    )
