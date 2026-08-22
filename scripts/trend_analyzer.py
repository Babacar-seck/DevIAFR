#!/usr/bin/env python3
"""
Analyseur de tendances YouTube et Google Trends
Génère des sujets de vidéos basés sur ce qui est tendance dans votre niche.

Usage:
    python trend_analyzer.py --persona dev_ia_fr --count 10
    python trend_analyzer.py --persona dev_ia_fr --output topics.json
"""

import argparse
import hashlib
import json
import os
import re
import sys
import time
import unicodedata
from pathlib import Path
from typing import List, Dict, Optional
import requests
from datetime import datetime, timedelta

# Ajouter les scripts au path
sys.path.insert(0, str(Path(__file__).parent))

UNIFIED_CONFIG = Path(__file__).parent.parent / "config" / "unified_config.yaml"

# Cache disque des réponses pytrends (anti-429 en usage répété).
# Sous storage/temp/ (gitignoré) pour ne jamais polluer le repo.
TREND_CACHE_PATH = Path(__file__).parent.parent / "storage" / "temp" / "trend_cache.json"
TREND_CACHE_TTL = 6 * 3600  # 6h — une tendance "3 derniers mois" ne change pas à la seconde

# Mots-outils français à exclure du découpage des topics composés.
STOPWORDS = {
    "pour", "les", "des", "avec", "une", "dans", "par", "sur", "et", "ou",
    "vs", "de", "la", "le", "en", "au", "aux", "du", "ce", "cette", "ces",
    "tout", "tous", "plus", "moins", "comment", "pourquoi", "avec",
}


def split_topic_keywords(topic: str) -> List[str]:
    """Découpe un topic composé en mots-clés atomiques exploitables par pytrends.

    Google Trends ne renvoie aucune requête associée pour des chaînes composées
    (ex. ``".NET Core / ASP.NET"``), mais fonctionne sur un mot-clé simple.
    Exemples :
      ".NET Core / ASP.NET"                     → [".NET Core", "ASP.NET"]
      "Angular / TypeScript"                    → ["Angular", "TypeScript"]
      "IA pour devs (Claude, ChatGPT, Copilot)" → ["IA", "devs", "Claude", "ChatGPT", "Copilot"]
      "DevOps / Docker / CI-CD"                 → ["DevOps", "Docker", "CI-CD"]
      "Architecture logicielle"                 → ["Architecture logicielle"]
    """
    out: List[str] = []

    # 1. Les items entre parenthèses sont des keywords indépendants
    #    (ex. "(Claude, ChatGPT, Copilot)" → 3 keywords).
    for m in re.findall(r"\(([^)]*)\)", topic):
        for kw in re.split(r"[,/]", m):
            kw = kw.strip()
            if kw:
                out.append(kw)

    # 2. Segment principal sans parenthèses, découpé sur les séparateurs composés.
    main = re.sub(r"\([^)]*\)", "", topic)
    for seg in re.split(r"[/&]", main):
        seg = seg.strip(" -–—·|")
        if not seg:
            continue
        words = [w for w in re.split(r"\s+", seg) if w.lower() not in STOPWORDS]
        if len(words) == len(re.split(r"\s+", seg)) and 1 <= len(words) <= 3:
            # Phrase courte sans mot-outil → gardée entière (ex. "Architecture logicielle")
            out.append(" ".join(words))
        else:
            # Phrase verbeuse (mot-outil détecté, ex. "IA pour devs") → mots atomiques
            out.extend(words)

    # Dédup insensible à la casse, en gardant l'ordre.
    seen: set = set()
    result: List[str] = []
    for kw in out:
        k = kw.lower()
        if k not in seen and len(kw) >= 2:
            seen.add(k)
            result.append(kw)
    return result


def _normalize(s: str) -> str:
    """Minuscules + suppression des accents (pour matcher des titres YouTube)."""
    return "".join(
        c for c in unicodedata.normalize("NFD", s.lower())
        if unicodedata.category(c) != "Mn"
    )


def load_unified_config() -> Dict:
    """Charge unified_config.yaml (nécessaire pour call_llm, indépendant du persona)."""
    import yaml
    with open(UNIFIED_CONFIG, encoding="utf-8") as f:
        return yaml.safe_load(f)


def _extract_json(raw: str) -> Dict:
    """Extrait un objet JSON d'une réponse LLM qui peut contenir des balises markdown."""
    raw = raw.strip()
    if "```" in raw:
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()
    start, end = raw.find("{"), raw.rfind("}") + 1
    return json.loads(raw[start:end])


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
    
    # ── Cache disque pytrends ────────────────────────────────────────────────
    def _load_trend_cache(self) -> Dict:
        try:
            return json.loads(TREND_CACHE_PATH.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def _save_trend_cache(self, cache: Dict):
        try:
            TREND_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
            TREND_CACHE_PATH.write_text(
                json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8"
            )
        except OSError as e:
            print(f"  ⚠️  Impossible d'écrire le cache tendances : {e}")

    def _pytrends_related_queries(
        self, pytrends, keyword: str, timeframe: str = "today 3-m", geo: str = "FR",
        max_retries: int = 3,
    ) -> Optional[List[Dict]]:
        """Appel pytrends avec backoff exponentiel + cache disque (anti-429).

        pytrends scrape sans clé API officielle et renvoie des 429 en usage
        répété à courte fenêtre : on retente avec backoff exponentiel, et on
        met en cache 6h pour ne jamais redemander deux fois le même mot-clé.
        """
        cache_key = hashlib.sha1(f"{keyword}|{timeframe}|{geo}".encode("utf-8")).hexdigest()
        cache = self._load_trend_cache()
        hit = cache.get(cache_key)
        if hit and hit.get("expires", 0) > time.time():
            print(f"    ↻ Cache hit « {keyword} » ({len(hit['queries'])} requêtes, valide {TREND_CACHE_TTL // 3600}h)")
            return hit["queries"]

        for attempt in range(max_retries + 1):
            try:
                pytrends.build_payload([keyword], timeframe=timeframe, geo=geo)
                related = pytrends.related_queries()
                df = (related or {}).get(keyword, {}).get("top")
                if df is None:
                    return None  # pas de requête associée pour ce mot-clé
                queries = [
                    {"query": str(r["query"]), "value": int(r["value"])}
                    for _, r in df.head(3).iterrows()
                ]
                cache[cache_key] = {"expires": time.time() + TREND_CACHE_TTL, "queries": queries}
                self._save_trend_cache(cache)
                return queries
            except Exception as e:
                if attempt < max_retries:
                    sleep_s = 2 ** (attempt + 1)  # 2, 4, 8 s
                    print(f"  ⏳ Erreur pytrends pour « {keyword} » — retry dans {sleep_s}s ({e})")
                    time.sleep(sleep_s)
                    continue
                raise

    def analyze_google_trends(self, max_results: int = 10) -> List[Dict]:
        """
        Analyse Google Trends pour trouver des sujets populaires.

        Note: Utilise pytrends (librairie non-officielle). Les topics composés
        du persona sont découpés en mots-clés atomiques avant l'appel, et les
        réponses sont mises en cache 6h avec backoff exponentiel (anti-429).
        """
        print(f"📈 Analyse Google Trends pour {self.persona_id}...")
        
        try:
            from pytrends.request import TrendReq
        except ImportError:
            print("⚠️  pytrends non installé. Installation...")
            import subprocess
            subprocess.run([sys.executable, "-m", "pip", "install", "-q", "pytrends"])
            from pytrends.request import TrendReq
        
        # Découper les topics composés du persona en mots-clés atomiques
        topics = self.persona.get('content', {}).get('topics', [])
        if not topics:
            print("⚠️  Aucun keyword défini dans le persona")
            return []
        
        keywords: List[str] = []
        for topic in topics:
            for kw in split_topic_keywords(topic):
                if kw not in keywords:
                    keywords.append(kw)
        keywords = keywords[:8]  # borne les appels réseau (anti-429)
        
        print(f"  🔑 Mots-clés atomiques ({len(keywords)}): {', '.join(keywords)}")
        
        # Initialiser pytrends
        pytrends = TrendReq(hl='fr-FR', tz=360)
        
        trending_topics = []
        
        # Analyser chaque mot-clé
        for keyword in keywords:
            try:
                top_queries = self._pytrends_related_queries(pytrends, keyword)
                if not top_queries:
                    continue
                for item in top_queries:
                    query, value = item["query"], item["value"]
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
    
    def analyze_youtube_data_api(self, max_results: int = 5) -> List[Dict]:
        """Tendances réelles via YouTube Data API v3 (source alternative à pytrends).

        Activée uniquement si une clé est configurée :
          - `youtube.api_key` dans config/unified_config.yaml, ou
          - variable d'environnement `YOUTUBE_API_KEY`.
        Sans clé, retourne [] (la chaîne de repli reste le persona).
        Utilise `videos.list(chart=mostPopular)` (France) filtré par la catégorie
        du persona et par correspondance des mots-clés dans les titres.
        """
        cfg = load_unified_config()
        api_key = (cfg.get("youtube", {}).get("api_key") or "").strip() or os.environ.get("YOUTUBE_API_KEY", "").strip()
        if not api_key:
            print("  ⚠️  YouTube Data API : pas de clé configurée (youtube.api_key / YOUTUBE_API_KEY) — source ignorée")
            return []

        print(f"📺 Analyse YouTube Data API pour {self.persona_id}...")

        topics = self.persona.get('content', {}).get('topics', [])
        keywords = [split_topic_keywords(t) for t in topics]
        flat = [kw for sub in keywords for kw in sub]
        if not flat:
            return []

        category_id = cfg.get("youtube", {}).get("category_id", "28")
        url = "https://www.googleapis.com/youtube/v3/videos"
        params = {
            "part": "snippet,statistics",
            "chart": "mostPopular",
            "regionCode": "FR",
            "videoCategoryId": category_id,
            "maxResults": 50,
            "key": api_key,
        }
        try:
            resp = requests.get(url, params=params, timeout=15)
            resp.raise_for_status()
            items = resp.json().get("items", [])
        except Exception as e:
            print(f"  ⚠️  Erreur YouTube Data API : {e}")
            return []

        trending_topics = []
        for item in items:
            title = item.get("snippet", {}).get("title", "")
            title_norm = _normalize(title)
            match = next((kw for kw in flat if _normalize(kw) in title_norm), None)
            if not match:
                continue
            views = int(item.get("statistics", {}).get("viewCount", 0) or 0)
            score = min(100, 5 + round(10 * (views ** 0.25)))  # échelle log, plafonné à 100
            trending_topics.append({
                'title': f"{title}: Le guide complet",
                'topic': match,
                'trend_score': score,
                'source': 'youtube_data_api',
                'query': title,
            })

        trending_topics.sort(key=lambda x: x['trend_score'], reverse=True)
        print(f"  ✓ {len(trending_topics)} tendances YouTube réelles ({len(flat)} mots-clés scrutés)")
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
    
    def generate_ai_subject(self) -> Dict:
        """Synthétise UN sujet de vidéo optimisé viralité à partir des tendances réelles.

        Le signal de tendance réel vient d'abord d'analyze_google_trends()
        (pytrends, mots-clés atomiques + cache/backoff), puis de la YouTube
        Data API si une clé est configurée, et on ne retombe sur le générateur
        de variations du persona que si aucune source réelle n'a rien renvoyé
        (indisponible / clé absente), pour ne jamais renvoyer un sujet vide.
        """
        trends = self.analyze_google_trends(max_results=8)
        if not trends:
            print("  ⚠ Google Trends indisponible — tentative YouTube Data API")
            trends = self.analyze_youtube_data_api(max_results=8)
        if not trends:
            print("  ⚠ Aucune source réelle — repli sur les topics du persona")
            trends = self.analyze_youtube_trends(max_results=8)
        if not trends:
            raise RuntimeError("Aucun signal de tendance disponible (persona sans topics ni Google Trends)")

        signals = "\n".join(
            f"- {t.get('query') or t['title']} (score tendance: {t['trend_score']}/100, thème: {t['topic']})"
            for t in trends
        )

        channel_cfg = self.persona.get("channel", {})
        niche = channel_cfg.get("niche", self.persona.get("niche", ""))
        tone = channel_cfg.get("tone", "")

        prompt = f"""Tu es un stratège viralité YouTube Shorts francophone, expert en growth hacking.

Niche de la chaîne : {niche}
Ton de la chaîne : {tone}

Voici des tendances réelles du moment (Google Trends / YouTube, France, 3 derniers mois) liées à cette niche :
{signals}

À partir de CES tendances réelles, invente UN SEUL sujet de vidéo Short (60s) avec le maximum de chances de devenir viral : accrocheur, formulé comme un titre YouTube percutant (pas une question plate), qui exploite une tendance actuelle.

Retourne UNIQUEMENT un JSON valide avec cette structure :
{{"subject": "le sujet de vidéo", "based_on_trend": "la tendance exacte utilisée", "why_viral": "1 phrase expliquant le potentiel viral"}}"""

        cfg = load_unified_config()
        from humanize_script import call_llm
        raw = call_llm(prompt, cfg, max_tokens=400, temperature=0.9)
        return _extract_json(raw)

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
