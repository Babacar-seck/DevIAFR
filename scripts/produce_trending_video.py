#!/usr/bin/env python3
"""
Pipeline de production vidéo complet avec :
- Analyse des tendances pour générer des sujets
- Clonage de voix RTVC (gratuit et local)
- Génération de scripts
- Production vidéo

Usage:
    python produce_trending_video.py --persona dev_ia_fr --count 3
    python produce_trending_video.py --persona dev_ia_fr --topic "Les 5 erreurs fatales en .NET" --dry-run
"""

import argparse
import sys
from pathlib import Path
import json

# Ajouter les scripts au path
sys.path.insert(0, str(Path(__file__).parent))

from trend_analyzer import TrendAnalyzer


def produce_video(persona_id: str, topic: str, dry_run: bool = False) -> dict:
    """
    Produit une vidéo complète pour un sujet donné.
    
    Args:
        persona_id: ID du persona
        topic: Sujet de la vidéo
        dry_run: Si True, ne génère pas la vidéo (seulement le script)
        
    Returns:
        Dict avec les informations de la vidéo produite
    """
    print(f"\n{'='*70}")
    print(f"🎬 PRODUCTION VIDÉO: {topic}")
    print(f"{'='*70}\n")
    
    # 1. Générer le script
    print("📝 Étape 1/4: Génération du script...")
    from humanize_script import generate_script
    
    script = generate_script(
        topic=topic,
        persona_id=persona_id,
        target_length=4000
    )
    
    if not script:
        print("❌ Échec de la génération du script")
        return None
    
    print(f"✅ Script généré ({len(script)} caractères)\n")
    
    if dry_run:
        print("🔍 Mode dry-run activé, arrêt ici")
        return {
            'topic': topic,
            'script': script,
            'status': 'script_only'
        }
    
    # 2. Générer l'audio avec RTVC
    print("🎤 Étape 2/4: Clonage de voix avec RTVC...")
    try:
        from voice_clone_rtvc import RTVCVoiceCloner, get_voice_sample_for_persona
        
        voice_sample = get_voice_sample_for_persona(persona_id)
        cloner = RTVCVoiceCloner(device="cpu")
        
        output_dir = Path(__file__).parent.parent / "output"
        output_dir.mkdir(exist_ok=True)
        
        audio_path = output_dir / f"{topic.replace(' ', '_')[:50]}.wav"
        cloner.clone_voice(
            text=script,
            voice_ref_path=voice_sample,
            output_path=str(audio_path)
        )
        print(f"✅ Audio généré: {audio_path}\n")
        
    except Exception as e:
        print(f"⚠️  Erreur RTVC: {e}")
        print(f"   Utilisation de la voix par défaut MPT")
        audio_path = None
    
    # 3. Générer la vidéo avec MPT
    print("🎥 Étape 3/4: Production vidéo avec MoneyPrinterTurbo...")
    
    # Sauvegarder le script temporaire
    script_file = output_dir / f"{topic.replace(' ', '_')[:50]}_script.txt"
    with open(script_file, 'w', encoding='utf-8') as f:
        f.write(script)
    
    # Lancer MPT (si disponible)
    mpt_path = Path.home() / "MyWorkProjectGithub" / "MoneyPrinterTurbo"
    if mpt_path.exists():
        print(f"  📂 MPT trouvé: {mpt_path}")
        print(f"  💡 Pour produire la vidéo, lancez:")
        print(f"     cd {mpt_path}")
        print(f"     python main.py -c config.toml -t \"{topic}\"")
        print(f"\n  Note: MPT nécessite une configuration manuelle")
    
    # 4. Résumé
    print(f"\n{'='*70}")
    print("✅ PRODUCTION TERMINÉE")
    print(f"{'='*70}")
    print(f"📊 Sujet: {topic}")
    print(f"📝 Script: {script_file}")
    if audio_path:
        print(f"🎤 Audio: {audio_path}")
    print(f"{'='*70}\n")
    
    return {
        'topic': topic,
        'script': script,
        'script_file': str(script_file),
        'audio_file': str(audio_path) if audio_path else None,
        'status': 'completed'
    }


def main():
    parser = argparse.ArgumentParser(
        description="Production vidéo avec analyse de tendances et voice cloning RTVC"
    )
    parser.add_argument(
        "--persona",
        required=True,
        help="ID du persona (ex: dev_ia_fr)"
    )
    parser.add_argument(
        "--topic",
        help="Sujet spécifique (si non fourni, utilise l'analyseur de tendances)"
    )
    parser.add_argument(
        "--count",
        type=int,
        default=1,
        help="Nombre de vidéos à produire (default: 1)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Génère seulement les scripts, pas les vidéos"
    )
    
    args = parser.parse_args()
    
    # Si pas de topic spécifique, utiliser l'analyseur de tendances
    if not args.topic:
        print(f"🔍 Analyse des tendances pour {args.persona}...\n")
        analyzer = TrendAnalyzer(args.persona)
        trending_topics = analyzer.generate_video_ideas(count=args.count)
        
        if not trending_topics:
            print("❌ Aucune tendance trouvée")
            sys.exit(1)
        
        # Produire les vidéos pour les meilleurs topics
        results = []
        for i, topic_data in enumerate(trending_topics, 1):
            print(f"\n{'='*70}")
            print(f"🎬 VIDÉO {i}/{len(trending_topics)}")
            print(f"{'='*70}")
            
            result = produce_video(
                persona_id=args.persona,
                topic=topic_data['title'],
                dry_run=args.dry_run
            )
            
            if result:
                results.append(result)
        
        # Résumé final
        print(f"\n{'='*70}")
        print(f"📊 RÉSUMÉ FINAL")
        print(f"{'='*70}")
        print(f"✅ Vidéos produites: {len(results)}/{len(trending_topics)}")
        
        for i, result in enumerate(results, 1):
            print(f"\n{i}. {result['topic']}")
            print(f"   📝 Script: {result.get('script_file', 'N/A')}")
            if result.get('audio_file'):
                print(f"   🎤 Audio: {result['audio_file']}")
        
    else:
        # Produire une vidéo pour le topic spécifique
        result = produce_video(
            persona_id=args.persona,
            topic=args.topic,
            dry_run=args.dry_run
        )
        
        if result:
            print(f"\n✅ Vidéo produite avec succès")


if __name__ == "__main__":
    main()
