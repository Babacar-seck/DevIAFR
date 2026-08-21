#!/usr/bin/env python3
"""
cross_publish.py — Cross-platform auto (TikTok + Instagram via Upload-Post MPT).

Publie une vidéo sur TikTok + Instagram via l'API Upload-Post de MPT.
Le CTA et les hashtags sont adaptés par plateforme depuis unified_config.yaml.

Usage:
    python cross_publish.py --video output/final.mp4 --title "5 outils IA..." 
    python cross_publish.py --video ... --title ... --platforms tiktok,instagram
    python cross_publish.py --video ... --title ... --dry-run
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import yaml
import requests

SCRIPT_DIR = Path(__file__).parent.parent
UNIFIED_CONFIG = SCRIPT_DIR / "config" / "unified_config.yaml"

UPLOAD_POST_API = "https://api.upload-post.com"


def load_config() -> dict:
    with open(UNIFIED_CONFIG) as f:
        return yaml.safe_load(f)


def publish_to_platforms(
    video_path: Path,
    title: str,
    platforms: list[str],
    cfg: dict,
    dry_run: bool = False,
) -> dict:
    """Publish video to TikTok + Instagram via Upload-Post API."""
    cross_cfg = cfg.get("cross_platform", {})
    upload_post = cross_cfg.get("upload_post", {})
    api_key = upload_post.get("api_key", "")
    username = upload_post.get("username", "")

    if not api_key or not username:
        return {
            "success": False,
            "error": "Upload-Post non configuré (api_key ou username manquant dans unified_config.yaml)",
            "instructions": (
                "1. Crée un compte sur https://upload-post.com\n"
                "2. Récupère ton API key et username\n"
                "3. Édite unified_config.yaml:\n"
                "   cross_platform:\n"
                "     enabled: true\n"
                "     upload_post:\n"
                "       api_key: 'ta_cle'\n"
                "       username: 'ton_username'\n"
            ),
        }

    cta = cross_cfg.get("cta", {})
    hashtags = cross_cfg.get("hashtags", {})

    # Build per-platform title with CTA
    results = {}
    for platform in platforms:
        platform_cta = cta.get(platform, cta.get("youtube", ""))
        platform_tags = " ".join(hashtags.get(platform, []))
        platform_title = f"{title} {platform_cta} {platform_tags}".strip()
        platform_title = platform_title[:2200]  # Upload-Post limit

        if dry_run:
            results[platform] = {"success": True, "dry_run": True, "title": platform_title[:100]}
            print(f"  [DRY RUN] {platform}: {platform_title[:80]}...")
            continue

        try:
            with open(video_path, "rb") as vf:
                files = {"video": vf}
                data = [
                    ("user", username),
                    ("title", platform_title[:2200]),
                    ("privacy_level", "PUBLIC_TO_EVERYONE"),
                    ("platform[]", platform),
                ]
                headers = {"Authorization": f"Apikey {api_key}"}
                resp = requests.post(
                    f"{UPLOAD_POST_API}/api/upload",
                    headers=headers,
                    data=data,
                    files=files,
                    timeout=300,
                )
                if resp.status_code == 200:
                    results[platform] = {"success": True, "response": resp.json()}
                    print(f"  ✅ {platform}: publié")
                else:
                    results[platform] = {"success": False, "error": resp.text[:200]}
                    print(f"  ❌ {platform}: {resp.text[:100]}")
        except Exception as e:
            results[platform] = {"success": False, "error": str(e)}
            print(f"  ❌ {platform}: {e}")

    return {"success": all(r.get("success") for r in results.values()), "results": results}


def main():
    parser = argparse.ArgumentParser(description="Cross-platform publishing via Upload-Post")
    parser.add_argument("--video", required=True, type=Path, help="Chemin de la vidéo")
    parser.add_argument("--title", required=True, help="Titre de la vidéo")
    parser.add_argument("--platforms", default="tiktok,instagram", help="Plateformes (comma-separated)")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    cfg = load_config()
    platforms = [p.strip() for p in args.platforms.split(",")]

    print("=" * 60)
    print("Cross-platform publishing (Upload-Post)")
    print("=" * 60)
    print(f"  Video: {args.video}")
    print(f"  Title: {args.title}")
    print(f"  Platforms: {platforms}")

    if not args.video.exists():
        print(f"  ❌ Vidéo introuvable: {args.video}")
        return

    result = publish_to_platforms(args.video, args.title, platforms, cfg, dry_run=args.dry_run)
    print(f"\n{'='*60}")
    if result.get("success"):
        print("✅ Publication cross-platform terminée")
    elif result.get("error"):
        print(f"⚠️  {result['error']}")
        if result.get("instructions"):
            print(result["instructions"])
    else:
        print("⚠️  Certaines publications ont échoué — voir détails ci-dessus")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()