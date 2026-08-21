#!/usr/bin/env python3
"""
color_grade.py — Applique un color grading (LUT) à une vidéo.

Usage:
    python color_grade.py --input video.mp4 --output graded.mp4 --channel dev_ia_fr
    python color_grade.py --input video.mp4 --lut custom.cube --output graded.mp4
"""

import argparse
import subprocess
import sys
from pathlib import Path

import yaml

SCRIPT_DIR = Path(__file__).parent
DEVIAFR_ROOT = SCRIPT_DIR.parent
UNIFIED_CONFIG = DEVIAFR_ROOT / "config" / "unified_config.yaml"
LUTS_DIR = DEVIAFR_ROOT / "storage" / "luts"


def load_config() -> dict:
    with open(UNIFIED_CONFIG) as f:
        return yaml.safe_load(f)


def get_lut_for_channel(channel: str, cfg: dict) -> Path | None:
    """Récupère le chemin de la LUT pour un channel donné."""
    post_processing = cfg.get("post_processing", {})
    color_grading = post_processing.get("color_grading", {})
    channel_luts = color_grading.get("channel_luts", {})

    lut_name = channel_luts.get(channel)
    if not lut_name:
        return None

    lut_path = LUTS_DIR / lut_name
    if not lut_path.exists():
        print(f"⚠ LUT non trouvée : {lut_path}")
        return None

    return lut_path


def apply_lut(input_path: str, lut_path: str, output_path: str) -> bool:
    """Applique une LUT 3D à une vidéo via ffmpeg."""
    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-vf", f"lut3d={lut_path}",
        "-c:a", "copy",
        "-preset", "medium",
        "-crf", "18",
        output_path
    ]

    print(f"→ Application LUT : {Path(lut_path).name}")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"✗ Erreur ffmpeg : {result.stderr[:200]}")
        return False

    print(f"✓ Color grading appliqué : {output_path}")
    return True


def main():
    parser = argparse.ArgumentParser(description="Applique un color grading (LUT) à une vidéo")
    parser.add_argument("--input", required=True, help="Vidéo d'entrée")
    parser.add_argument("--output", required=True, help="Vidéo de sortie")
    parser.add_argument("--channel", default="dev_ia_fr", help="Nom du channel (pour LUT automatique)")
    parser.add_argument("--lut", help="Chemin LUT custom (override --channel)")
    args = parser.parse_args()

    if not Path(args.input).exists():
        print(f"✗ Fichier d'entrée introuvable : {args.input}")
        sys.exit(1)

    cfg = load_config()

    # Déterminer la LUT à utiliser
    if args.lut:
        lut_path = Path(args.lut)
        if not lut_path.exists():
            print(f"✗ LUT custom introuvable : {args.lut}")
            sys.exit(1)
    else:
        lut_path = get_lut_for_channel(args.channel, cfg)
        if not lut_path:
            print(f"⚠ Aucune LUT configurée pour le channel '{args.channel}'")
            print(f"  → Copie sans color grading")
            # Copie simple
            subprocess.run(["cp", args.input, args.output], check=True)
            return

    # Appliquer la LUT
    success = apply_lut(args.input, str(lut_path), args.output)
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
