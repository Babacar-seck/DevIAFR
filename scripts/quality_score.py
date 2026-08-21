#!/usr/bin/env python3
"""
quality_score.py — Calcule un score de qualité pour une vidéo (0-100).

Usage:
    python quality_score.py --video video.mp4 --script script.txt --thumbnail thumb.png
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


def analyze_video(video_path: str) -> dict:
    """Analyse les propriétés techniques de la vidéo."""
    cmd = [
        "ffprobe",
        "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height,r_frame_rate,bit_rate",
        "-show_entries", "format=duration",
        "-of", "json",
        video_path
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return {}
    
    import json
    data = json.loads(result.stdout)
    
    stream = data.get("streams", [{}])[0]
    format_data = data.get("format", {})
    
    return {
        "width": int(stream.get("width", 0)),
        "height": int(stream.get("height", 0)),
        "fps": eval(stream.get("r_frame_rate", "0/1")),
        "bitrate": int(stream.get("bit_rate", 0)),
        "duration": float(format_data.get("duration", 0))
    }


def score_video(video_info: dict, script_text: str, thumbnail_path: str, cfg: dict) -> dict:
    """Calcule le score de qualité (0-100)."""
    quality = cfg.get("quality", {})
    weights = quality.get("weights", {})
    min_score = quality.get("min_score", 70)
    
    scores = {}
    
    # Score technique (40%)
    tech_score = 0
    if video_info:
        # Résolution
        if video_info["width"] >= 1920 and video_info["height"] >= 1080:
            tech_score += 15
        elif video_info["width"] >= 1280 and video_info["height"] >= 720:
            tech_score += 10
        else:
            tech_score += 5
        
        # FPS
        if video_info["fps"] >= 30:
            tech_score += 10
        elif video_info["fps"] >= 24:
            tech_score += 7
        else:
            tech_score += 3
        
        # Bitrate
        if video_info["bitrate"] >= 5000000:
            tech_score += 10
        elif video_info["bitrate"] >= 2500000:
            tech_score += 7
        else:
            tech_score += 3
        
        # Durée
        if 30 <= video_info["duration"] <= 180:
            tech_score += 5
    
    scores["technical"] = tech_score
    
    # Score script (40%)
    script_score = 0
    if script_text:
        # Longueur
        word_count = len(script_text.split())
        if 150 <= word_count <= 300:
            script_score += 15
        elif 100 <= word_count <= 400:
            script_score += 10
        else:
            script_score += 5
        
        # Structure storytelling
        if "hook" in script_text.lower():
            script_score += 5
        if "problème" in script_text.lower() or "problem" in script_text.lower():
            script_score += 5
        if "conclusion" in script_text.lower() or "cta" in script_text.lower():
            script_score += 5
        
        # Qualité du contenu
        if "?" in script_text:
            script_score += 5  # Questions engageantes
        if "!" in script_text:
            script_score += 5  # Enthousiasme
    
    scores["script"] = script_score
    
    # Score thumbnail (20%)
    thumb_score = 0
    if thumbnail_path and Path(thumbnail_path).exists():
        try:
            from PIL import Image
            img = Image.open(thumbnail_path)
            
            # Résolution
            if img.width >= 1280 and img.height >= 720:
                thumb_score += 10
            elif img.width >= 640 and img.height >= 360:
                thumb_score += 7
            else:
                thumb_score += 3
            
            # Ratio
            ratio = img.width / img.height
            if 1.7 <= ratio <= 1.8:  # 16:9
                thumb_score += 10
            else:
                thumb_score += 5
        except Exception as e:
            print(f"⚠ Erreur analyse thumbnail : {e}")
            thumb_score = 5
    
    scores["thumbnail"] = thumb_score
    
    # Score total pondéré
    total = (
        scores["technical"] * weights.get("technical", 0.4) +
        scores["script"] * weights.get("script", 0.4) +
        scores["thumbnail"] * weights.get("thumbnail", 0.2)
    )
    
    return {
        "total": int(total),
        "scores": scores,
        "passed": total >= min_score,
        "min_score": min_score
    }


def main():
    parser = argparse.ArgumentParser(description="Calcule un score de qualité pour une vidéo")
    parser.add_argument("--video", required=True, help="Vidéo à analyser")
    parser.add_argument("--script", help="Fichier script")
    parser.add_argument("--thumbnail", help="Fichier thumbnail")
    parser.add_argument("--json", action="store_true", help="Sortie JSON")
    args = parser.parse_args()
    
    if not Path(args.video).exists():
        print(f"✗ Fichier vidéo introuvable : {args.video}")
        sys.exit(1)
    
    cfg = load_config()
    
    # Analyser la vidéo
    video_info = analyze_video(args.video)
    
    # Lire le script
    script_text = ""
    if args.script and Path(args.script).exists():
        script_text = Path(args.script).read_text()
    
    # Calculer le score
    result = score_video(video_info, script_text, args.thumbnail, cfg)
    
    # Afficher le résultat
    if args.json:
        import json
        print(json.dumps(result, indent=2))
    else:
        print(f"\n{'='*60}")
        print(f"Score de qualité : {result['total']}/100")
        print(f"{'='*60}")
        print(f"  Technique : {result['scores']['technical']}/40")
        print(f"  Script    : {result['scores']['script']}/40")
        print(f"  Thumbnail : {result['scores']['thumbnail']}/20")
        print(f"{'='*60}")
        
        if result["passed"]:
            print(f"✓ Score acceptable (min: {result['min_score']})")
        else:
            print(f"✗ Score insuffisant (min: {result['min_score']})")
            sys.exit(1)


if __name__ == "__main__":
    main()
