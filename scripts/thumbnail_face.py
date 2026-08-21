#!/usr/bin/env python3
"""
thumbnail_face.py — Miniatures YouTube avec visage IA expressif.

Étend thumbnail_generator.py de TST en ajoutant un visage émotionnel
généré par IA (ComfyUI/FLUX) pour un CTR +50%.

Usage:
    python thumbnail_face.py --title "5 outils IA" --emotion surprise --output thumb.jpg
    python thumbnail_face.py --title "..." --emotion curiosity --ab-test  # génère 2 variantes
    python thumbnail_face.py --title "..." --no-face  # sans visage (fallback)
"""
from __future__ import annotations

import argparse
import subprocess
from pathlib import Path
from typing import Literal

import yaml
from PIL import Image, ImageDraw, ImageFont, ImageFilter

SCRIPT_DIR = Path(__file__).parent.parent
UNIFIED_CONFIG = SCRIPT_DIR / "config" / "unified_config.yaml"
TST_PATH = Path.home() / "MyWorkDirectory" / "TestShortYoutube"
THUMBNAIL_DIR = SCRIPT_DIR / "storage" / "thumbnails"

W, H = 1280, 720

# Emotion → ComfyUI prompt mapping
EMOTION_PROMPTS = {
    "surprise": "shocked surprised male developer face, eyes wide open, mouth open, looking at computer screen, dramatic lighting, cinematic, 8K, high quality",
    "curiosity": "curious male developer face, raised eyebrow, leaning forward, looking at screen, dramatic lighting, cinematic, 8K",
    "satisfaction": "satisfied happy male developer face, slight smile, nodding, looking at screen result, warm lighting, cinematic, 8K",
    "determination": "determined focused male developer face, intense stare, clenched jaw, looking at code, dramatic lighting, cinematic, 8K",
    "shock": "shocked male developer face, hand on head, disbelief expression, looking at screen, dramatic lighting, cinematic, 8K",
}

EMOTION_COLORS = {
    "surprise": (255, 200, 0),     # jaune
    "curiosity": (0, 212, 255),    # cyan
    "satisfaction": (50, 200, 100), # vert
    "determination": (255, 100, 50), # orange
    "shock": (255, 50, 50),        # rouge
}

FONT_CANDIDATES = {
    "impact": [
        "/System/Library/Fonts/Supplemental/Impact.ttf",
        "/usr/share/fonts/truetype/msttcorefonts/Impact.ttf",
    ],
    "bold": [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ],
}


def _find_font(name: str) -> str:
    for path in FONT_CANDIDATES.get(name, []):
        if Path(path).exists():
            return path
    return ""


def load_config() -> dict:
    with open(UNIFIED_CONFIG) as f:
        return yaml.safe_load(f)


def generate_face_image(emotion: str, output_path: Path, cfg: dict) -> bool:
    """Generate a face image via TST's image_generator (ComfyUI → Gemini → procedural cascade)."""
    prompt = EMOTION_PROMPTS.get(emotion, EMOTION_PROMPTS["surprise"])

    try:
        import sys
        sys.path.insert(0, str(TST_PATH / "src"))
        from image_generator import generate_image_pil, which_backend

        backend = which_backend(prompt)
        print(f"  → Génération visage via {backend} (émotion: {emotion})...")
        img = generate_image_pil(f"portrait photo of a {prompt}")
        if img:
            # Resize to ~500x500 for thumbnail
            img = img.resize((500, 500), Image.Resampling.LANCZOS)
            img.save(str(output_path))
            print(f"  ✅ Visage généré ({backend}) : {output_path}")
            return True
    except Exception as e:
        print(f"  ⚠️  Génération image indisponible: {e}")

    # Fallback: create a gradient placeholder with emotion color
    print(f"  → Fallback: placeholder avec couleur d'émotion ({emotion})")
    color = EMOTION_COLORS.get(emotion, (0, 212, 255))
    img = Image.new("RGB", (500, 500), color)
    draw = ImageDraw.Draw(img)
    # Add a simple face silhouette
    draw.ellipse([150, 80, 350, 280], fill=(50, 50, 60))  # head
    draw.ellipse([190, 140, 230, 180], fill=(200, 200, 210))  # left eye
    draw.ellipse([270, 140, 310, 180], fill=(200, 200, 210))  # right eye
    draw.ellipse([220, 200, 280, 250], fill=(180, 180, 190))  # mouth
    img.save(str(output_path))
    print(f"  ✅ Placeholder généré : {output_path}")
    return True


def create_thumbnail(
    title: str,
    emotion: str,
    face_path: Path | None,
    output_path: Path,
    cfg: dict,
    accent_color: tuple = (0, 212, 255),
) -> bool:
    """Create a YouTube thumbnail with face + text + accent."""
    thumb = Image.new("RGB", (W, H), (6, 6, 14))  # dark background
    draw = ImageDraw.Draw(thumb)

    # Paste face on left 40%
    if face_path and face_path.exists():
        face = Image.open(str(face_path))
        face = face.resize((int(W * 0.42), H), Image.Resampling.LANCZOS)
        thumb.paste(face, (0, 0))
        # Add gradient overlay on right side for text readability
        gradient = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        g_draw = ImageDraw.Draw(gradient)
        for x in range(int(W * 0.35), W):
            alpha = int((x - W * 0.35) / (W * 0.65) * 200)
            g_draw.line([(x, 0), (x, H)], fill=(6, 6, 14, min(alpha, 220)))
        thumb = Image.alpha_composite(thumb.convert("RGBA"), gradient).convert("RGB")
        draw = ImageDraw.Draw(thumb)

    # Add accent bar on left edge
    draw.rectangle([0, 0, 8, H], fill=accent_color)

    # Add text on right side
    font_path = _find_font("impact")
    if font_path:
        font = ImageFont.truetype(font_path, 72)
    else:
        font = ImageFont.load_default()

    # Wrap text to max 4-6 words, 2-3 lines
    words = title.split()
    lines = []
    current_line = []
    for word in words:
        current_line.append(word)
        test = " ".join(current_line)
        if draw.textlength(test, font=font) > W * 0.55 and len(current_line) > 1:
            current_line.pop()
            lines.append(" ".join(current_line))
            current_line = [word]
    if current_line:
        lines.append(" ".join(current_line))
    lines = lines[:3]  # max 3 lines

    # Draw text with outline
    text_x = int(W * 0.45)
    text_y = H // 2 - len(lines) * 40
    for line in lines:
        # Outline
        for dx, dy in [(-2, 0), (2, 0), (0, -2), (0, 2), (-2, -2), (2, 2), (-2, 2), (2, -2)]:
            draw.text((text_x + dx, text_y + dy), line, font=font, fill=(0, 0, 0))
        # Main text
        draw.text((text_x, text_y), line, font=font, fill=(255, 255, 255))
        text_y += 80

    # Add channel badge top-right
    badge_w, badge_h = 180, 50
    badge_x, badge_y = W - badge_w - 20, 20
    draw.rounded_rectangle([badge_x, badge_y, badge_x + badge_w, badge_y + badge_h], radius=8, fill=accent_color)
    badge_font_path = _find_font("bold")
    if badge_font_path:
        bfont = ImageFont.truetype(badge_font_path, 24)
    else:
        bfont = ImageFont.load_default()
    channel_name = cfg.get("channel", {}).get("name", "Dev IA FR")
    bbox = draw.textbbox((0, 0), channel_name, font=bfont)
    tw = bbox[2] - bbox[0]
    draw.text((badge_x + (badge_w - tw) // 2, badge_y + 12), channel_name, font=bfont, fill=(0, 0, 0))

    # Save
    output_path.parent.mkdir(parents=True, exist_ok=True)
    thumb.save(str(output_path), "JPEG", quality=90)
    print(f"  ✅ Miniature créée : {output_path}")
    return True


def main():
    parser = argparse.ArgumentParser(description="Miniature YouTube avec visage IA")
    parser.add_argument("--title", required=True, help="Titre de la vidéo (4-6 mots pour la miniature)")
    parser.add_argument("--emotion", default="surprise", choices=list(EMOTION_PROMPTS.keys()), help="Émotion du visage")
    parser.add_argument("--output", type=Path, default=None, help="Fichier de sortie")
    parser.add_argument("--ab-test", action="store_true", help="Génère 2 variantes (surprise + curiosity)")
    parser.add_argument("--no-face", action="store_true", help="Sans visage (texte seulement)")
    args = parser.parse_args()

    cfg = load_config()
    accent_str = cfg.get("thumbnail", {}).get("accent_color", "#00d4ff")
    accent_color = tuple(int(accent_str[i:i+2], 16) for i in (1, 3, 5))

    print("=" * 60)
    print("Miniature YouTube avec visage IA")
    print("=" * 60)
    print(f"  Title: {args.title}")
    print(f"  Emotion: {args.emotion}")

    emotions_to_generate = [args.emotion]
    if args.ab_test:
        emotions_to_generate = [args.emotion, "curiosity"]

    for emotion in emotions_to_generate:
        output_path = args.output or THUMBNAIL_DIR / f"thumb_{emotion}.jpg"
        if len(emotions_to_generate) > 1:
            output_path = THUMBNAIL_DIR / f"thumb_{emotion}.jpg"

        if args.no_face:
            create_thumbnail(args.title, emotion, None, output_path, cfg, accent_color)
        else:
            face_path = THUMBNAIL_DIR / f"face_{emotion}.png"
            generate_face_image(emotion, face_path, cfg)
            create_thumbnail(args.title, emotion, face_path, output_path, cfg, accent_color)

    print("=" * 60)


if __name__ == "__main__":
    main()