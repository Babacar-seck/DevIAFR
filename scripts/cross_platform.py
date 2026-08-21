#!/usr/bin/env python3
"""
cross_platform.py — Publie une vidéo sur TikTok et Instagram via Upload-Post MPT.

Usage:
    python cross_platform.py --video video.mp4 --title "Titre" --channel dev_ia_fr
"""

import argparse
import subprocess
import sys
from pathlib import Path

import yaml

SCRIPT_DIR = Path(__file__).parent
DEVIAFR_ROOT = SCRIPT_DIR.parent
UNIFIED_CONFIG = DEVIAFR_ROOT / "config" / "unified_config.yaml"
MPT_PATH = None


def load_config() -> dict:
    with open(UNIFIED_CONFIG) as f:
        return yaml.safe_load(f)


def get_mpt_path(cfg: dict) -> Path:
    """Récupère le chemin de MPT."""
    global MPT_PATH
    if MPT_PATH is None:
        mpt_cfg = cfg.get("projects", {}).get("mpt", {})
        MPT_PATH = Path(mpt_cfg.get("path", "~/MyWorkProjectGithub/MoneyPrinterTurbo")).expanduser()
    return MPT_PATH


def publish_tiktok(video_path: str, title: str, cfg: dict) -> bool:
    """Publie sur TikTok via Upload-Post MPT."""
    mpt_path = get_mpt_path(cfg)
    upload_post = mpt_path / "upload_post.py"
    
    if not upload_post.exists():
        print(f"✗ Upload-Post MPT introuvable : {upload_post}")
        return False
    
    cross_platform = cfg.get("cross_platform", {})
    tiktok_cfg = cross_platform.get("tiktok", {})
    
    if not tiktok_cfg.get("enabled", False):
        print("⚠ TikTok désactivé dans unified_config.yaml")
        return False
    
    cmd = [
        "python", str(upload_post),
        "--platform", "tiktok",
        "--video", video_path,
        "--title", title,
        "--description", tiktok_cfg.get("description", ""),
    ]
    
    print(f"→ Publication TikTok : {title}")
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(mpt_path))
    
    if result.returncode != 0:
        print(f"✗ Erreur TikTok : {result.stderr[:200]}")
        return False
    
    print(f"✓ Publié sur TikTok")
    return True


def publish_instagram(video_path: str, title: str, cfg: dict) -> bool:
    """Publie sur Instagram via Upload-Post MPT."""
    mpt_path = get_mpt_path(cfg)
    upload_post = mpt_path / "upload_post.py"
    
    if not upload_post.exists():
        print(f"✗ Upload-Post MPT introuvable : {upload_post}")
        return False
    
    cross_platform = cfg.get("cross_platform", {})
    instagram_cfg = cross_platform.get("instagram", {})
    
    if not instagram_cfg.get("enabled", False):
        print("⚠ Instagram désactivé dans unified_config.yaml")
        return False
    
    cmd = [
        "python", str(upload_post),
        "--platform", "instagram",
        "--video", video_path,
        "--title", title,
        "--description", instagram_cfg.get("description", ""),
    ]
    
    print(f"→ Publication Instagram : {title}")
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(mpt_path))
    
    if result.returncode != 0:
        print(f"✗ Erreur Instagram : {result.stderr[:200]}")
        return False
    
    print(f"✓ Publié sur Instagram")
    return True


def main():
    parser = argparse.ArgumentParser(description="Publie une vidéo sur TikTok et Instagram")
    parser.add_argument("--video", required=True, help="Vidéo à publier")
    parser.add_argument("--title", required=True, help="Titre de la vidéo")
    parser.add_argument("--channel", default="dev_ia_fr", help="Nom du channel")
    parser.add_argument("--tiktok-only", action="store_true", help="Publier uniquement sur TikTok")
    parser.add_argument("--instagram-only", action="store_true", help="Publier uniquement sur Instagram")
    args = parser.parse_args()
    
    if not Path(args.video).exists():
        print(f"✗ Fichier vidéo introuvable : {args.video}")
        sys.exit(1)
    
    cfg = load_config()
    
    success_count = 0
    
    # Publier sur TikTok
    if not args.instagram_only:
        if publish_tiktok(args.video, args.title, cfg):
            success_count += 1
    
    # Publier sur Instagram
    if not args.tiktok_only:
        if publish_instagram(args.video, args.title, cfg):
            success_count += 1
    
    if success_count > 0:
        print(f"\n✓ {success_count} publication(s) réussie(s)")
    else:
        print(f"\n✗ Aucune publication réussie")
        sys.exit(1)


if __name__ == "__main__":
    main()
