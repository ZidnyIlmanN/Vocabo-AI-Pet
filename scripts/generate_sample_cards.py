"""
Generate High-Quality Smartphone Food Cards and Synthetic Training Data.
Creates phone-ready graphical cards in data/sample_cards/ with real full-color
food illustrations (rendered with Segoe UI Emoji embedded colors), clean typography,
and vector accents.
"""
import json
import math
from pathlib import Path
import random
from PIL import Image, ImageDraw, ImageFont

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
CATALOG_PATH = DATA_DIR / "food_catalog.json"
CARDS_DIR = DATA_DIR / "sample_cards"
FOODS_DIR = DATA_DIR / "foods"

CARDS_DIR.mkdir(parents=True, exist_ok=True)
FOODS_DIR.mkdir(parents=True, exist_ok=True)

# Color themes for each food card — maximally distinct palettes
CARD_THEMES = {
    "rice_egg": {
        "bg_top": (255, 248, 220),       # Cornsilk
        "bg_bottom": (255, 236, 139),    # Light golden yellow
        "primary": (218, 165, 32),       # Goldenrod
        "border": (184, 134, 11),        # Dark goldenrod
        "accent": (255, 215, 0),         # Gold
        "text": (101, 67, 33),           # Dark brown
        "emoji": "🍚🍳",
        "tag": "RICE & EGG",
        "icon_shapes": "circles",
    },
    "fried_chicken": {
        "bg_top": (255, 237, 213),       # Peach
        "bg_bottom": (251, 191, 36),     # Amber-orange
        "primary": (234, 88, 12),        # Deep orange
        "border": (194, 65, 12),         # Burnt orange
        "accent": (251, 146, 60),        # Orange
        "text": (124, 45, 18),           # Dark rust
        "emoji": "🍗",
        "tag": "FRIED CHICKEN",
        "icon_shapes": "triangles",
    },
    "noodles": {
        "bg_top": (255, 228, 225),       # Misty rose
        "bg_bottom": (255, 160, 160),    # Light red/coral
        "primary": (220, 38, 38),        # Vivid red
        "border": (185, 28, 28),         # Dark red
        "accent": (248, 113, 113),       # Light red
        "text": (127, 29, 29),           # Dark wine red
        "emoji": "🍜",
        "tag": "NOODLES",
        "icon_shapes": "waves",
    },
    "apple": {
        "bg_top": (220, 252, 231),       # Mint
        "bg_bottom": (134, 239, 172),    # Light green
        "primary": (22, 163, 74),        # Green
        "border": (21, 128, 61),         # Dark green
        "accent": (74, 222, 128),        # Bright green
        "text": (20, 83, 45),            # Forest green
        "emoji": "🍎",
        "tag": "APPLE",
        "icon_shapes": "leaves",
    },
    "milk": {
        "bg_top": (219, 234, 254),       # Light blue
        "bg_bottom": (147, 197, 253),    # Sky blue
        "primary": (37, 99, 235),        # Royal blue
        "border": (29, 78, 216),         # Dark blue
        "accent": (96, 165, 250),        # Bright blue
        "text": (30, 58, 138),           # Navy
        "emoji": "🥛",
        "tag": "MILK",
        "icon_shapes": "drops",
    },
}


def get_font(size: int, bold: bool = False):
    """Loads system sans-serif font for text."""
    try:
        font_name = "segoeui.ttf" if not bold else "segoeuib.ttf"
        return ImageFont.truetype(font_name, size)
    except IOError:
        try:
            return ImageFont.truetype("arial.ttf", size)
        except IOError:
            return ImageFont.load_default()


def render_emoji(emoji_str: str, size: int = 150) -> Image.Image:
    """
    Renders full-color emoji graphics using Windows Segoe UI Emoji font with embedded colors.
    Returns a tightly-cropped RGBA PIL Image.
    """
    try:
        font = ImageFont.truetype("seguiemj.ttf", size)
    except Exception:
        return None

    # Scratch canvas large enough for multiple characters
    scratch_w = size * max(2, len(emoji_str) + 1)
    scratch_h = size * 2
    scratch = Image.new("RGBA", (scratch_w, scratch_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(scratch)
    draw.text((10, 10), emoji_str, font=font, embedded_color=True)
    bbox = scratch.getbbox()
    if bbox:
        return scratch.crop(bbox)
    return None


def paste_centered(target_img: Image.Image, source_img: Image.Image, cx: int, cy: int):
    """Pastes an RGBA source image centered at (cx, cy) on target_img with alpha blending."""
    if source_img is None:
        return
    sw, sh = source_img.size
    x = cx - sw // 2
    y = cy - sh // 2
    target_img.paste(source_img, (x, y), source_img)


def draw_gradient_bg(draw: ImageDraw.Draw, width: int, height: int, top_color, bottom_color):
    """Draw a smooth vertical gradient background."""
    for y in range(height):
        ratio = y / float(height)
        r = int(top_color[0] + (bottom_color[0] - top_color[0]) * ratio)
        g = int(top_color[1] + (bottom_color[1] - top_color[1]) * ratio)
        b = int(top_color[2] + (bottom_color[2] - top_color[2]) * ratio)
        draw.line([(0, y), (width, y)], fill=(r, g, b))


def draw_star(draw: ImageDraw.Draw, cx: float, cy: float, radius: float, fill):
    """Draw a crisp 5-pointed star polygon."""
    points = []
    for i in range(10):
        r = radius if i % 2 == 0 else radius * 0.45
        angle = i * math.pi / 5 - math.pi / 2
        points.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
    draw.polygon(points, fill=fill)


def draw_decorative_shapes(draw: ImageDraw.Draw, width: int, height: int, theme: dict):
    """Draw unique decorative shapes on the card background for visual distinctiveness."""
    primary = theme["primary"]
    random.seed(hash(theme["tag"]))  # Deterministic per card
    for _ in range(12):
        x = random.randint(60, width - 60)
        y = random.randint(180, height - 200)
        size = random.randint(15, 35)
        shape = theme["icon_shapes"]

        if shape == "circles":
            draw.ellipse((x, y, x + size, y + size), outline=primary, width=2)
        elif shape == "triangles":
            draw.polygon([(x, y + size), (x + size // 2, y), (x + size, y + size)],
                         outline=primary, width=2)
        elif shape == "waves":
            for offset in range(0, size, 6):
                draw.arc((x + offset, y, x + offset + 12, y + 12), 0, 180, fill=primary, width=2)
        elif shape == "leaves":
            draw.ellipse((x, y, x + size, y + size // 2), outline=primary, width=2)
            draw.line((x + size // 2, y, x + size // 2, y + size), fill=primary, width=2)
        elif shape == "drops":
            draw.ellipse((x, y + size // 3, x + size, y + size), outline=primary, width=2)
            draw.polygon([(x + size // 2, y), (x, y + size // 2), (x + size, y + size // 2)],
                         outline=primary, width=2)


def create_smartphone_card(food_id: str, info: dict) -> Path:
    """Generates a high-res, smartphone-displayable vertical card with rich food icon graphics."""
    width, height = 720, 1280
    theme = CARD_THEMES.get(food_id, {
        "bg_top": (250, 250, 250),
        "bg_bottom": (230, 230, 230),
        "primary": (100, 100, 100),
        "border": (50, 50, 50),
        "accent": (150, 150, 150),
        "text": (20, 20, 20),
        "emoji": "🍲",
        "tag": info["name"].upper(),
        "icon_shapes": "circles",
    })

    img = Image.new("RGBA", (width, height), color=(255, 255, 255, 255))
    draw = ImageDraw.Draw(img)

    # 1. Gradient background
    draw_gradient_bg(draw, width, height, theme["bg_top"], theme["bg_bottom"])

    # 2. Decorative background shapes
    draw_decorative_shapes(draw, width, height, theme)

    # 3. Outer rounded borders
    margin = 28
    draw.rounded_rectangle(
        (margin, margin, width - margin, height - margin),
        radius=40,
        outline=theme["border"],
        width=14,
    )
    draw.rounded_rectangle(
        (margin + 16, margin + 16, width - margin - 16, height - margin - 16),
        radius=30,
        outline=theme["accent"],
        width=5,
    )

    # 4. Top Header
    paw_icon = render_emoji("🐾", size=32)
    paste_centered(img, paw_icon, 180, 85)
    font_brand = get_font(32, bold=True)
    draw.text((width // 2 + 15, 85), "INTERACTIVE AI PET", fill=theme["text"], font=font_brand, anchor="mm")

    font_sub = get_font(22)
    draw.text((width // 2, 124), "FOOD VISION CARD", fill=theme["text"], font=font_sub, anchor="mm")

    # 5. Inner card frame
    frame_box = (margin + 44, 165, width - margin - 44, 900)
    draw.rounded_rectangle(frame_box, radius=32, fill=(255, 255, 255, 240), outline=theme["primary"], width=6)

    # 6. Food Icon Badge: circular white plate with decorative rim
    plate_cx = width // 2
    plate_cy = 340
    plate_radius = 125
    # Outer ring
    draw.ellipse(
        (plate_cx - plate_radius, plate_cy - plate_radius,
         plate_cx + plate_radius, plate_cy + plate_radius),
        fill=(255, 255, 255),
        outline=theme["accent"],
        width=8,
    )
    # Inner ring
    draw.ellipse(
        (plate_cx - plate_radius + 14, plate_cy - plate_radius + 14,
         plate_cx + plate_radius - 14, plate_cy + plate_radius - 14),
        outline=theme["primary"],
        width=4,
    )

    # Render REAL full-color Food Emoji Icon
    emoji_size = 140 if len(theme["emoji"]) > 1 else 170
    food_icon = render_emoji(theme["emoji"], size=emoji_size)
    if food_icon:
        paste_centered(img, food_icon, plate_cx, plate_cy)

    # 7. Big food name title
    font_title = get_font(50, bold=True)
    draw.text((width // 2, 515), theme["tag"], fill=theme["text"], font=font_title, anchor="mm")

    # 8. Description text
    font_desc = get_font(23)
    desc_text = info.get("description", "Delicious food!")
    if len(desc_text) > 40:
        mid = len(desc_text) // 2
        split = desc_text.rfind(" ", 0, mid + 10)
        if split == -1:
            split = mid
        draw.text((width // 2, 570), desc_text[:split], fill=theme["text"], font=font_desc, anchor="mm")
        draw.text((width // 2, 602), desc_text[split:].strip(), fill=theme["text"], font=font_desc, anchor="mm")
    else:
        draw.text((width // 2, 575), desc_text, fill=theme["text"], font=font_desc, anchor="mm")

    # 9. Star Rating Bar (crisp vector stars)
    bar_y = 650
    draw.rounded_rectangle((120, bar_y, width - 120, bar_y + 55), radius=20, fill=theme["primary"])
    star_center_y = bar_y + 27
    star_spacing = 42
    star_start_x = width // 2 - (star_spacing * 2)
    for i in range(5):
        draw_star(draw, star_start_x + i * star_spacing, star_center_y, 14, (255, 235, 59))

    # 10. Nutritional-style info boxes
    box_w = 150
    box_h = 75
    info_y = 745
    labels = ["YUMMY", "QUALITY", "TASTY"]
    values = ["100%", "FRESH", "A+"]
    for idx, (lbl, val) in enumerate(zip(labels, values)):
        bx = 95 + idx * (box_w + 42)
        draw.rounded_rectangle((bx, info_y, bx + box_w, info_y + box_h),
                                radius=14, fill=(255, 255, 255), outline=theme["primary"], width=3)
        font_sm = get_font(18, bold=True)
        draw.text((bx + box_w // 2, info_y + 25), val, fill=theme["primary"], font=font_sm, anchor="mm")
        font_xs = get_font(14, bold=True)
        draw.text((bx + box_w // 2, info_y + 53), lbl, fill=theme["text"], font=font_xs, anchor="mm")

    # 11. Food ID Tag badge
    badge_rect = (width // 2 - 210, 855, width // 2 + 210, 920)
    draw.rounded_rectangle(badge_rect, radius=22, fill=theme["primary"])
    font_badge = get_font(28, bold=True)
    draw.text((width // 2, 887), f"FOOD ID: {food_id.upper().replace('_', ' ')}", fill=(255, 255, 255),
              font=font_badge, anchor="mm")

    # 12. Bottom Instructions Card
    draw.rounded_rectangle((55, 960, width - 55, 1120), radius=24, fill=(255, 255, 255), outline=theme["border"], width=3)
    cam_icon = render_emoji("📷", size=32)
    paste_centered(img, cam_icon, 160, 1005)
    font_hint = get_font(25, bold=True)
    draw.text((width // 2 + 15, 1005), "Point screen towards webcam", fill=theme["text"], font=font_hint, anchor="mm")

    font_hint2 = get_font(22)
    draw.text((width // 2, 1050), "Hold steady 30-50 cm away", fill=(110, 115, 135), font=font_hint2, anchor="mm")
    draw.text((width // 2, 1085), "Wait for the pet to react!", fill=(110, 115, 135), font=font_hint2, anchor="mm")

    # 13. Bottom Brand Tag
    draw.rounded_rectangle((margin + 44, height - 95, width - margin - 44, height - 50),
                            radius=14, fill=theme["primary"])
    font_bottom = get_font(20, bold=True)
    draw.text((width // 2, height - 72), "PET FOOD VISION PROTOTYPE", fill=(255, 255, 255),
              font=font_bottom, anchor="mm")

    # Convert to RGB and save PNG
    final_rgb = img.convert("RGB")
    out_path = CARDS_DIR / f"{food_id}.png"
    final_rgb.save(out_path, "PNG", quality=95)
    print(f"Generated phone card: {out_path}")
    return out_path


def generate_synthetic_dataset_images(food_id: str, card_img_path: Path, num_samples: int = 15):
    """
    Generates synthetic phone/card camera captures in data/foods/<food_id>/
    simulating various angles, scales, and lighting conditions.
    """
    food_dir = FOODS_DIR / food_id
    food_dir.mkdir(parents=True, exist_ok=True)

    base_card = Image.open(card_img_path)

    for i in range(1, num_samples + 1):
        bg_w, bg_h = 640, 480
        # Random background (simulating laptop room/desk environment)
        r = random.randint(40, 180)
        g = random.randint(40, 180)
        b = random.randint(40, 180)
        scene = Image.new("RGB", (bg_w, bg_h), color=(r, g, b))

        # Scale card to simulate distance (between 25% and 65% of screen height)
        scale = random.uniform(0.35, 0.65)
        card_h = int(bg_h * scale)
        card_w = int(card_h * (base_card.width / base_card.height))
        scaled_card = base_card.resize((card_w, card_h), Image.Resampling.LANCZOS)

        # Rotate slightly (-15 to +15 degrees)
        angle = random.uniform(-15, 15)
        rotated_card = scaled_card.rotate(angle, expand=True, resample=Image.Resampling.BICUBIC)

        # Place card near center with random jitter
        jitter_x = random.randint(-40, 40)
        jitter_y = random.randint(-30, 30)
        pos_x = (bg_w - rotated_card.width) // 2 + jitter_x
        pos_y = (bg_h - rotated_card.height) // 2 + jitter_y

        scene.paste(rotated_card, (pos_x, pos_y), rotated_card.convert("RGBA").split()[3])

        # Save synthetic image
        sample_path = food_dir / f"image_{i:03d}.jpg"
        scene.save(sample_path, "JPEG", quality=90)


def main():
    print("Generating smartphone food cards with real food illustration icons...")
    with open(CATALOG_PATH, "r", encoding="utf-8") as f:
        catalog = json.load(f)

    for food in catalog.get("foods", []):
        f_id = food["id"]
        card_path = create_smartphone_card(f_id, food)
        generate_synthetic_dataset_images(f_id, card_path, num_samples=12)

    print("\nAll smartphone food cards successfully generated in:")
    print(f" -> {CARDS_DIR}")
    print("Initial synthetic training dataset created in:")
    print(f" -> {FOODS_DIR}")


if __name__ == "__main__":
    main()
