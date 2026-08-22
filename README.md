# DevIAFR - Système de Production Vidéo Automatisé

Pipeline complet de production vidéo YouTube pour développeurs (.NET/Angular) utilisant MoneyPrinterTurbo (MPT) et TestShortYoutube (TST).

## 🎯 Vue d'ensemble

Ce système automatise la production de vidéos YouTube de haute qualité en combinant :
- **MPT** : Génération vidéo de base (stock footage, TTS, sous-titres)
- **TST** : Post-processing avancé (SFX, color grading, quality control)
- **DevIAFR** : Orchestration et unification des deux pipelines

## 📁 Structure du projet

```
DevIAFR/
├── config/
│   └── unified_config.yaml      # Configuration unifiée MPT+TST
├── scripts/
│   ├── sync_config.py           # Synchronise unified_config → MPT/TST
│   ├── test_voice.py            # Test des voix ElevenLabs
│   ├── humanize_script.py       # Humanisation + storytelling
│   ├── unified_pipeline.py      # Pipeline principal unifié
│   ├── whisper_subtitles.py     # Sous-titres Whisper large-v3
│   ├── sfx_designer.py          # Sound design (SFX + ducking)
│   ├── color_grading.py           # Color grading (LUT)
│   ├── intro_outro.py           # Intro/outro animés
│   ├── quality_score.py         # Score qualité (0-100)
│   ├── human_review.py          # Revue humaine obligatoire
│   ├── cross_publish.py        # Publication multi-plateforme
│   ├── repurpose.py             # Repurposing (long→shorts)
│   ├── analytics_loop.py        # Analytics + apprentissage
│   └── produce_first_10_videos.sh  # Script de production initial
├── storage/
│   ├── output/                  # Vidéos finales
│   ├── voice_samples/           # Échantillons de voix
│   ├── thumbnails/              # Miniatures générées
│   ├── sfx/                     # Effets sonores
│   ├── luts/                    # LUTs de color grading
│   └── quality_reports/         # Rapports de qualité
└── README.md                    # Ce fichier
```

## 🚀 Installation et configuration

### 1. Prérequis

- Python 3.11+
- FFmpeg
- Ollama (avec modèle gemma4:latest)
- MoneyPrinterTurbo installé dans `~/MyWorkProjectGithub/MoneyPrinterTurbo`
- TestShortYoutube installé dans `~/MyWorkDirectory/TestShortYoutube`

### 2. Configuration des voix ElevenLabs

**CRITIQUE** : Ne jamais utiliser de voix ElevenLabs gratuite (détection automatique → démonétisation).

1. Créer un compte ElevenLabs (plan Creator $22/mois minimum)
2. Voice Design → créer "TechDev FR" (homme, 25-35 ans, français natif)
3. Récupérer `api_key` et `voice_id`
4. Éditer `config/unified_config.yaml` :

```yaml
tts:
  elevenlabs:
    api_key: "votre_api_key"
    voice_id: "votre_voice_id"
```

### 3. Synchroniser les configurations

```bash
# Preview des changements
python scripts/sync_config.py --dry-run

# Appliquer les changements
python scripts/sync_config.py
```

Cela propage automatiquement les paramètres vers MPT (`config.toml`) et TST (`config.yaml`).

### 4. Tester la voix

```bash
# Test avec Edge TTS (gratuit, pour validation)
python scripts/test_voice.py

# Test avec ElevenLabs (une fois configuré)
python scripts/test_voice.py --text "Bonjour, ceci est un test de voix custom"
```

## 🎬 Production de vidéos

### Production manuelle (étape par étape)

```bash
# 1. Générer le script humanisé
python scripts/humanize_script.py \
  --subject "Comment créer une API REST .NET" \
  --output storage/output/script.txt

# 2. Produire la vidéo avec MPT
cd ~/MyWorkProjectGithub/MoneyPrinterTurbo
.venv/bin/python webui.py
# Utiliser l'API ou le WebUI avec le script généré

# 3. Post-processing (une fois la vidéo prête)
cd ~/MyWorkDirectory/DevIAFR

# Sous-titres Whisper
python scripts/whisper_subtitles.py \
  --input storage/output/video.mp4 \
  --output storage/output/video_subtitled.mp4 \
  --srt storage/output/subtitles.srt

# Sound design
python scripts/sfx_designer.py \
  --input storage/output/video_subtitled.mp4 \
  --output storage/output/video_sfx.mp4 \
  --ducking

# Color grading
python scripts/color_grading.py \
  --input storage/output/video_sfx.mp4 \
  --output storage/output/video_graded.mp4

# Intro/Outro
python scripts/intro_outro.py \
  --input storage/output/video_graded.mp4 \
  --output storage/output/video_final.mp4 \
  --channel dev_ia_fr

# Quality score
python scripts/quality_score.py \
  --video storage/output/video_final.mp4 \
  --script storage/output/script.txt \
  --thumbnail storage/thumbnails/thumb.png

# Revue humaine
python scripts/human_review.py \
  --video storage/output/video_final.mp4 \
  --script storage/output/script.txt \
  --thumbnail storage/thumbnails/thumb.png \
  --channel dev_ia_fr
```

### Production automatisée (script batch)

```bash
# Production des 10 premières vidéos
./scripts/produce_first_10_videos.sh

# Mode dry-run (test sans production)
./scripts/produce_first_10_videos.sh --dry-run
```

### Publication multi-plateforme

```bash
# TikTok + Instagram
python scripts/cross_publish.py \
  --video storage/output/video_final.mp4 \
  --title "Comment créer une API REST .NET"

# TikTok uniquement
python scripts/cross_publish.py \
  --video storage/output/video_final.mp4 \
  --title "Comment créer une API REST .NET" \
  --platforms tiktok
```

### Repurposing (long → shorts)

```bash
# Découper une vidéo longue en 5 clips de 30s
python scripts/repurpose.py \
  --input storage/output/video_final.mp4 \
  --output-dir storage/output/clips/

# Publier les clips sur TikTok/Reels
for clip in storage/output/clips/clip_*.mp4; do
  python scripts/cross_publish.py \
    --video "$clip" \
    --title "Extrait : API REST .NET" \
    --platforms tiktok
done
```

### Analytics et apprentissage

```bash
# Récupérer les analytics YouTube
python scripts/analytics_loop.py --channel dev_ia_fr

# Les résultats sont sauvegardés dans storage/analytics/
# et utilisés pour ajuster les prompts de génération
```

## 🎨 Pipeline de production complet

```
┌─────────────────────────────────────────────────────────────┐
│ 1. SCRIPT GENERATION                                        │
│    humanize_script.py → script.txt                          │
│    (Storytelling: Hook → Problème → Solution → CTA)         │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. VIDEO PRODUCTION (MPT)                                   │
│    MoneyPrinterTurbo → video.mp4                            │
│    (Stock footage + TTS + sous-titres de base)              │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. POST-PROCESSING (TST)                                    │
│    whisper_subtitles.py → sous-titres précis                │
│    sfx_designer.py → effets sonores + ducking               │
│    color_grading.py → color grading (LUT)                     │
│    intro_outro.py → branding                                │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. QUALITY CONTROL                                          │
│    quality_score.py → score 0-100                           │
│    human_review.py → validation manuelle                    │
│    (Rejet automatique si score < 70)                        │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. PUBLICATION                                              │
│    cross_publish.py → YouTube + TikTok + Instagram         │
│    repurpose.py → clips courts                              │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 6. ANALYTICS & LEARNING                                     │
│    analytics_loop.py → feedback pour améliorer les scripts  │
└─────────────────────────────────────────────────────────────┘
```

## ⚠️ Règles anti-ban (CRITIQUE)

1. **Voix ElevenLabs** : Toujours utiliser une voix custom (jamais de voix gratuite)
2. **Humanisation** : Toujours humaniser les scripts LLM (anecdotes, émotions, exemples)
3. **Revue humaine** : Toujours valider manuellement avant publication
4. **Rythme de publication** : Maximum 3 vidéos/jour, espacées de 4+ heures
5. **Métadonnées** : Titres/descriptions uniques, jamais de spam keywords

## 🔧 Configuration avancée

### unified_config.yaml

Fichier de configuration central qui contrôle tout le système :

```yaml
projects:
  mpt:
    path: "~/MyWorkProjectGithub/MoneyPrinterTurbo"
  tst:
    path: "~/MyWorkDirectory/TestShortYoutube"

channel:
  name: "Dev IA FR"
  niche: "Développement .NET/Angular pour développeurs francophones"
  target_audience: "Développeurs intermédiaires (2-5 ans d'expérience)"

tts:
  elevenlabs:
    api_key: "..."
    voice_id: "..."

script:
  storytelling:
    structure: "Hook (5s) → Problème (10s) → Solution (30s) → CTA (5s)"
  
quality:
  min_score: 70
  weights:
    technical: 0.3
    content: 0.4
    engagement: 0.3
```

### Synchronisation automatique

Après modification de `unified_config.yaml` :

```bash
python scripts/sync_config.py
```

Cela propage automatiquement les changements vers :
- MPT : `config.toml` (LLM, TTS, vidéo, sous-titres)
- TST : `config.yaml` (profils, qualité, publication)

## 📊 Monitoring et analytics

### Rapports de qualité

Chaque vidéo génère un rapport dans `storage/quality_reports/` :
- Score technique (résolution, codec, loudness)
- Score contenu (structure, humanisation, exemples)
- Score engagement (hook, CTA, storytelling)

### Analytics YouTube

```bash
python scripts/analytics_loop.py --channel dev_ia_fr
```

Génère :
- `storage/analytics/analytics_dev_ia_fr_YYYYMMDD.json` : données brutes
- `storage/analytics/summary_dev_ia_fr_YYYYMMDD.txt` : résumé lisible

Les insights sont automatiquement intégrés dans les prochains scripts via `humanize_script.py`.

## 🐛 Dépannage

### "Model 'gemini-3.5-flash-lite' not found"

```bash
# Vérifier les modèles Ollama disponibles
ollama list

# Utiliser un modèle disponible (ex: gemma4:latest)
# Éditer config/unified_config.yaml → llm.humanizer_model
```

### "No module named 'requests'"

```bash
# Utiliser le venv de MPT
~/MyWorkProjectGithub/MoneyPrinterTurbo/.venv/bin/python scripts/...
```

### "Whisper non installé"

```bash
# Installer Whisper
pip install openai-whisper
```

### "MPT API non accessible"

```bash
# Démarrer MPT
cd ~/MyWorkProjectGithub/MoneyPrinterTurbo
.venv/bin/python webui.py
# L'API sera disponible sur http://localhost:8501
```

## 📈 Prochaines étapes

1. **Configurer ElevenLabs** : Créer la voix custom "TechDev FR"
2. **Tester le pipeline** : `./scripts/produce_first_10_videos.sh --dry-run`
3. **Produire la première vidéo** : Suivre le workflow manuel étape par étape
4. **Publier** : `python scripts/cross_publish.py --video ... --title ...`
5. **Analyser** : `python scripts/analytics_loop.py --channel dev_ia_fr`
6. **Itérer** : Ajuster les scripts basé sur les analytics

## 🎯 Objectifs de monétisation

- **1000 abonnés** : ~3-6 mois avec 3 vidéos/semaine
- **4000 heures de watch time** : ~6-9 mois
- **Revenus publicitaires** : $500-2000/mois une fois monétisé
- **Sponsoring** : Possible dès 5000 abonnés ($200-1000/vidéo)

## 📚 Ressources

- [MoneyPrinterTurbo](https://github.com/harry0703/MoneyPrinterTurbo) - Moteur de production vidéo
- [TestShortYoutube](https://github.com/Babacar-seck/TestShortYoutube) - Pipeline de qualité
- [ElevenLabs](https://elevenlabs.io) - TTS premium
- [Ollama](https://ollama.ai) - LLM local
- [Whisper](https://github.com/openai/whisper) - Transcription audio

## 📝 Licence

Ce projet est privé et confidentiel. Ne pas distribuer.

---

**Dernière mise à jour** : 21 août 2026
**Version** : 1.0.0
**Statut** : Prêt pour production
