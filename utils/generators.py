from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.conf import settings
import os
import math


def generate_wedding_card(event, invitation=None, qr_image=None, invitee_name=None, events=None, payment_amount=None):
    card_size = (600, 900)  

    background_gradient_start = (252, 250, 248)  
    background_gradient_end = (248, 242, 235)  
    primary_text_color = (60, 50, 45)  # Dark brown
    accent_color = (170, 120, 70)  # Gold
    secondary_text_color = (100, 85, 75)  # Medium brown
    border_color = (190, 160, 120)  # Gold border

    # Create base image and drawer
    image = Image.new("RGB", card_size, color=background_gradient_start)
    draw = ImageDraw.Draw(image)

    # Gradient background
    for y in range(card_size[1]):
        ratio = y / card_size[1]
        r = int(
            background_gradient_start[0] * (1 - ratio)
            + background_gradient_end[0] * ratio
        )
        g = int(
            background_gradient_start[1] * (1 - ratio)
            + background_gradient_end[1] * ratio
        )
        b = int(
            background_gradient_start[2] * (1 - ratio)
            + background_gradient_end[2] * ratio
        )
        draw.line([(0, y), (card_size[0], y)], fill=(r, g, b))

    # Borders
    border_margin = 30
    border_width = 3

    draw.rectangle(
        [
            border_margin,
            border_margin,
            card_size[0] - border_margin,
            card_size[1] - border_margin,
        ],
        outline=border_color,
        width=border_width,
    )

    inner_margin = border_margin + 15
    draw.rectangle(
        [
            inner_margin,
            inner_margin,
            card_size[0] - inner_margin,
            card_size[1] - inner_margin,
        ],
        outline=accent_color,
        width=1,
    )

    # Load fonts helper
    def load_font(font_name, size):
        font_paths = [
            os.path.join(settings.BASE_DIR, "static", "fonts", font_name),
            f"/System/Library/Fonts/{font_name}",
            f"C:/Windows/Fonts/{font_name}",
        ]
        for font_path in font_paths:
            try:
                if os.path.exists(font_path):
                    return ImageFont.truetype(font_path, size)
            except:
                continue
        return ImageFont.load_default()

    # Fonts scaled down for portrait
    title_font = load_font("GreatVibes-Regular.ttf", 40)
    subtitle_font = load_font("Poppins-Light.ttf", 16)
    body_font = load_font("Poppins-Regular.ttf", 14)
    accent_font = load_font("Poppins-Medium.ttf", 12)
    small_font = load_font("Poppins-Regular.ttf", 10)

    # Decorative flourishes function
    def draw_flourish(x, y, size=20):
        for i in range(0, 360, 10):
            angle = math.radians(i)
            radius = size * (1 - i / 360) * 0.5
            x1 = x + radius * math.cos(angle)
            y1 = y + radius * math.sin(angle)
            x2 = x + (radius + 2) * math.cos(angle + 0.1)
            y2 = y + (radius + 2) * math.sin(angle + 0.1)
            draw.line([(x1, y1), (x2, y2)], fill=accent_color, width=1)

    # Flourishes at top left and right
    draw_flourish(card_size[0] // 2 - 100, 100, 20)
    draw_flourish(card_size[0] // 2 + 100, 100, 20)

    # Invitation text centered
    invitation_text = "You're Cordially Invited"
    bbox = draw.textbbox((0, 0), invitation_text, font=subtitle_font)
    x_pos = (card_size[0] - (bbox[2] - bbox[0])) // 2
    draw.text(
        (x_pos, 130), invitation_text, fill=secondary_text_color, font=subtitle_font
    )

    # Add invitee name if provided
    current_y = 160
    if invitee_name:
        invitee_text = f"Dear {invitee_name},"
        bbox = draw.textbbox((0, 0), invitee_text, font=accent_font)
        x_pos = (card_size[0] - (bbox[2] - bbox[0])) // 2
        draw.text((x_pos, current_y), invitee_text, fill=accent_color, font=accent_font)
        current_y += 25

    # Decorative line under invitation text
    line_y = current_y
    line_length = 150
    line_x = (card_size[0] - line_length) // 2
    draw.line(
        [(line_x, line_y), (line_x + line_length, line_y)], fill=accent_color, width=2
    )

    # Event title centered
    event_title = f"The {event.title}"
    bbox = draw.textbbox((0, 0), event_title, font=title_font)
    x_pos = (card_size[0] - (bbox[2] - bbox[0])) // 2
    title_y = line_y + 20
    draw.text((x_pos, title_y), event_title, fill=primary_text_color, font=title_font)

    # Couple's names (if available)
    current_y = title_y + 50
    if hasattr(event, 'couple') and event.couple:
        couple_text = event.couple
        bbox = draw.textbbox((0, 0), couple_text, font=subtitle_font)
        x_pos = (card_size[0] - (bbox[2] - bbox[0])) // 2
        draw.text((x_pos, current_y), couple_text, fill=accent_color, font=subtitle_font)
        current_y += 40
    
    decorative_y = current_y

    # Decorative ellipses around title/couple area
    draw.ellipse(
        [card_size[0] // 2 - 90, decorative_y, card_size[0] // 2 - 85, decorative_y + 5],
        fill=accent_color,
    )
    draw.ellipse(
        [card_size[0] // 2 + 85, decorative_y, card_size[0] // 2 + 90, decorative_y + 5],
        fill=accent_color,
    )

    # Multiple events or single event
    events_y = decorative_y + 30
    if events and len(events) > 1:
        # Multiple events
        for i, evt in enumerate(events):
            # Event name/label
            event_name = evt.get('name', f'Event {i + 1}')
            bbox = draw.textbbox((0, 0), event_name, font=accent_font)
            x_pos = (card_size[0] - (bbox[2] - bbox[0])) // 2
            draw.text((x_pos, events_y), event_name, fill=accent_color, font=accent_font)
            events_y += 20
            
            # Date and time
            date_str = evt.get('date', 'TBD')
            time_str = evt.get('time', 'TBD')
            
            bbox = draw.textbbox((0, 0), date_str, font=body_font)
            x_pos = (card_size[0] - (bbox[2] - bbox[0])) // 2
            draw.text((x_pos, events_y), date_str, fill=primary_text_color, font=body_font)
            events_y += 20
            
            bbox = draw.textbbox((0, 0), time_str, font=accent_font)
            x_pos = (card_size[0] - (bbox[2] - bbox[0])) // 2
            draw.text((x_pos, events_y), time_str, fill=secondary_text_color, font=accent_font)
            events_y += 20
            
            # Location
            location = evt.get('location', 'TBD')
            venue_label = "AT"
            bbox = draw.textbbox((0, 0), venue_label, font=accent_font)
            x_pos = (card_size[0] - (bbox[2] - bbox[0])) // 2
            draw.text((x_pos, events_y), venue_label, fill=secondary_text_color, font=accent_font)
            events_y += 15
            
            bbox = draw.textbbox((0, 0), location, font=body_font)
            x_pos = (card_size[0] - (bbox[2] - bbox[0])) // 2
            draw.text((x_pos, events_y), location, fill=primary_text_color, font=body_font)
            events_y += 30
    else:
        # Single event (original behavior)
        date_str = event.date.strftime("%A, %B %d, %Y")
        time_str = event.date.strftime("%I:%M %p")

        bbox = draw.textbbox((0, 0), date_str, font=body_font)
        x_pos = (card_size[0] - (bbox[2] - bbox[0])) // 2
        draw.text((x_pos, events_y), date_str, fill=primary_text_color, font=body_font)
        events_y += 25

        bbox = draw.textbbox((0, 0), time_str, font=accent_font)
        x_pos = (card_size[0] - (bbox[2] - bbox[0])) // 2
        draw.text((x_pos, events_y), time_str, fill=accent_color, font=accent_font)
        events_y += 30

        # Venue label "AT"
        venue_label = "AT"
        bbox = draw.textbbox((0, 0), venue_label, font=accent_font)
        x_pos = (card_size[0] - (bbox[2] - bbox[0])) // 2
        draw.text((x_pos, events_y), venue_label, fill=secondary_text_color, font=accent_font)
        events_y += 15

        # Venue name
        venue_name = event.venue
        bbox = draw.textbbox((0, 0), venue_name, font=body_font)
        x_pos = (card_size[0] - (bbox[2] - bbox[0])) // 2
        draw.text((x_pos, events_y), venue_name, fill=primary_text_color, font=body_font)
        events_y += 30

    # Payment amount if provided
    if payment_amount:
        # Add some spacing
        events_y += 10
        
        # Payment label
        payment_label = "Registration Fee:"
        bbox = draw.textbbox((0, 0), payment_label, font=accent_font)
        x_pos = (card_size[0] - (bbox[2] - bbox[0])) // 2
        draw.text((x_pos, events_y), payment_label, fill=secondary_text_color, font=accent_font)
        events_y += 20
        
        # Payment amount
        amount_text = f"${payment_amount}" if isinstance(payment_amount, (int, float)) else str(payment_amount)
        bbox = draw.textbbox((0, 0), amount_text, font=body_font)
        x_pos = (card_size[0] - (bbox[2] - bbox[0])) // 2
        draw.text((x_pos, events_y), amount_text, fill=accent_color, font=body_font)
        events_y += 30

    # Bible scripture
    scripture_text = '"He who finds a wife finds what is good'
    scripture_reference = 'and receives favor from the LORD."'
    scripture_verse = "Proverbs 18:22"
    
    # Scripture text with line wrapping (dynamic positioning)
    scripture_y = events_y + 10
    bbox = draw.textbbox((0, 0), scripture_text, font=accent_font)
    x_pos = (card_size[0] - (bbox[2] - bbox[0])) // 2
    draw.text((x_pos, scripture_y), scripture_text, fill=secondary_text_color, font=accent_font)
    
    bbox = draw.textbbox((0, 0), scripture_reference, font=accent_font)
    x_pos = (card_size[0] - (bbox[2] - bbox[0])) // 2
    draw.text((x_pos, scripture_y + 15), scripture_reference, fill=secondary_text_color, font=accent_font)
    
    # Scripture reference in italics style
    bbox = draw.textbbox((0, 0), scripture_verse, font=small_font)
    x_pos = (card_size[0] - (bbox[2] - bbox[0])) // 2
    draw.text((x_pos, scripture_y + 40), scripture_verse, fill=accent_color, font=small_font)

    # Adjust bottom decorations position dynamically
    bottom_y = scripture_y + 70

    separator_length = 200
    separator_x = (card_size[0] - separator_length) // 2
    draw.line(
        [(separator_x, bottom_y), (separator_x + separator_length, bottom_y)],
        fill=border_color,
        width=1,
    )

    diamond_size = 5
    for i in range(5):
        diamond_x = separator_x + (separator_length // 4) * i
        diamond_points = [
            (diamond_x, bottom_y - diamond_size),
            (diamond_x + diamond_size, bottom_y),
            (diamond_x, bottom_y + diamond_size),
            (diamond_x - diamond_size, bottom_y),
        ]
        draw.polygon(diamond_points, fill=accent_color)

    # RSVP info if available (adjust position based on QR code)
    if hasattr(event, "rsvp_info") and event.rsvp_info:
        rsvp_y_offset = 40 if not qr_image else 30
        details_y_offset = 65 if not qr_image else 50
        
        rsvp_text = "RSVP"
        bbox = draw.textbbox((0, 0), rsvp_text, font=accent_font)
        x_pos = (card_size[0] - (bbox[2] - bbox[0])) // 2
        draw.text(
            (x_pos, bottom_y + rsvp_y_offset),
            rsvp_text,
            fill=secondary_text_color,
            font=accent_font,
        )

        rsvp_details = event.rsvp_info
        bbox = draw.textbbox((0, 0), rsvp_details, font=body_font)
        x_pos = (card_size[0] - (bbox[2] - bbox[0])) // 2
        draw.text(
            (x_pos, bottom_y + details_y_offset),
            rsvp_details,
            fill=secondary_text_color,
            font=body_font,
        )

    # Corner flourishes
    corner_size = 20
    margin = 40

    # Top-left corner
    for i in range(3):
        draw.arc(
            [
                margin - corner_size + i * 7,
                margin - corner_size + i * 7,
                margin + corner_size - i * 7,
                margin + corner_size - i * 7,
            ],
            180,
            270,
            fill=accent_color,
            width=1,
        )

    # Top-right corner
    for i in range(3):
        draw.arc(
            [
                card_size[0] - margin - corner_size + i * 7,
                margin - corner_size + i * 7,
                card_size[0] - margin + corner_size - i * 7,
                margin + corner_size - i * 7,
            ],
            270,
            360,
            fill=accent_color,
            width=1,
        )

    # Bottom-left corner
    for i in range(3):
        draw.arc(
            [
                margin - corner_size + i * 7,
                card_size[1] - margin - corner_size + i * 7,
                margin + corner_size - i * 7,
                card_size[1] - margin + corner_size - i * 7,
            ],
            90,
            180,
            fill=accent_color,
            width=1,
        )

    # Bottom-right corner
    for i in range(3):
        draw.arc(
            [
                card_size[0] - margin - corner_size + i * 7,
                card_size[1] - margin - corner_size + i * 7,
                card_size[0] - margin + corner_size - i * 7,
                card_size[1] - margin + corner_size - i * 7,
            ],
            0,
            90,
            fill=accent_color,
            width=1,
        )

    # QR Code placement - smaller size at bottom left
    if qr_image:
        # Smaller QR code
        qr_size = 80  # Reduced from 160 to 80
        
        # Position at bottom left with margin
        margin_from_edge = 50
        qr_x = margin_from_edge
        qr_y = card_size[1] - qr_size - margin_from_edge
        
        # Create a white background with subtle border for the QR code
        padding = 8  # Reduced padding
        bg_x = qr_x - padding
        bg_y = qr_y - padding
        bg_size = qr_size + (padding * 2)
        
        # Draw white background
        draw.rectangle(
            [bg_x, bg_y, bg_x + bg_size, bg_y + bg_size],
            fill=(255, 255, 255),
            outline=border_color,
            width=1
        )
        
        # Resize and paste the QR code
        qr_resized = qr_image.resize((qr_size, qr_size), Image.Resampling.LANCZOS)
        image.paste(qr_resized, (qr_x, qr_y))
        
        # Add "Scan" text below QR code (smaller text)
        scan_text = "Scan"
        bbox = draw.textbbox((0, 0), scan_text, font=small_font)
        text_x = qr_x + (qr_size - (bbox[2] - bbox[0])) // 2  # Center under QR code
        text_y = qr_y + qr_size + 5
        draw.text(
            (text_x, text_y),
            scan_text,
            fill=secondary_text_color,
            font=small_font,
        )

    # Save image to BytesIO buffer
    buffer = BytesIO()
    image.save(buffer, format="PNG", optimize=True, quality=95)
    buffer.seek(0)

    # Safe file name
    safe_title = "".join(
        c for c in event.title if c.isalnum() or c in (" ", "-", "_")
    ).rstrip()
    file_name = f"wedding_invitation_{safe_title}_{event.id}.png"

    # Return as InMemoryUploadedFile for Django
    return InMemoryUploadedFile(
        buffer, None, file_name, "image/png", buffer.getbuffer().nbytes, None
    )