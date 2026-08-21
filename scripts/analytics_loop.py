#!/usr/bin/env python3
"""
analytics_loop.py — Récupère les analytics YouTube et ajuste les prompts.

Usage:
    python analytics_loop.py --channel dev_ia_fr
"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime, timedelta

import yaml

SCRIPT_DIR = Path(__file__).parent
DEVIAFR_ROOT = SCRIPT_DIR.parent
UNIFIED_CONFIG = DEVIAFR_ROOT / "config" / "unified_config.yaml"
ANALYTICS_DIR = DEVIAFR_ROOT / "storage" / "analytics"


def load_config() -> dict:
    with open(UNIFIED_CONFIG) as f:
        return yaml.safe_load(f)


def get_youtube_analytics(channel: str, cfg: dict) -> dict:
    """Récupère les analytics YouTube via l'API."""
    analytics_cfg = cfg.get("analytics", {})
    
    if not analytics_cfg.get("enabled", False):
        print("⚠ Analytics désactivé dans unified_config.yaml")
        return {}
    
    # Pour l'instant, on simule des données
    # Dans une vraie implémentation, on utiliserait l'API YouTube Data v3
    print("→ Récupération des analytics YouTube...")
    
    # Simuler des données
    return {
        "videos": [
            {"id": "video1", "title": "Titre 1", "views": 1500, "watch_time": 45, "engagement": 0.12},
            {"id": "video2", "title": "Titre 2", "views": 800, "watch_time": 30, "engagement": 0.08},
            {"id": "video3", "title": "Titre 3", "views": 2200, "watch_time": 60, "engagement": 0.15},
        ],
        "channel_stats": {
            "subscribers": 150,
            "total_views": 4500,
            "avg_watch_time": 45
        }
    }


def analyze_performance(analytics: dict) -> dict:
    """Analyse les performances et identifie les patterns."""
    videos = analytics.get("videos", [])
    
    if not videos:
        return {}
    
    # Trier par views
    sorted_by_views = sorted(videos, key=lambda v: v["views"], reverse=True)
    
    # Top performers
    top_3 = sorted_by_views[:3]
    
    # Calculer les moyennes
    avg_views = sum(v["views"] for v in videos) / len(videos)
    avg_watch_time = sum(v["watch_time"] for v in videos) / len(videos)
    avg_engagement = sum(v["engagement"] for v in videos) / len(videos)
    
    # Identifier les patterns dans les top performers
    patterns = []
    for video in top_3:
        title = video["title"].lower()
        
        # Détecter les mots-clés
        if "comment" in title or "tutorial" in title:
            patterns.append("how-to")
        if "?" in video["title"]:
            patterns.append("question")
        if any(word in title for word in ["top", "best", "meilleur"]):
            patterns.append("listicle")
    
    return {
        "top_videos": top_3,
        "avg_views": int(avg_views),
        "avg_watch_time": int(avg_watch_time),
        "avg_engagement": avg_engagement,
        "patterns": list(set(patterns))
    }


def adjust_prompts(analysis: dict, cfg: dict) -> dict:
    """Ajuste les prompts basés sur les performances."""
    patterns = analysis.get("patterns", [])
    
    # Ajustements basés sur les patterns
    adjustments = {}
    
    if "how-to" in patterns:
        adjustments["script_style"] = "Focus sur les tutoriels step-by-step"
    
    if "question" in patterns:
        adjustments["hook_style"] = "Commencer par une question engageante"
    
    if "listicle" in patterns:
        adjustments["format"] = "Format top 5/10 fonctionne bien"
    
    # Ajuster le watch time
    avg_watch_time = analysis.get("avg_watch_time", 0)
    if avg_watch_time < 30:
        adjustments["pacing"] = "Rythme trop lent, accélérer les intros"
    elif avg_watch_time > 50:
        adjustments["pacing"] = "Bon rythme, maintenir"
    
    return adjustments


def save_analytics_report(analytics: dict, analysis: dict, adjustments: dict, channel: str):
    """Sauvegarde un rapport d'analytics."""
    ANALYTICS_DIR.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = ANALYTICS_DIR / f"analytics_{channel}_{timestamp}.json"
    
    report = {
        "timestamp": timestamp,
        "channel": channel,
        "analytics": analytics,
        "analysis": analysis,
        "adjustments": adjustments
    }
    
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Rapport sauvegardé : {report_path}")
    
    # Aussi sauvegarder un résumé lisible
    summary_path = ANALYTICS_DIR / f"summary_{channel}_{timestamp}.txt"
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write(f"RAPPORT ANALYTICS - {channel}\n")
        f.write(f"{'='*60}\n\n")
        
        f.write(f"Stats channel :\n")
        channel_stats = analytics.get("channel_stats", {})
        f.write(f"  Abonnés : {channel_stats.get('subscribers', 0)}\n")
        f.write(f"  Vues totales : {channel_stats.get('total_views', 0)}\n")
        f.write(f"  Watch time moyen : {channel_stats.get('avg_watch_time', 0)}s\n\n")
        
        f.write(f"Top 3 vidéos :\n")
        for i, video in enumerate(analysis.get("top_videos", []), 1):
            f.write(f"  {i}. {video['title']} ({video['views']} vues, {video['watch_time']}s)\n")
        
        f.write(f"\nPatterns détectés : {', '.join(analysis.get('patterns', []))}\n\n")
        
        f.write(f"Ajustements recommandés :\n")
        for key, value in adjustments.items():
            f.write(f"  - {key}: {value}\n")
    
    print(f"✓ Résumé sauvegardé : {summary_path}")


def main():
    parser = argparse.ArgumentParser(description="Récupère les analytics YouTube et ajuste les prompts")
    parser.add_argument("--channel", default="dev_ia_fr", help="Nom du channel")
    parser.add_argument("--json", action="store_true", help="Sortie JSON")
    args = parser.parse_args()
    
    cfg = load_config()
    
    # Récupérer les analytics
    analytics = get_youtube_analytics(args.channel, cfg)
    
    if not analytics:
        print("✗ Aucune donnée analytics")
        sys.exit(1)
    
    # Analyser les performances
    analysis = analyze_performance(analytics)
    
    # Ajuster les prompts
    adjustments = adjust_prompts(analysis, cfg)
    
    # Sauvegarder le rapport
    save_analytics_report(analytics, analysis, adjustments, args.channel)
    
    # Afficher le résumé
    if args.json:
        print(json.dumps({
            "analysis": analysis,
            "adjustments": adjustments
        }, indent=2, ensure_ascii=False))
    else:
        print(f"\n{'='*60}")
        print(f"ANALYTICS LOOP - {args.channel}")
        print(f"{'='*60}")
        print(f"\nTop vidéos :")
        for video in analysis.get("top_videos", []):
            print(f"  • {video['title']} ({video['views']} vues)")
        
        print(f"\nMoyennes :")
        print(f"  Vues : {analysis.get('avg_views', 0)}")
        print(f"  Watch time : {analysis.get('avg_watch_time', 0)}s")
        print(f"  Engagement : {analysis.get('avg_engagement', 0):.2%}")
        
        print(f"\nPatterns : {', '.join(analysis.get('patterns', []))}")
        
        print(f"\nAjustements :")
        for key, value in adjustments.items():
            print(f"  • {key}: {value}")
        
        print(f"{'='*60}")


if __name__ == "__main__":
    main()
