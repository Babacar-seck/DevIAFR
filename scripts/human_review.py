#!/usr/bin/env python3
"""
human_review.py — Interface de revue humaine avant publication.

Usage:
    python human_review.py --video video.mp4 --script script.txt --thumbnail thumb.png
"""

import argparse
import subprocess
import sys
from pathlib import Path

import yaml

SCRIPT_DIR = Path(__file__).parent
DEVIAFR_ROOT = SCRIPT_DIR.parent
UNIFIED_CONFIG = DEVIAFR_ROOT / "config" / "unified_config.yaml"
REVIEW_DIR = DEVIAFR_ROOT / "storage" / "review"


def load_config() -> dict:
    with open(UNIFIED_CONFIG) as f:
        return yaml.safe_load(f)


def create_review_package(video: str, script: str, thumbnail: str, channel: str) -> Path:
    """Crée un package de revue avec tous les assets."""
    import shutil
    from datetime import datetime
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    review_package = REVIEW_DIR / f"review_{timestamp}"
    review_package.mkdir(parents=True, exist_ok=True)
    
    # Copier les fichiers
    if Path(video).exists():
        shutil.copy(video, review_package / "video.mp4")
    
    if Path(script).exists():
        shutil.copy(script, review_package / "script.txt")
    
    if Path(thumbnail).exists():
        shutil.copy(thumbnail, review_package / "thumbnail.png")
    
    # Créer un fichier README
    readme = review_package / "README.txt"
    readme.write_text(f"""
PACKAGE DE REVUE - {channel}
{'='*60}

Vidéo : video.mp4
Script : script.txt
Thumbnail : thumbnail.png

INSTRUCTIONS :
1. Regarder la vidéo complète
2. Vérifier le script (orthographe, grammaire, ton)
3. Vérifier la thumbnail (lisibilité, attractivité)
4. Si OK : créer un fichier "approved.txt"
5. Si NOK : créer un fichier "rejected.txt" avec les raisons

{'='*60}
""")
    
    print(f"✓ Package de revue créé : {review_package}")
    return review_package


def wait_for_review(review_package: Path) -> bool:
    """Attend la revue humaine (polling)."""
    approved_file = review_package / "approved.txt"
    rejected_file = review_package / "rejected.txt"
    
    print(f"\n⏳ En attente de la revue humaine...")
    print(f"   Package : {review_package}")
    print(f"   Crée 'approved.txt' pour approuver")
    print(f"   Crée 'rejected.txt' pour rejeter\n")
    
    import time
    while True:
        if approved_file.exists():
            print(f"✓ Revue approuvée")
            return True
        elif rejected_file.exists():
            reasons = rejected_file.read_text()
            print(f"✗ Revue rejetée : {reasons}")
            return False
        
        time.sleep(5)


def publish_if_approved(video: str, script: str, thumbnail: str, channel: str, cfg: dict):
    """Publie la vidéo si approuvée."""
    anti_ban = cfg.get("anti_ban", {})
    
    if not anti_ban.get("human_review_required", True):
        print("⚠ Revue humaine désactivée dans unified_config.yaml")
        return
    
    # Créer le package de revue
    review_package = create_review_package(video, script, thumbnail, channel)
    
    # Attendre la revue
    approved = wait_for_review(review_package)
    
    if approved:
        print(f"\n→ Publication de la vidéo...")
        # Ici on appellerait le pipeline d'upload
        # Pour l'instant, juste un message
        print(f"✓ Vidéo prête pour publication : {video}")
    else:
        print(f"\n✗ Publication annulée")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Interface de revue humaine avant publication")
    parser.add_argument("--video", required=True, help="Vidéo à revoir")
    parser.add_argument("--script", help="Fichier script")
    parser.add_argument("--thumbnail", help="Fichier thumbnail")
    parser.add_argument("--channel", default="dev_ia_fr", help="Nom du channel")
    parser.add_argument("--auto-approve", action="store_true", help="Approuver automatiquement (test)")
    args = parser.parse_args()
    
    if not Path(args.video).exists():
        print(f"✗ Fichier vidéo introuvable : {args.video}")
        sys.exit(1)
    
    cfg = load_config()
    
    if args.auto_approve:
        print("✓ Auto-approuvé (mode test)")
        return
    
    publish_if_approved(args.video, args.script, args.thumbnail, args.channel, cfg)


if __name__ == "__main__":
    main()
