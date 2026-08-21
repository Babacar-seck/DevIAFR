#!/usr/bin/env python3
"""
Analyseur de tendances YouTube et Google Trends
Génère des sujets de vidéos basés sur ce qui est tendance dans votre niche.

Usage:
    python trend_analyzer.py --persona dev_ia_fr --count 10
    python trend_analyzer.py --persona dev_ia_fr --output topics.json
"""

import argparse
import json
import sys
from pathlib import Path
from typing import List, Dict
import requests
from datetime import datetime, timedelta

# Ajouter les scripts au path
sys.path.insert(0, str(Path(__file__).parent))


class TrendAnalyzer:
    """Analyse les tendances pour générer des sujets de vidéos"""
    
    def __init__(self, persona_id: str):
        self.persona_id = persona_id
        self.persona = self._load_persona()
        
    def _load_persona(self) -> Dict:
        """Charge la configuration du persona"""
        import yaml
        persona_path = Path(__file__).parent.parent / "config" / "personas" / f"{self.persona_id}.yaml"
        
        if not persona_path.exists():
            print(f"❌ Persona non trouvé: {persona_path}")
            sys.exit(1)
        
        with open(persona_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def analyze_youtube_trends(self, max_results: int = 10) -> List[Dict]:
        """
        Analyse les vidéos tendance YouTube pour la niche du persona.
        
        Note: Nécessite une clé API YouTube Data v3.
        Pour l'instant, retourne des sujets basés sur les topics du persona.
        """
        print(f"🔍 Analyse des tendances YouTube pour {self.persona_id}...")
        
        # Extraire les topics du persona
        topics = self.persona.get('content', {}).get('topics', [])
        
        if not topics:
            print("⚠️  Aucun topic défini dans le persona")
            return []
        
        print(f"  📊 Topics trouvés: {len(topics)}")
        
        # Générer des variations de sujets basées sur les topics
        trending_topics = []
        
        for topic in topics[:max_results]:
            # Créer plusieurs variations pour chaque topic
            variations = [
                f"Les 5 erreurs fatales en {topic} que tout le monde fait",
                f"{topic} en 2024: Ce qui change tout",
                f"Pourquoi 90% des devs échouent avec {topic}",
                f"{topic}: Le guide ultime pour débutants",
                f"Comment j'ai maîtrisé {topic} en 30 jours",
                f"Les secrets de {topic} que personne ne vous dit",
                f"{topic} vs alternatives: Lequel choisir?",
                f"J'ai testé {topic} pendant 1 mois - Résultats",
            ]
            
            for variation in variations[:2]:  # 2 variations par topic
                trending_topics.append({
                    'title': variation,
                    'topic': topic,
                    'trend_score': 85,  # Score simulé
                    'source': 'persona_topics'
                })
        
        return trending_topics[:max_results]
    
    def analyze_google_trends(self, max_results: int = 10) -> List[Dict]:
        """
        Analyse Google Trends pour trouver des sujets populaires.
        
        Note: Utilise pytrends (librairie non-officielle).
        """
        print(f"📈 Analyse Google Trends pour {self.persona_id}...")
        
        try:
            from pytrends.request import TrendReq
        except ImportError:
            print("⚠️  pytrends non installé. Installation...")
            import subprocess
            subprocess.run([sys.executable, "-m", "pip", "install", "-q", "pytrends"])
            from pytrends.request import TrendReq
        
        # Extraire les keywords du persona
        keywords = self.persona.get('content', {}).get('topics', [])[:5]
        
        if not keywords:
            print("⚠️  Aucun keyword défini dans le persona")
            return []
        
        print(f"  🔑 Keywords: {', '.join(keywords)}")
        
        # Initialiser pytrends
        pytrends = TrendReq(hl='fr-FR', tz=360)
        
        trending_topics = []
        
        # Analyser chaque keyword
        for keyword in keywords:
            try:
                # Rechercher des requêtes liées
                pytrends.build_payload([keyword], timeframe='today 3-m', geo='FR')
                related_queries = pytrends.related_queries()
                
                if keyword in related_queries and related_queries[keyword]['top'] is not None:
                    top_queries = related_queries[keyword]['top'].head(3)
                    
                    for _, row in top_queries.iterrows():
                        query = row['query']
                        value = row['value']
                        
                        trending_topics.append({
                            'title': f"{query}: Le guide complet",
                            'topic': keyword,
                            'trend_score': min(100, value),
                            'source': 'google_trends',
                            'query': query
                        })
            except Exception as e:
                print(f"  ⚠️  Erreur pour {keyword}: {e}")
                continue
        
        # Trier par score de tendance
        trending_topics.sort(key=lambda x: x['trend_score'], reverse=True)
        
        return trending_topics[:max_results]
    
    def generate_video_ideas(self, count: int = 10) -> List[Dict]:
        """
        Génère des idées de vidéos basées sur les tendances.
        
        Combine:
        - Topics du persona
        - Tendances YouTube (simulé)
        - Google Trends (si disponible)
        """
        print(f"🎬 Génération de {count} idées de vidéos pour {self.persona_id}...\n")
        
        all_topics = []
        
        # 1. Analyser les topics du persona
        youtube_topics = self.analyze_youtube_trends(max_results=count // 2)
        all_topics.extend(youtube_topics)
        
        # 2. Analyser Google Trends
        google_topics = self.analyze_google_trends(max_results=count // 2)
        all_topics.extend(google_topics)
        
        # 3. Trier par score de tendance
        all_topics.sort(key=lambda x: x['trend_score'], reverse=True)
        
        # 4. Prendre les meilleurs
        best_topics = all_topics[:count]
        
        print(f"\n✅ {len(best_topics)} idées générées\n")
        
        return best_topics
    
    def save_topics(self, topics: List[Dict], output_path: str):
        """Sauvegarde les topics dans un fichier JSON"""
        output = {
            'persona_id': self.persona_id,
            'generated_at': datetime.now().isoformat(),
            'count': len(topics),
            'topics': topics
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        
        print(f"💾 Topics sauvegardés: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Analyseur de tendances pour générer des sujets de vidéos"
    )
    parser.add_argument(
        "--persona",
        required=True,
        help="ID du persona (ex: dev_ia_fr)"
    )
    parser.add_argument(
        "--count",
        type=int,
        default=10,
        help="Nombre d'idées à générer (default: 10)"
    )
    parser.add_argument(
        "--output",
        help="Chemin de sortie pour sauvegarder les topics (JSON)"
    )
    
    args = parser.parse_args()
    
    # Créer l'analyseur
    analyzer = TrendAnalyzer(args.persona)
    
    # Générer les idées
    topics = analyzer.generate_video_ideas(count=args.count)
    
    # Afficher les résultats
    print("=" * 70)
    print(f"🎬 TOP {len(topics)} IDÉES DE VIDÉOS POUR {args.persona.upper()}")
    print("=" * 70)
    
    for i, topic in enumerate(topics, 1):
        print(f"\n{i}. {topic['title']}")
        print(f"   📊 Score: {topic['trend_score']}/100")
        print(f"   🏷️  Topic: {topic['topic']}")
        print(f"   📍 Source: {topic['source']}")
    
    print("\n" + "=" * 70)
    
    # Sauvegarder si demandé
    if args.output:
        analyzer.save_topics(topics, args.output)
    
    # Retourner les topics pour utilisation programmatique
    return topics


if __name__ == "__main__":
    main()
