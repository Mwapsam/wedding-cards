from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.conf import settings
import os
import math


def generate_wedding_card(event, invitation=None):
    # Portrait card dimensions
    card_size = (600, 900)  # width x height (portrait)

    # Colors palette
    background_gradient_start = (252, 250, 248)  # Warm white
    background_gradient_end = (248, 242, 235)  # Deeper cream
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

    # Decorative line under invitation text
    line_y = 160
    line_length = 150
    line_x = (card_size[0] - line_length) // 2
    draw.line(
        [(line_x, line_y), (line_x + line_length, line_y)], fill=accent_color, width=2
    )

    # Event title centered
    event_title = f"The {event.title}"
    bbox = draw.textbbox((0, 0), event_title, font=title_font)
    x_pos = (card_size[0] - (bbox[2] - bbox[0])) // 2
    draw.text((x_pos, 180), event_title, fill=primary_text_color, font=title_font)

    # Decorative ellipses around title
    title_y = 210
    draw.ellipse(
        [card_size[0] // 2 - 90, title_y, card_size[0] // 2 - 85, title_y + 5],
        fill=accent_color,
    )
    draw.ellipse(
        [card_size[0] // 2 + 85, title_y, card_size[0] // 2 + 90, title_y + 5],
        fill=accent_color,
    )

    # Date and time
    date_str = event.date.strftime("%A, %B %d, %Y")
    time_str = event.date.strftime("%I:%M %p")

    bbox = draw.textbbox((0, 0), date_str, font=body_font)
    x_pos = (card_size[0] - (bbox[2] - bbox[0])) // 2
    draw.text((x_pos, 280), date_str, fill=primary_text_color, font=body_font)

    bbox = draw.textbbox((0, 0), time_str, font=accent_font)
    x_pos = (card_size[0] - (bbox[2] - bbox[0])) // 2
    draw.text((x_pos, 310), time_str, fill=accent_color, font=accent_font)

    # Venue label "AT"
    venue_label = "AT"
    bbox = draw.textbbox((0, 0), venue_label, font=accent_font)
    x_pos = (card_size[0] - (bbox[2] - bbox[0])) // 2
    draw.text((x_pos, 350), venue_label, fill=secondary_text_color, font=accent_font)

    # Venue name
    venue_name = event.venue
    bbox = draw.textbbox((0, 0), venue_name, font=body_font)
    x_pos = (card_size[0] - (bbox[2] - bbox[0])) // 2
    draw.text((x_pos, 380), venue_name, fill=primary_text_color, font=body_font)

    # Bottom decorations
    bottom_y = 550
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

    # RSVP info if available
    if hasattr(event, "rsvp_info") and event.rsvp_info:
        rsvp_text = "RSVP"
        bbox = draw.textbbox((0, 0), rsvp_text, font=accent_font)
        x_pos = (card_size[0] - (bbox[2] - bbox[0])) // 2
        draw.text(
            (x_pos, bottom_y + 40),
            rsvp_text,
            fill=secondary_text_color,
            font=accent_font,
        )

        rsvp_details = event.rsvp_info
        bbox = draw.textbbox((0, 0), rsvp_details, font=body_font)
        x_pos = (card_size[0] - (bbox[2] - bbox[0])) // 2
        draw.text(
            (x_pos, bottom_y + 65),
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

    # Save image to BytesIO buffer
    buffer = BytesIO()
    image.save(buffer, format="PNG", optimize=True)
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
