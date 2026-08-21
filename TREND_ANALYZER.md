# 📈 Analyseur de Tendances pour Génération de Sujets

Génère automatiquement des sujets de vidéos basés sur l'analyse des tendances du marché.

## 🎯 Fonctionnalités

### 1. Analyse des Topics du Persona
- Extrait les topics définis dans le persona YAML
- Génère des variations de sujets (listes, guides, comparaisons, etc.)
- Score de tendance basé sur la popularité estimée

### 2. Analyse Google Trends (optionnel)
- Recherche les requêtes liées aux topics du persona
- Récupère les tendances des 3 derniers mois
- Score de tendance basé sur le volume de recherche

### 3. Génération d'Idées de Vidéos
- Combine les deux sources de tendances
- Trie par score de tendance
- Retourne les meilleures idées

## 🚀 Utilisation

### Ligne de commande

```bash
cd ~/MyWorkDirectory/DevIAFR

# Générer 10 idées de vidéos
python scripts/trend_analyzer.py --persona dev_ia_fr --count 10

# Sauvegarder dans un fichier JSON
python scripts/trend_analyzer.py --persona dev_ia_fr --count 10 --output trends.json

# Utiliser dans le pipeline complet
python scripts/produce_trending_video.py --persona dev_ia_fr --count 3
```

### Exemple de sortie

```
🎬 Génération de 5 idées de vidéos pour dev_ia_fr...

🔍 Analyse des tendances YouTube pour dev_ia_fr...
  📊 Topics trouvés: 5

📈 Analyse Google Trends pour dev_ia_fr...
  🔑 Keywords: .NET Core, Angular, IA pour devs, Architecture, DevOps

======================================================================
🎬 TOP 5 IDÉES DE VIDÉOS POUR DEV_IA_FR
======================================================================

1. Les 5 erreurs fatales en .NET Core que tout le monde fait
   📊 Score: 92/100
   🏷️  Topic: .NET Core / ASP.NET
   📍 Source: google_trends

2. .NET Core en 2024: Ce qui change tout
   📊 Score: 88/100
   🏷️  Topic: .NET Core / ASP.NET
   📍 Source: google_trends

3. Pourquoi 90% des devs échouent avec Angular
   📊 Score: 85/100
   🏷️  Topic: Angular / TypeScript
   📍 Source: persona_topics

4. IA pour devs: Le guide ultime pour débutants
   📊 Score: 85/100
   🏷️  Topic: IA pour devs (Claude, ChatGPT, Copilot)
   📍 Source: persona_topics

5. Comment j'ai maîtrisé Docker en 30 jours
   📊 Score: 85/100
   🏷️  Topic: DevOps / Docker / CI-CD
   📍 Source: persona_topics

======================================================================
💾 Topics sauvegardés: trends.json
```

## 📊 Sources de Tendances

### 1. Topics du Persona

Extrait de `config/personas/{persona_id}.yaml` :

```yaml
content:
  topics:
    - .NET Core / ASP.NET
    - Angular / TypeScript
    - IA pour devs (Claude, ChatGPT, Copilot)
    - Architecture logicielle
    - DevOps / Docker / CI-CD
```

**Variations générées** :
- "Les 5 erreurs fatales en {topic} que tout le monde fait"
- "{topic} en 2024: Ce qui change tout"
- "Pourquoi 90% des devs échouent avec {topic}"
- "{topic}: Le guide ultime pour débutants"
- "Comment j'ai maîtrisé {topic} en 30 jours"
- "Les secrets de {topic} que personne ne vous dit"
- "{topic} vs alternatives: Lequel choisir?"
- "J'ai testé {topic} pendant 1 mois - Résultats"

### 2. Google Trends (via pytrends)

**Requêtes liées** :
- Pour chaque topic, recherche les requêtes associées
- Récupère le volume de recherche (0-100)
- Filtre les 3 dernières mois
- Zone géographique : France

**Exemple** :
- Topic : ".NET Core"
- Requêtes liées : ".NET Core 8", "migration .NET Core", ".NET Core vs .NET Framework"
- Score : 92, 88, 85

## 🔧 Configuration

### Installation de pytrends

```bash
# pytrends est installé automatiquement par le script
# Sinon, manuellement :
pip install pytrends
```

### Limites de Google Trends

Google Trends a des limites strictes :
- **Rate limit** : ~10 requêtes/minute
- **Erreur 429** : Too Many Requests
- **Solution** : Le script gère automatiquement les erreurs et continue avec les topics du persona

### Personnalisation

Modifier les variations de sujets dans `trend_analyzer.py` :

```python
variations = [
    f"Les 5 erreurs fatales en {topic} que tout le monde fait",
    f"{topic} en 2024: Ce qui change tout",
    # ... ajoutez vos propres variations
]
```

## 🎬 Pipeline Complet

### 1. Analyser les tendances

```bash
python scripts/trend_analyzer.py \
  --persona dev_ia_fr \
  --count 10 \
  --output trends.json
```

### 2. Produire les vidéos

```bash
# Produire les 3 meilleures vidéos
python scripts/produce_trending_video.py \
  --persona dev_ia_fr \
  --count 3
```

### 3. Ou tout en une commande

```bash
# Analyser + produire automatiquement
python scripts/produce_trending_video.py \
  --persona dev_ia_fr \
  --count 5 \
  --dry-run  # Test sans produire les vidéos
```

## 📝 Format de Sortie

### JSON

```json
{
  "persona_id": "dev_ia_fr",
  "generated_at": "2026-08-21T14:30:00",
  "count": 5,
  "topics": [
    {
      "title": "Les 5 erreurs fatales en .NET Core que tout le monde fait",
      "topic": ".NET Core / ASP.NET",
      "trend_score": 92,
      "source": "google_trends",
      "query": ".NET Core 8"
    },
    {
      "title": ".NET Core en 2024: Ce qui change tout",
      "topic": ".NET Core / ASP.NET",
      "trend_score": 88,
      "source": "google_trends",
      "query": "migration .NET Core"
    }
  ]
}
```

### Utilisation Programmatique

```python
from trend_analyzer import TrendAnalyzer

# Créer l'analyseur
analyzer = TrendAnalyzer("dev_ia_fr")

# Générer les idées
topics = analyzer.generate_video_ideas(count=10)

# Utiliser les topics
for topic in topics:
    print(f"{topic['title']} (Score: {topic['trend_score']})")
```

## 🎯 Stratégie de Contenu

### Fréquence de Publication

- **Analyser les tendances** : 1x/semaine
- **Produire les vidéos** : 3-5/semaine
- **Publier** : Régulièrement (2-3x/semaine)

### Optimisation

1. **Diversifiez les sources** :
   - Topics du persona (toujours disponibles)
   - Google Trends (quand disponible)
   - YouTube Trends (futur)

2. **Variez les formats** :
   - Listes ("5 erreurs", "10 astuces")
   - Guides ("Le guide ultime")
   - Comparaisons ("X vs Y")
   - Études de cas ("J'ai testé pendant 1 mois")

3. **Testez et itérez** :
   - Analysez les performances (views, watch time)
   - Identifiez les topics qui fonctionnent
   - Ajustez les variations de sujets

## 🚀 Améliorations Futures

### À Implémenter

- [ ] **YouTube Data API** : Analyser les vidéos tendance directement
- [ ] **Reddit/HackerNews** : Détecter les discussions populaires
- [ ] **Twitter/X** : Analyser les hashtags tendance
- [ ] **SEO Tools** : Intégrer Ahrefs/SEMrush pour les keywords
- [ ] **Historique** : Sauvegarder les tendances pour éviter les doublons
- [ ] **A/B Testing** : Tester plusieurs titres pour le même topic

### Exemple : YouTube Data API

```python
# Futur : Analyser les vidéos tendance YouTube
from googleapiclient.discovery import build

youtube = build('youtube', 'v3', developerKey=API_KEY)

response = youtube.search().list(
    part='snippet',
    q='.NET Core',
    order='viewCount',
    publishedAfter='2024-01-01T00:00:00Z',
    maxResults=10
).execute()

for video in response['items']:
    title = video['snippet']['title']
    views = video['statistics']['viewCount']
    print(f"{title} ({views} vues)")
```

## 📚 Ressources

- [Google Trends](https://trends.google.com)
- [pytrends Documentation](https://github.com/GeneralMills/pytrends)
- [YouTube Data API](https://developers.google.com/youtube/v3)
- [SEO Keyword Research](https://ahrefs.com/blog/keyword-research/)
