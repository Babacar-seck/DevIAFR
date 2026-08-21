# 🎭 Guide rapide : Utiliser les Personas

## Commandes de base

### Lister tous les personas disponibles
```bash
python scripts/select_persona.py --list
```

### Charger un persona
```bash
# Afficher la config du persona
python scripts/select_persona.py --persona dev_ia_fr

# Fusionner avec unified_config.yaml
python scripts/select_persona.py --persona finance_par_age --merge

# Sauvegarder la config fusionnée
python scripts/select_persona.py --persona psy_stick_fr --merge --output config/final_config.yaml
```

## Produire une vidéo avec un persona

### Méthode 1 : Utiliser le script batch
```bash
# Éditer le script pour utiliser le bon persona
nano scripts/produce_first_10_videos.sh

# Changer la ligne PERSONA_ID
PERSONA_ID="finance_par_age"  # ou "psy_stick_fr", "coran_lumiere_fr", etc.

# Lancer la production
./scripts/produce_first_10_videos.sh --dry-run  # test
./scripts/produce_first_10_videos.sh            # production
```

### Méthode 2 : Pipeline manuel
```bash
# 1. Charger le persona
python scripts/select_persona.py --persona motivation_fr --merge --output config/active_config.yaml

# 2. Générer le script
python scripts/humanize_script.py \
  --subject "Comment rester motivé pendant 30 jours" \
  --output storage/scripts/motivation_script.txt

# 3. Produire la vidéo (MPT)
cd ~/MyWorkProjectGithub/MoneyPrinterTurbo
python main.py --config ~/MyWorkDirectory/DevIAFR/config/active_config.yaml

# 4. Post-processing
cd ~/MyWorkDirectory/DevIAFR
python scripts/color_grade.py --input output/video.mp4 --output output/graded.mp4 --persona motivation_fr
python scripts/quality_score.py --video output/graded.mp4 --script storage/scripts/motivation_script.txt
python scripts/human_review.py --video output/graded.mp4 --script storage/scripts/motivation_script.txt
python scripts/cross_platform.py --video output/graded.mp4 --script storage/scripts/motivation_script.txt
```

## Créer un nouveau persona

### 1. Copier un template
```bash
cp config/personas/dev_ia_fr.yaml config/personas/mon_persona.yaml
```

### 2. Éditer les champs essentiels
```yaml
name: "Mon Nouveau Persona"
id: "mon_persona"

channel:
  name: "Ma Chaîne"
  handle: "@machaine"
  niche: "Ma niche spécifique"
  language: "fr"

branding:
  colors:
    primary: "#ff6b9d"  # Couleur principale
    secondary: "#4ecdc4" # Couleur secondaire

voice:
  engine: "elevenlabs"
  voice_id: "my_custom_voice_id"  # Créer sur ElevenLabs
  style: "confiant, direct"

script:
  storytelling:
    structure:
      - name: "Hook"
        duration_pct: 5
        description: "Question choc"
      # ... adapter la structure

content:
  topics:
    - "Sujet 1"
    - "Sujet 2"
  format: "short-form (60s)"  # ou "long-form (8-12min)"
```

### 3. Tester
```bash
python scripts/select_persona.py --list  # Vérifier qu'il apparaît
python scripts/select_persona.py --persona mon_persona --merge --output test_config.yaml
```

## Personas pré-configurés

| ID | Usage | CPM estimé |
|---|---|---|
| `dev_ia_fr` | Tech/AI pour devs .NET/Angular | $15-30 |
| `finance_par_age` | Conseils financiers par tranche d'âge | $8-20 |
| `psy_stick_fr` | Psychologie avec animations stick figure | $4-10 |
| `coran_lumiere_fr` | Récitation + explication Coran | $2-5 |
| `mini_melodies_fr` | Chansons éducatives pour enfants | $1-3 |
| `motivation_fr` | Motivation quotidienne | $3-8 |

## Intégration SaaS (API)

Pour exposer via API REST (multi-tenant) :

```bash
# Démarrer l'API FastAPI
uvicorn api.main:app --reload --port 8000

# Endpoints disponibles
POST /personas          # Créer un persona
GET /personas           # Lister ses personas
POST /videos/generate   # Générer une vidéo
GET /videos/{id}        # Suivre la production
POST /videos/{id}/upload  # Publier sur YouTube
```

Voir `SAAS_PERSONAS.md` pour l'architecture complète.
