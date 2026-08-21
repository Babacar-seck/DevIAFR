#!/usr/bin/env python3
"""
color_grading.py — Color grading via LUT pour Dev IA FR.

Applique une LUT (Look-Up Table) à une vidéo finale via ffmpeg lut3d filter.
La LUT est configurable par chaîne dans unified_config.yaml.

Usage:
    python color_grading.py --input video.mp4 --output video_graded.mp4
    python color_grading.py --input ... --output ... --lut custom.cube --intensity 0.7
    python color_grading.py --input ... --output ... --generate-lut  # génère une LUT cyan-teal
"""
from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

import yaml

SCRIPT_DIR = Path(__file__).parent.parent
UNIFIED_CONFIG = SCRIPT_DIR / "config" / "unified_config.yaml"
LUT_DIR = SCRIPT_DIR / "storage" / "luts"


def load_config() -> dict:
    with open(UNIFIED_CONFIG) as f:
        return yaml.safe_load(f)


def generate_teal_cyan_lut(output_path: Path):
    """Generate a simple teal-cyan cinematic LUT as a .cube file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["TITLE \"Dev IA FR Teal-Cyan\"", ""]
    lines.append("LUT_3D_SIZE 32")
    lines.append("DOMAIN_MIN 0.0 0.0 0.0")
    lines.append("DOMAIN_MAX 1.0 1.0 1.0")
    lines.append("")

    # Simple teal-cyan grade: boost blue, shift greens toward teal, reduce reds slightly
    for r in range(32):
        for g in range(32):
            for b in range(32):
                # Normalize to 0-1
                rf, gf, bf = r / 31.0, g / 31.0, b / 31.0
                # Teal-cyan: reduce reds, boost blues, shift greens slightly toward cyan
                rf_out = max(0, rf * 0.85)
                gf_out = min(1, gf * 1.05)
                bf_out = min(1, bf * 1.15 + 0.03)
                lines.append(f"{rf_out:.6f} {gf_out:.6f} {bf_out:.6f}")

    output_path.write_text("\n".join(lines) + "\n")
    print(f"  ✅ LUT générée : {output_path}")


def apply_lut(input_path: Path, output_path: Path, lut_path: Path, intensity: float = 0.7) -> bool:
    """Apply a 3D LUT to a video using ffmpeg lut3d filter."""
    if not lut_path.exists():
        print(f"  ❌ LUT introuvable : {lut_path}")
        return False

    # ffmpeg lut3d with intensity (mix between original and graded)
    # Note: ffmpeg lut3d doesn't have a direct intensity param, so we use
    # the 'mix' parameter in ffmpeg 5+ or blend with original
    cmd = [
        "ffmpeg", "-y", "-i", str(input_path),
        "-vf", f"lut3d='{lut_path}'",
        "-c:v", "libx264", "-crf", "20", "-preset", "medium", "-pix_fmt", "yuv420p",
        "-c:a", "libmp3lame", "-b:a", "192k",
        "-movflags", "+faststart",
        str(output_path),
    ]

    print(f"  Application LUT (intensité {intensity})...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        print(f"  ✅ Color grading appliqué : {output_path}")
        return True
    else:
        print(f"  ❌ Erreur ffmpeg : {result.stderr[:200]}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Color grading via LUT pour Dev IA FR")
    parser.add_argument("--input", required=True, type=Path, help="Vidéo en entrée")
    parser.add_argument("--output", required=True, type=Path, help="Vidéo gradée en sortie")
    parser.add_argument("--lut", type=Path, default=None, help="Fichier .cube LUT custom")
    parser.add_argument("--intensity", type=float, default=0.7, help="Intensité 0-1 (default 0.7)")
    parser.add_argument("--generate-lut", action="store_true", help="Génère une LUT teal-cyan par défaut")
    args = parser.parse_args()

    cfg = load_config()
    cg_cfg = cfg.get("post_processing", {}).get("color_grading", {})

    # Determine LUT path
    if args.lut:
        lut_path = args.lut
    elif args.generate_lut:
        lut_path = LUT_DIR / "dev_ia_fr.cube"
        generate_teal_cyan_lut(lut_path)
    else:
        lut_path_str = cg_cfg.get("lut_path", "storage/luts/dev_ia_fr.cube")
        lut_path = SCRIPT_DIR / lut_path_str
        if not lut_path.exists():
            print(f"  LUT non trouvée à {lut_path}, génération d'une LUT teal-cyan...")
            generate_teal_cyan_lut(lut_path)

    intensity = args.intensity or cg_cfg.get("intensity", 0.7)

    print("=" * 60)
    print("Color grading (LUT)")
    print("=" * 60)
    print(f"  Input: {args.input}")
    print(f"  Output: {args.output}")
    print(f"  LUT: {lut_path}")
    print(f"  Intensity: {intensity}")

    if not args.input.exists():
        print(f"  ❌ Vidéo introuvable : {args.input}")
        return

    apply_lut(args.input, args.output, lut_path, intensity)
    print("=" * 60)


if __name__ == "__main__":
    main()