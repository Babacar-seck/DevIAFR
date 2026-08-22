# 🚀 DevIAFR — Guide de Démarrage Rapide

## Table des Matières

1. [Installation](#installation)
2. [Configuration](#configuration)
3. [Utilisation](#utilisation)
4. [Personas](#personas)
5. [Structure du Projet](#structure-du-projet)
6. [Dépannage](#dépannage)
7. [SaaS Multi-Tenant](#saas-multi-tenant)

---

## Installation

### Prérequis

- **Python 3.10+**
- **FFmpeg** (traitement vidéo)
- **Ollama** (LLM local, optionnel)
- **Compte ElevenLabs** (voix IA)
- **Compte Alibaba Cloud** (Qwen API)

### 1. Cloner le projet

```bash
cd ~/MyWorkDirectory
git clone https://github.com/Babacar-seck/TestShortYoutube.git
cd TestShortYoutube
```

### 2. Installer les dépendances

```bash
# Créer l'environnement virtuel
python3 -m venv .venv
source .venv/bin/activate

# Installer les packages
pip install -r requirements.txt
```

### 3. Installer MoneyPrinterTurbo (MPT)

```bash
cd ~/MyWorkProjectGithub
git clone https://github.com/harry0703/MoneyPrinterTurbo.git
cd MoneyPrinterTurbo

# Créer venv séparé pour MPT
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Vérifier l'installation
python webui.py
# Ouvrir http://localhost:8501 dans le navigateur
```

### 4. Vérifier l'environnement

```bash
cd ~/MyWorkDirectory/DevIAFR
./run.sh --check
```

Résultat attendu :
```
[✓] Python 3.10+
[✓] FFmpeg installé
[✓] MPT venv trouvé
[✓] Hermes .env trouvé
[✓] Config unified_config.yaml
[✓] 6 personas disponibles
```

---

## Configuration

### 1. Configurer les clés API

Créer `~/.hermes/.env` :

```bash
# Alibaba Cloud (Qwen)
DASHSCOPE_API_KEY=sk-your-dashscope-key

# ElevenLabs (voix IA)
ELEVENLABS_API_KEY=your-elevenlabs-key

# YouTube (optionnel, pour upload auto)
YOUTUBE_CLIENT_ID=your-client-id
YOUTUBE_CLIENT_SECRET=your-client-secret
YOUTUBE_REFRESH_TOKEN=your-refresh-token
```

### 2. Configurer le pipeline

Éditer `config/unified_config.yaml` :

```yaml
# LLM Provider
llm:
  provider: "alibaba"  # ou "ollama", "gemini"
  model: "qwen3.7-max"
  temperature: 0.7
  max_tokens: 4000

# Voix IA
voice:
  engine: "elevenlabs"  # ou "edge_tts" (gratuit)
  voice_id: "your-voice-id"  # Voir ElevenLabs Voice Library

# Qualité
quality:
  min_score: 70  # Score minimum 0-100
```

### 3. Créer une voix ElevenLabs (recommandé)

1. Aller sur https://elevenlabs.io/voice-library
2. Choisir une voix "Professional" ou "Narrative"
3. Copier le `voice_id`
4. Coller dans `config/unified_config.yaml`

---

## Utilisation

### Mode Interactif (recommandé pour débuter)

```bash
cd ~/MyWorkDirectory/DevIAFR
./run.sh
```

Le script vous demandera :
1. **Persona** : Choisir parmi les 6 personas disponibles
2. **Sujet** : Entrer le sujet de la vidéo
3. **Confirmation** : Lancer la production

### Mode Direct

```bash
# Produire une vidéo tech
./run.sh --persona dev_ia_fr --subject "Les 5 erreurs fatales en architecture .NET"

# Produire une vidéo finance
./run.sh --persona finance_par_age --subject "Comment investir à 25 ans avec 100€/mois"

# Mode test (sans produire de vidéo)
./run.sh --persona psy_stick_fr --subject "Pourquoi 90% des gens procrastinent" --dry-run
```

### Lister les personas

```bash
./run.sh --list-personas
```

### Pipeline complet (avancé)

```bash
# 1. Charger le persona
python scripts/select_persona.py --persona dev_ia_fr --merge --output config/active_config.yaml

# 2. Générer le script
python scripts/humanize_script.py --subject "Sujet vidéo" --output storage/scripts/script.txt

# 3. Produire la vidéo
python scripts/unified_pipeline.py --script storage/scripts/script.txt

# 4. Post-processing
python scripts/color_grading.py --input output/video.mp4 --output output/graded.mp4
python scripts/quality_score.py --video output/graded.mp4 --script storage/scripts/script.txt

# 5. Upload (optionnel)
python scripts/youtube_uploader.py --video output/graded.mp4 --title "Titre" --description "Description"
```

---

## Personas

### Personas Disponibles

| ID | Niche | CPM | Public |
|---|---|---|---|
| `dev_ia_fr` | Tech/AI pour devs | $15-30 | Développeurs .NET/Angular |
| `finance_par_age` | Finance personnelle | $8-20 | Jeunes actifs 25-35 ans |
| `psy_stick_fr` | Psychologie | $4-10 | Grand public 20-40 ans |
| `coran_lumiere_fr` | Spiritualité | $2-5 | Communauté musulmane FR |
| `mini_melodies_fr` | Enfants | $1-3 | Parents 25-40 ans |
| `motivation_fr` | Motivation | $3-8 | Entrepreneurs, étudiants |

### Créer un Nouveau Persona

1. **Copier un template** :
```bash
cp config/personas/dev_ia_fr.yaml config/personas/mon_persona.yaml
```

2. **Éditer la configuration** :
```yaml
name: "Mon Persona"
id: "mon_persona"
niche: "Ma niche"
language: "fr"

tone: "conversationnel, expert"
structure:
  - hook: "Question provocatrice"
  - problem: "Pourquoi c'est important"
  - solution: "3 étapes concrètes"
  - cta: "Abonne-toi"

visual_style:
  primary_color: "#FF6B6B"
  secondary_color: "#4ECDC4"
  font: "Montserrat Bold"
```

3. **Tester** :
```bash
./run.sh --persona mon_persona --subject "Test" --dry-run
```

### Structure d'un Persona

```yaml
# Identité
name: "Nom du persona"
id: "identifiant_unique"
niche: "Description de la niche"
language: "fr"

# Ton et style
tone: "description du ton"
structure:
  - hook: "type d'accroche"
  - problem: "type de problème"
  - solution: "type de solution"
  - cta: "type d'appel à l'action"

# Visuel
visual_style:
  primary_color: "#hex"
  secondary_color: "#hex"
  font: "nom police"
  
# Voix
voice:
  engine: "elevenlabs"
  voice_id: "id_voix"
  style: "narrative"

# Qualité
quality:
  min_score: 70
```

---

## Structure du Projet

```
DevIAFR/
├── run.sh                      # Point d'entrée principal
├── README.md                   # Documentation (ce fichier)
│
├── config/
│   ├── unified_config.yaml     # Configuration globale
│   └── personas/               # Personas personnalisables
│       ├── dev_ia_fr.yaml
│       ├── finance_par_age.yaml
│       ├── psy_stick_fr.yaml
│       ├── coran_lumiere_fr.yaml
│       ├── mini_melodies_fr.yaml
│       └── motivation_fr.yaml
│
├── scripts/
│   ├── select_persona.py       # Sélection de persona
│   ├── humanize_script.py      # Humanisation + storytelling
│   ├── unified_pipeline.py     # Pipeline de production
│   ├── color_grading.py        # Color grading
│   ├── quality_score.py        # Score qualité
│   ├── intro_outro.py          # Ajout intro/outro
│   ├── sfx_designer.py         # Design sonore
│   ├── whisper_subtitles.py    # Sous-titres auto
│   ├── repurpose.py            # Repurposing (long → shorts)
│   ├── cross_publish.py        # Multi-plateforme
│   ├── analytics_loop.py       # Analytics feedback
│   └── youtube_uploader.py     # Upload YouTube
│
├── storage/
│   ├── scripts/                # Scripts générés
│   ├── output/                 # Vidéos produites
│   ├── thumbnails/             # Miniatures
│   └── branding/               # Assets (logo, intro, outro)
│
├── docs/
│   ├── PERSONA_GUIDE.md        # Guide détaillé personas
│   ├── SAAS_PERSONAS.md        # Architecture SaaS
│   └── RUNBOOK.md              # Ce fichier
│
└── .github/
    └── workflows/
        └── ci.yml              # Tests automatiques
```

---

## Dépannage

### Erreur : "MPT venv non trouvé"

**Solution** : Installer MoneyPrinterTurbo
```bash
cd ~/MyWorkProjectGithub
git clone https://github.com/harry0703/MoneyPrinterTurbo.git
cd MoneyPrinterTurbo
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Erreur : "DASHSCOPE_API_KEY non défini"

**Solution** : Créer `~/.hermes/.env`
```bash
echo "DASHSCOPE_API_KEY=sk-your-key" > ~/.hermes/.env
```

### Erreur : "FFmpeg non trouvé"

**Solution** : Installer FFmpeg
```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt-get install ffmpeg

# Windows
choco install ffmpeg
```

### Erreur : "Persona non trouvé"

**Solution** : Lister les personas disponibles
```bash
./run.sh --list-personas
```

### Vidéo de mauvaise qualité (score < 70)

**Solutions** :
1. Augmenter la qualité du script :
```yaml
# config/unified_config.yaml
llm:
  temperature: 0.5  # Réduire pour plus de cohérence
  max_tokens: 6000  # Augmenter pour plus de détail
```

2. Améliorer le prompt d'humanisation :
```bash
# Éditer scripts/humanize_script.py
# Ajouter des instructions spécifiques au persona
```

3. Activer le color grading :
```bash
python scripts/color_grading.py --input video.mp4 --output graded.mp4
```

### MPT ne démarre pas

**Solution** : Vérifier les ports
```bash
# MPT utilise les ports 8080 (API) et 8501 (WebUI)
lsof -i :8080
lsof -i :8501

# Tuer les processus bloquants
kill -9 <PID>
```

---

## SaaS Multi-Tenant

### Architecture

```
Client → API FastAPI → PostgreSQL → Queue Celery → Workers
                ↓
         Stripe (Paiements)
                ↓
         YouTube Upload
```

### Déploiement Production

1. **Base de données** :
```bash
# PostgreSQL
docker run -d --name deviafr-db \
  -e POSTGRES_PASSWORD=secret \
  -e POSTGRES_DB=deviafr \
  -p 5432:5432 \
  postgres:15

# Redis (queue)
docker run -d --name deviafr-redis \
  -p 6379:6379 \
  redis:7
```

2. **API FastAPI** :
```bash
cd api
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```

3. **Workers Celery** :
```bash
celery -A api.tasks worker --loglevel=info --concurrency=4
```

4. **Frontend Next.js** :
```bash
cd frontend
npm install
npm run build
npm start
```

### Plans SaaS

| Plan | Prix | Vidéos/mois | Features |
|---|---|---|---|
| Free | $0 | 5 | Scripts + voix, pas de vidéo |
| Pro | $49 | 50 | Vidéos 1080p, upload auto |
| Enterprise | $199 | 200 | 4K, API illimitée, support |

### API Endpoints

```bash
# Créer un persona
POST /api/personas
{
  "name": "Mon Persona",
  "niche": "Tech",
  "config": {...}
}

# Générer une vidéo
POST /api/videos
{
  "persona_id": "uuid",
  "subject": "Sujet vidéo"
}

# Télécharger la vidéo
GET /api/videos/{id}/download

# Analytics
GET /api/analytics?persona_id=uuid
```

---

## Support

- **Documentation** : `docs/PERSONA_GUIDE.md`, `docs/SAAS_PERSONAS.md`
- **Issues** : https://github.com/Babacar-seck/TestShortYoutube/issues
- **Email** : contact@deviafr.com

---

## Roadmap

- [x] Pipeline unifié (MPT + TST)
- [x] Système multi-personas
- [x] Humanisation + storytelling
- [x] Color grading automatique
- [x] Score qualité
- [ ] API SaaS complète
- [ ] Dashboard utilisateur
- [ ] Paiements Stripe
- [ ] A/B testing thumbnails
- [ ] Analytics temps réel

---

**Version** : 2.0.0  
**Dernière mise à jour** : 2026-01-22  
**Auteur** : Babacar Seck
