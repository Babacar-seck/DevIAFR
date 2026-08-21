#!/usr/bin/env python3
"""
intro_outro.py — Génère et ajoute une intro/outro à une vidéo.

Usage:
    python intro_outro.py --input video.mp4 --output final.mp4 --channel dev_ia_fr
"""

import argparse
import subprocess
import sys
from pathlib import Path

import yaml

SCRIPT_DIR = Path(__file__).parent
DEVIAFR_ROOT = SCRIPT_DIR.parent
UNIFIED_CONFIG = DEVIAFR_ROOT / "config" / "unified_config.yaml"
ASSETS_DIR = DEVIAFR_ROOT / "storage" / "assets"


def load_config() -> dict:
    with open(UNIFIED_CONFIG) as f:
        return yaml.safe_load(f)


def generate_intro(channel: str, cfg: dict) -> Path:
    """Génère une intro vidéo pour le channel."""
    branding = cfg.get("branding", {})
    intro = branding.get("intro", {})
    
    if not intro.get("enabled", False):
        return None
    
    # Vérifier si l'intro existe déjà
    intro_path = ASSETS_DIR / f"{channel}_intro.mp4"
    if intro_path.exists():
        return intro_path
    
    # Générer une intro procédurale avec ffmpeg
    duration = intro.get("duration", 3)
    text = intro.get("text", channel)
    bg_color = branding.get("primary_color", "#000000")
    text_color = "#FFFFFF"
    
    # Créer un clip texte animé
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", f"color=c={bg_color}:s=1920x1080:d={duration}",
        "-vf", f"drawtext=text='{text}':fontcolor={text_color}:fontsize=72:x=(w-text_w)/2:y=(h-text_h)/2",
        "-t", str(duration),
        "-c:v", "libx264",
        "-preset", "fast",
        str(intro_path)
    ]
    
    print(f"→ Génération de l'intro pour {channel}...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"✗ Erreur génération intro : {result.stderr[:200]}")
        return None
    
    print(f"✓ Intro générée : {intro_path}")
    return intro_path


def generate_outro(channel: str, cfg: dict) -> Path:
    """Génère une outro vidéo pour le channel."""
    branding = cfg.get("branding", {})
    outro = branding.get("outro", {})
    
    if not outro.get("enabled", False):
        return None
    
    # Vérifier si l'outro existe déjà
    outro_path = ASSETS_DIR / f"{channel}_outro.mp4"
    if outro_path.exists():
        return outro_path
    
    # Générer une outro procédurale
    duration = outro.get("duration", 5)
    text = outro.get("text", "Abonnez-vous !")
    bg_color = branding.get("primary_color", "#000000")
    text_color = "#FFFFFF"
    
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", f"color=c={bg_color}:s=1920x1080:d={duration}",
        "-vf", f"drawtext=text='{text}':fontcolor={text_color}:fontsize=60:x=(w-text_w)/2:y=(h-text_h)/2",
        "-t", str(duration),
        "-c:v", "libx264",
        "-preset", "fast",
        str(outro_path)
    ]
    
    print(f"→ Génération de l'outro pour {channel}...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"✗ Erreur génération outro : {result.stderr[:200]}")
        return None
    
    print(f"✓ Outro générée : {outro_path}")
    return outro_path


def concat_videos(videos: list[str], output: str) -> bool:
    """Concatène plusieurs vidéos avec ffmpeg."""
    # Créer un fichier liste
    list_file = Path(output).stem + "_list.txt"
    with open(list_file, "w") as f:
        for video in videos:
            f.write(f"file '{video}'\n")
    
    cmd = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", list_file,
        "-c", "copy",
        output
    ]
    
    print(f"→ Concaténation de {len(videos)} vidéos...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    # Nettoyer
    Path(list_file).unlink(missing_ok=True)
    
    if result.returncode != 0:
        print(f"✗ Erreur concaténation : {result.stderr[:200]}")
        return False
    
    print(f"✓ Vidéos concaténées : {output}")
    return True


def main():
    parser = argparse.ArgumentParser(description="Ajoute une intro/outro à une vidéo")
    parser.add_argument("--input", required=True, help="Vidéo principale")
    parser.add_argument("--output", required=True, help="Vidéo finale (avec intro/outro)")
    parser.add_argument("--channel", default="dev_ia_fr", help="Nom du channel")
    parser.add_argument("--no-intro", action="store_true", help="Ne pas ajouter d'intro")
    parser.add_argument("--no-outro", action="store_true", help="Ne pas ajouter d'outro")
    args = parser.parse_args()
    
    if not Path(args.input).exists():
        print(f"✗ Fichier d'entrée introuvable : {args.input}")
        sys.exit(1)
    
    cfg = load_config()
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    
    videos_to_concat = []
    
    # Générer et ajouter l'intro
    if not args.no_intro:
        intro_path = generate_intro(args.channel, cfg)
        if intro_path:
            videos_to_concat.append(str(intro_path))
    
    # Ajouter la vidéo principale
    videos_to_concat.append(args.input)
    
    # Générer et ajouter l'outro
    if not args.no_outro:
        outro_path = generate_outro(args.channel, cfg)
        if outro_path:
            videos_to_concat.append(str(outro_path))
    
    # Concaténer
    if len(videos_to_concat) == 1:
        # Pas d'intro/outro, juste copier
        subprocess.run(["cp", args.input, args.output], check=True)
        print(f"✓ Pas d'intro/outro, copie simple : {args.output}")
    else:
        if not concat_videos(videos_to_concat, args.output):
            sys.exit(1)


if __name__ == "__main__":
    main()
