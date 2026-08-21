#!/usr/bin/env python3
"""
whisper_subtitles.py — Génère des sous-titres SRT avec Whisper large-v3.

Usage:
    python whisper_subtitles.py --input video.mp4 --output subtitles.srt
"""

import argparse
import subprocess
import sys
from pathlib import Path

import yaml

SCRIPT_DIR = Path(__file__).parent
DEVIAFR_ROOT = SCRIPT_DIR.parent
UNIFIED_CONFIG = DEVIAFR_ROOT / "config" / "unified_config.yaml"
MODELS_DIR = DEVIAFR_ROOT / "storage" / "models"


def load_config() -> dict:
    with open(UNIFIED_CONFIG) as f:
        return yaml.safe_load(f)


def generate_subtitles(input_video: str, output_srt: str, cfg: dict) -> bool:
    """Génère des sous-titres SRT avec Whisper."""
    subtitles_cfg = cfg.get("subtitles", {})
    whisper_cfg = subtitles_cfg.get("whisper", {})
    
    model = whisper_cfg.get("model", "large-v3")
    language = whisper_cfg.get("language", "fr")
    device = whisper_cfg.get("device", "cpu")
    
    # Vérifier que whisper est disponible
    try:
        import whisper
    except ImportError:
        print("✗ Whisper non installé. Installer avec: pip install openai-whisper")
        return False
    
    print(f"→ Chargement du modèle Whisper {model}...")
    model = whisper.load_model(model, device=device)
    
    print(f"→ Transcription de {input_video}...")
    result = model.transcribe(
        input_video,
        language=language,
        verbose=False
    )
    
    # Générer le fichier SRT
    with open(output_srt, "w", encoding="utf-8") as f:
        for i, segment in enumerate(result["segments"], 1):
            start = segment["start"]
            end = segment["end"]
            text = segment["text"].strip()
            
            # Formater les timestamps SRT
            start_h = int(start // 3600)
            start_m = int((start % 3600) // 60)
            start_s = start % 60
            start_str = f"{start_h:02d}:{start_m:02d}:{start_s:06.3f}".replace(".", ",")
            
            end_h = int(end // 3600)
            end_m = int((end % 3600) // 60)
            end_s = end % 60
            end_str = f"{end_h:02d}:{end_m:02d}:{end_s:06.3f}".replace(".", ",")
            
            f.write(f"{i}\n")
            f.write(f"{start_str} --> {end_str}\n")
            f.write(f"{text}\n\n")
    
    print(f"✓ Sous-titres générés : {output_srt}")
    return True


def burn_subtitles(video_path: str, srt_path: str, output_path: str, cfg: dict) -> bool:
    """Incruste les sous-titres dans la vidéo."""
    subtitles_cfg = cfg.get("subtitles", {})
    style = subtitles_cfg.get("style", {})
    
    font_name = style.get("font_name", "Arial-Bold.ttf")
    font_size = style.get("font_size", 24)
    primary_color = style.get("primary_color", "#FFFFFF")
    outline_color = style.get("outline_color", "#000000")
    outline = style.get("outline", 2)
    
    # Convertir les couleurs en format ASS
    primary_color = primary_color.replace("#", "&H00")
    outline_color = outline_color.replace("#", "&H00")
    
    # Force style
    force_style = f"FontName={font_name},FontSize={font_size},PrimaryColour={primary_color},OutlineColour={outline_color},Outline={outline}"
    
    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-vf", f"subtitles={srt_path}:force_style='{force_style}'",
        "-c:a", "copy",
        "-preset", "medium",
        "-crf", "18",
        output_path
    ]
    
    print(f"→ Incrustation des sous-titres...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"✗ Erreur ffmpeg : {result.stderr[:200]}")
        return False
    
    print(f"✓ Sous-titres incrustés : {output_path}")
    return True


def main():
    parser = argparse.ArgumentParser(description="Génère et incruste des sous-titres avec Whisper")
    parser.add_argument("--input", required=True, help="Vidéo d'entrée")
    parser.add_argument("--output", required=True, help="Vidéo de sortie (avec sous-titres)")
    parser.add_argument("--srt", help="Fichier SRT (si déjà existant)")
    parser.add_argument("--no-burn", action="store_true", help="Générer uniquement le SRT, sans incruster")
    args = parser.parse_args()
    
    if not Path(args.input).exists():
        print(f"✗ Fichier d'entrée introuvable : {args.input}")
        sys.exit(1)
    
    cfg = load_config()
    
    # Générer ou utiliser le SRT existant
    if args.srt:
        srt_path = args.srt
    else:
        srt_path = Path(args.input).stem + ".srt"
        if not generate_subtitles(args.input, srt_path, cfg):
            sys.exit(1)
    
    # Incruster si demandé
    if not args.no_burn:
        if not burn_subtitles(args.input, srt_path, args.output, cfg):
            sys.exit(1)
    else:
        print(f"✓ Sous-titres SRT uniquement : {srt_path}")


if __name__ == "__main__":
    main()
