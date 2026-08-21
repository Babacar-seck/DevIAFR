#!/usr/bin/env python3
"""
repurpose.py — Découpe une vidéo longue en clips courts pour TikTok/Reels/Shorts.

Usage:
    python repurpose.py --input video.mp4 --output-dir clips/
"""

import argparse
import subprocess
import sys
from pathlib import Path

import yaml

SCRIPT_DIR = Path(__file__).parent
DEVIAFR_ROOT = SCRIPT_DIR.parent
UNIFIED_CONFIG = DEVIAFR_ROOT / "config" / "unified_config.yaml"


def load_config() -> dict:
    with open(UNIFIED_CONFIG) as f:
        return yaml.safe_load(f)


def get_video_duration(video_path: str) -> float:
    """Récupère la durée de la vidéo en secondes."""
    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        video_path
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return 0.0
    
    return float(result.stdout.strip())


def detect_silence(video_path: str, threshold: float = -30) -> list[tuple[float, float]]:
    """Détecte les moments de silence dans la vidéo."""
    cmd = [
        "ffmpeg",
        "-i", video_path,
        "-af", f"silencedetect=noise={threshold}dB:d=0.5",
        "-f", "null",
        "-"
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    # Parser la sortie pour extraire les timestamps
    silences = []
    lines = result.stderr.split("\n")
    
    start = None
    for line in lines:
        if "silence_start:" in line:
            start = float(line.split("silence_start:")[1].split()[0])
        elif "silence_end:" in line and start is not None:
            end = float(line.split("silence_end:")[1].split()[0])
            silences.append((start, end))
            start = None
    
    return silences


def extract_clip(input_video: str, output_video: str, start: float, duration: float, aspect: str = "9:16") -> bool:
    """Extrait un clip d'une vidéo avec recadrage vertical."""
    # Calculer le crop pour 9:16
    if aspect == "9:16":
        # Crop center pour format vertical
        vf = "crop=ih*9/16:ih"
    else:
        vf = "scale=1920:1080"
    
    cmd = [
        "ffmpeg", "-y",
        "-i", input_video,
        "-ss", str(start),
        "-t", str(duration),
        "-vf", vf,
        "-c:v", "libx264",
        "-preset", "fast",
        "-c:a", "aac",
        "-b:a", "128k",
        output_video
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"✗ Erreur extraction clip : {result.stderr[:200]}")
        return False
    
    return True


def repurpose_video(input_video: str, output_dir: Path, cfg: dict) -> list[str]:
    """Découpe une vidéo en clips courts."""
    repurposing = cfg.get("repurposing", {})
    
    clip_duration = repurposing.get("clip_duration_s", 30)
    max_clips = repurposing.get("max_clips", 5)
    aspect = repurposing.get("aspect_ratio", "9:16")
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Récupérer la durée totale
    total_duration = get_video_duration(input_video)
    if total_duration == 0:
        print(f"✗ Impossible de lire la durée de {input_video}")
        return []
    
    print(f"→ Durée totale : {total_duration:.1f}s")
    
    # Détecter les silences pour trouver les bons moments de coupe
    print(f"→ Détection des silences...")
    silences = detect_silence(input_video)
    print(f"  {len(silences)} silences détectés")
    
    # Générer les clips
    clips = []
    clip_count = 0
    
    # Stratégie : extraire des clips réguliers en évitant les silences
    interval = max(total_duration / (max_clips + 1), clip_duration * 2)
    
    for i in range(max_clips):
        start_time = i * interval
        
        # Vérifier qu'on n'est pas dans un silence
        in_silence = any(s[0] <= start_time <= s[1] for s in silences)
        if in_silence:
            continue
        
        # Vérifier qu'on ne dépasse pas la durée
        if start_time + clip_duration > total_duration:
            break
        
        clip_path = output_dir / f"clip_{clip_count:03d}.mp4"
        
        print(f"→ Extraction clip {clip_count + 1} : {start_time:.1f}s - {start_time + clip_duration:.1f}s")
        
        if extract_clip(input_video, str(clip_path), start_time, clip_duration, aspect):
            clips.append(str(clip_path))
            clip_count += 1
    
    print(f"\n✓ {clip_count} clips générés dans {output_dir}")
    return clips


def main():
    parser = argparse.ArgumentParser(description="Découpe une vidéo en clips courts")
    parser.add_argument("--input", required=True, help="Vidéo longue à découper")
    parser.add_argument("--output-dir", required=True, help="Dossier de sortie pour les clips")
    args = parser.parse_args()
    
    if not Path(args.input).exists():
        print(f"✗ Fichier d'entrée introuvable : {args.input}")
        sys.exit(1)
    
    cfg = load_config()
    
    clips = repurpose_video(args.input, Path(args.output_dir), cfg)
    
    if clips:
        print(f"\n{'='*60}")
        print(f"Clips générés :")
        for i, clip in enumerate(clips, 1):
            print(f"  {i}. {clip}")
        print(f"{'='*60}")
    else:
        print(f"\n✗ Aucun clip généré")
        sys.exit(1)


if __name__ == "__main__":
    main()
