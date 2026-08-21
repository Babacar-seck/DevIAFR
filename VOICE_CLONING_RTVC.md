# 🎤 Voice Cloning avec RTVC (Real-Time Voice Cloning)

RTVC remplace ElevenLabs par une solution **100% locale et gratuite** pour le clonage de voix.

## 📋 Prérequis

### 1. Installer RTVC

```bash
cd ~/MyWorkProjectGithub/Real-Time-Voice-Cloning

# Installer uv si pas déjà fait
curl -LsSf https://astral.sh/uv/install.sh | sh

# Installer les dépendances
uv sync --extra cpu  # ou --extra cuda si vous avez un GPU NVIDIA
```

### 2. Télécharger les modèles

Les modèles sont téléchargés automatiquement au premier lancement. Sinon :

```bash
cd ~/MyWorkProjectGithub/Real-Time-Voice-Cloning
uv run demo_cli.py --cpu
```

Les modèles seront dans `saved_models/default/` :
- `encoder.pt` : Crée l'embedding de voix
- `synthesizer.pt` : Génère le spectrogramme
- `vocoder.pt` : Convertit en audio

### 3. Enregistrer un échantillon de voix

Pour chaque persona, vous devez enregistrer **5-10 secondes** de votre voix :

**Avec Audacity** (recommandé) :
1. Ouvrir Audacity
2. Enregistrer 5-10 secondes de votre voix (parlez naturellement)
3. Exporter en WAV :
   - Format : WAV (Microsoft)
   - Encodage : Signed 16-bit PCM
   - Fréquence : 16000 Hz
   - Canaux : Mono
4. Sauvegarder dans `DevIAFR/voice_samples/{persona_id}.wav`

**Avec ffmpeg** :
```bash
# Enregistrer avec le microphone (macOS)
ffmpeg -f avfoundation -i ":0" -t 10 -ar 16000 -ac 1 voice_samples/dev_ia_fr.wav

# Convertir un fichier existant
ffmpeg -i input.mp3 -ar 16000 -ac 1 voice_samples/dev_ia_fr.wav
```

## 🚀 Utilisation

### Ligne de commande

```bash
cd ~/MyWorkDirectory/DevIAFR

# Avec un persona
python scripts/voice_clone_rtvc.py \
  --persona dev_ia_fr \
  --text "Bonjour, je vais vous présenter les 5 erreurs fatales en .NET" \
  --output output/test.wav

# Avec un fichier de référence direct
python scripts/voice_clone_rtvc.py \
  --voice-ref voice_samples/dev_ia_fr.wav \
  --text "Bonjour, je vais vous présenter les 5 erreurs fatales en .NET" \
  --output output/test.wav

# Avec GPU (si disponible)
python scripts/voice_clone_rtvc.py \
  --persona dev_ia_fr \
  --text "Bonjour" \
  --output output/test.wav \
  --device cuda
```

### Dans le pipeline

Le script `produce_trending_video.py` utilise automatiquement RTVC :

```bash
# Produire une vidéo avec voix clonée RTVC
python scripts/produce_trending_video.py \
  --persona dev_ia_fr \
  --topic "Les 5 erreurs fatales en .NET"
```

## 🎯 Avantages par rapport à ElevenLabs

| Critère | ElevenLabs | RTVC |
|---------|-----------|------|
| **Coût** | $5-99/mois | **Gratuit** |
| **Limite** | 10k-500k caractères/mois | **Illimité** |
| **Qualité** | Excellente | Bonne |
| **Latence** | 1-5 sec (API) | 5-30 sec (local) |
| **Confidentialité** | Données envoyées à ElevenLabs | **100% local** |
| **Dépendance** | API externe | **Aucune** |

## ⚙️ Configuration

### Dans les personas (YAML)

Mettre à jour la section `voice` pour utiliser RTVC :

```yaml
voice:
  engine: "rtvc"  # au lieu de "elevenlabs"
  voice_id: "dev_ia_fr"  # ID du persona (charge voice_samples/dev_ia_fr.wav)
  style: "conversationnel, expert"
  speed: 1.0
```

### Structure des fichiers

```
DevIAFR/
├── voice_samples/
│   ├── dev_ia_fr.wav          # Échantillon pour Dev IA FR
│   ├── finance_par_age.wav    # Échantillon pour Finance
│   └── ...
├── scripts/
│   └── voice_clone_rtvc.py    # Script de clonage
└── config/personas/
    └── dev_ia_fr.yaml         # Configuration du persona
```

## 🔧 Dépannage

### "ModuleNotFoundError: No module named 'encoder'"

```bash
# Ajouter RTVC au PYTHONPATH
export PYTHONPATH=$PYTHONPATH:$HOME/MyWorkProjectGithub/Real-Time-Voice-Cloning
```

### "FileNotFoundError: voice_samples/dev_ia_fr.wav"

Enregistrez un échantillon de voix (voir section 3 ci-dessus).

### "CUDA out of memory"

Utilisez le CPU :
```bash
python scripts/voice_clone_rtvc.py --device cpu ...
```

### Qualité audio médiocre

1. **Améliorez l'échantillon de référence** :
   - Parlez clairement et naturellement
   - Évitez le bruit de fond
   - Durée : 5-10 secondes (pas plus)
   - Format : WAV 16kHz mono

2. **Texte trop long** :
   - RTVC fonctionne mieux avec des phrases courtes
   - Découpez le script en segments de 200-300 caractères

## 📝 Exemples

### Test rapide

```bash
# Tester RTVC avec un texte simple
cd ~/MyWorkDirectory/DevIAFR

python scripts/voice_clone_rtvc.py \
  --persona dev_ia_fr \
  --text "Bonjour et bienvenue sur Dev IA FR" \
  --output /tmp/test_rtvc.wav

# Écouter le résultat
afplay /tmp/test_rtvc.wav  # macOS
# ou
aplay /tmp/test_rtvc.wav   # Linux
```

### Production complète

```bash
# Produire 5 vidéos avec analyse de tendances et voix RTVC
python scripts/produce_trending_video.py \
  --persona dev_ia_fr \
  --count 5
```

## 🚀 Prochaines étapes

1. **Enregistrez vos échantillons de voix** pour chaque persona
2. **Testez RTVC** avec des textes courts
3. **Ajustez les paramètres** dans les personas YAML
4. **Produisez votre première vidéo** avec le pipeline complet

## 📚 Ressources

- [RTVC GitHub](https://github.com/CorentinJ/Real-Time-Voice-Cloning)
- [Documentation SV2TTS](https://arxiv.org/pdf/1806.04558.pdf)
- [Exemples audio](https://www.youtube.com/watch?v=-O_hYhToKoA)
