# 🎤 Échantillons de Voix pour RTVC

Ce dossier contient les échantillons de voix pour le clonage vocal avec RTVC (Real-Time Voice Cloning).

## 📋 Fichiers Requis

Pour chaque persona, vous devez créer un fichier WAV :

```
voice_samples/
├── dev_ia_fr.wav          # Pour le persona Dev IA FR
├── finance_par_age.wav    # Pour le persona Finance Par Âge
├── psy_stick_fr.wav       # Pour le persona Psy Stick FR
├── coran_lumiere_fr.wav   # Pour le persona Coran Lumière FR
├── mini_melodies_fr.wav   # Pour le persona Mini Mélodies FR
└── motivation_fr.wav      # Pour le persona Motivation FR
```

## 🎯 Spécifications

Chaque fichier doit respecter ces critères :

- **Format** : WAV (Microsoft)
- **Encodage** : Signed 16-bit PCM
- **Fréquence** : 16000 Hz
- **Canaux** : Mono
- **Durée** : 5-10 secondes
- **Contenu** : Parlez naturellement et clairement

## 📝 Comment Enregistrer

### Option 1 : Audacity (Recommandé)

1. Télécharger et installer [Audacity](https://www.audacityteam.org/)
2. Configurer le projet :
   - Project Rate : 16000 Hz
   - Channels : Mono
3. Enregistrer 5-10 secondes de votre voix
   - Parlez naturellement (ex: "Bonjour, je vais vous présenter...")
   - Évitez le bruit de fond
   - Parlez clairement
4. Exporter :
   - File → Export → Export as WAV
   - Format : WAV (Microsoft)
   - Encoding : Signed 16-bit PCM
5. Sauvegarder dans `voice_samples/{persona_id}.wav`

### Option 2 : FFmpeg (Ligne de commande)

```bash
# Enregistrer avec le microphone (macOS)
ffmpeg -f avfoundation -i ":0" -t 10 -ar 16000 -ac 1 voice_samples/dev_ia_fr.wav

# Enregistrer avec le microphone (Linux)
ffmpeg -f pulse -i default -t 10 -ar 16000 -ac 1 voice_samples/dev_ia_fr.wav

# Convertir un fichier existant
ffmpeg -i input.mp3 -ar 16000 -ac 1 voice_samples/dev_ia_fr.wav
```

### Option 3 : QuickTime Player (macOS)

1. Ouvrir QuickTime Player
2. File → New Audio Recording
3. Enregistrer 10 secondes
4. Sauvegarder en .m4a
5. Convertir avec ffmpeg :
   ```bash
   ffmpeg -i recording.m4a -ar 16000 -ac 1 voice_samples/dev_ia_fr.wav
   ```

## ✅ Vérification

Pour vérifier qu'un fichier est correct :

```bash
# Vérifier les propriétés avec ffprobe
ffprobe voice_samples/dev_ia_fr.wav

# Devrait afficher :
# - Audio: pcm_s16le, 16000 Hz, mono, s16
# - Duration: ~5-10 seconds

# Écouter le fichier
afplay voice_samples/dev_ia_fr.wav  # macOS
aplay voice_samples/dev_ia_fr.wav   # Linux
```

## 🧪 Tester RTVC

Une fois l'échantillon créé, testez-le :

```bash
cd ~/MyWorkDirectory/DevIAFR

python scripts/voice_clone_rtvc.py \
  --persona dev_ia_fr \
  --text "Bonjour et bienvenue sur Dev IA FR" \
  --output /tmp/test_rtvc.wav

# Écouter le résultat
afplay /tmp/test_rtvc.wav
```

## 💡 Conseils pour une Bonne Qualité

1. **Environnement calme** : Évitez le bruit de fond (ventilateur, clim, etc.)
2. **Microphone de qualité** : Utilisez un bon micro (pas le micro intégré du laptop si possible)
3. **Distance** : 15-20 cm du microphone
4. **Ton naturel** : Parlez comme vous parleriez normalement
5. **Contenu varié** : Dites quelques phrases différentes (pas juste "bonjour")

### Exemple de Texte à Enregistrer

```
Bonjour et bienvenue. Aujourd'hui je vais vous présenter 
un sujet qui va changer votre façon de développer. 
Restez bien jusqu'à la fin pour découvrir l'astuce 
qui fait toute la différence.
```

## 🔧 Dépannage

### "FileNotFoundError: voice_samples/dev_ia_fr.wav"

→ Créez l'échantillon de voix en suivant les instructions ci-dessus.

### Qualité audio médiocre

→ Réenregistrez avec :
- Un environnement plus calme
- Un meilleur microphone
- Une durée de 8-10 secondes (au lieu de 5)

### "Error loading audio file"

→ Vérifiez que le fichier est bien en WAV 16kHz mono :
```bash
ffprobe voice_samples/dev_ia_fr.wav
```

## 📚 Ressources

- [Documentation RTVC](../VOICE_CLONING_RTVC.md)
- [Audacity Manual](https://manual.audacityteam.org/)
- [FFmpeg Documentation](https://ffmpeg.org/documentation.html)
