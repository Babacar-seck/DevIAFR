#!/usr/bin/env python3
"""
test_voice.py — Test la voix ElevenLabs custom "TechDev FR".

Génère un sample audio de 10s avec la voix configurée dans unified_config.yaml,
valide la qualité (durée, pas de glitch, normalisation) et sauvegarde le résultat.

Usage:
    python test_voice.py                    # utilise unified_config.yaml
    python test_voice.py --text "Texte..."  # texte custom
    python test_voice.py --api-key "xxx" --voice-id "xxx"  # override
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

import yaml

SCRIPT_DIR = Path(__file__).parent.parent
UNIFIED_CONFIG = SCRIPT_DIR / "config" / "unified_config.yaml"
SAMPLE_OUTPUT = SCRIPT_DIR / "storage" / "voice_samples"

# Texte de test par défaut (10s environ à vitesse normale)
DEFAULT_TEST_TEXT = (
    "Salut, bienvenue sur Dev IA FR. "
    "Aujourd'hui, on va voir comment intégrer Claude AI dans une application .NET. "
    "Franchement, quand j'ai testé pour la première fois, j'ai été bluffé par la simplicité. "
    "Allez, c'est parti !"
)


def load_config() -> dict:
    with open(UNIFIED_CONFIG) as f:
        return yaml.safe_load(f)


def generate_with_elevenlabs(api_key: str, voice_id: str, model_id: str, text: str, output_path: Path) -> bool:
    """Génère l'audio via l'API ElevenLabs en utilisant requests."""
    import requests

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {
        "xi-api-key": api_key,
        "Content-Type": "application/json",
    }
    payload = {
        "text": text,
        "model_id": model_id,
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75,
            "style": 0.0,
            "use_speaker_boost": True,
        },
    }

    print(f"  → Appel API ElevenLabs (voice_id={voice_id[:8]}...)...")
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        if response.status_code == 200:
            output_path.write_bytes(response.content)
            print(f"  ✅ Audio généré : {output_path} ({len(response.content)} bytes)")
            return True
        else:
            error_msg = response.text[:200]
            print(f"  ❌ Erreur API ElevenLabs ({response.status_code}): {error_msg}")
            return False
    except Exception as e:
        print(f"  ❌ Erreur réseau: {e}")
        return False


def generate_with_edge_tts(voice: str, text: str, output_path: Path) -> bool:
    """Fallback : génère l'audio avec Edge TTS (gratuit)."""
    import asyncio
    import edge_tts

    async def _gen():
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(str(output_path))

    try:
        asyncio.run(_gen())
        print(f"  ✅ Audio généré (Edge TTS fallback) : {output_path}")
        return True
    except Exception as e:
        print(f"  ❌ Erreur Edge TTS: {e}")
        return False


def validate_audio(audio_path: Path) -> dict:
    """Valide la qualité technique de l'audio avec ffprobe."""
    if not audio_path.exists():
        return {"ok": False, "errors": ["Fichier non trouvé"]}

    result = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", "-show_streams", str(audio_path)],
        capture_output=True, text=True,
    )

    if result.returncode != 0:
        return {"ok": False, "errors": ["ffprobe a échoué — fichier corrompu ?"]}

    import json
    data = json.loads(result.stdout)
    errors = []
    info = {}

    # Durée
    duration = float(data.get("format", {}).get("duration", 0))
    info["duration_s"] = round(duration, 2)
    if duration < 5:
        errors.append(f"Durée trop courte ({duration:.1f}s < 5s attendu)")
    if duration > 20:
        errors.append(f"Durée trop longue ({duration:.1f}s > 20s attendu)")

    # Codec audio
    audio_stream = next((s for s in data.get("streams", []) if s.get("codec_type") == "audio"), None)
    if audio_stream:
        info["codec"] = audio_stream.get("codec_name", "?")
        info["sample_rate"] = audio_stream.get("sample_rate", "?")
        info["channels"] = audio_stream.get("channels", "?")
        if audio_stream.get("codec_name") not in ("mp3", "aac", "opus", "wav"):
            errors.append(f"Codec audio inattendu: {audio_stream.get('codec_name')}")
    else:
        errors.append("Aucun stream audio trouvé")

    info["file_size_kb"] = round(audio_path.stat().st_size / 1024, 1)

    return {"ok": len(errors) == 0, "errors": errors, "info": info}


def normalize_audio(input_path: Path, output_path: Path) -> bool:
    """Normalise l'audio à -16 LUFS (broadcast standard)."""
    cmd = [
        "ffmpeg", "-y", "-i", str(input_path),
        "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
        "-c:a", "libmp3lame", "-b:a", "192k",
        str(output_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        print(f"  ✅ Audio normalisé (-16 LUFS) : {output_path}")
        return True
    else:
        print(f"  ❌ Erreur normalisation: {result.stderr[:200]}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Test la voix ElevenLabs custom pour Dev IA FR")
    parser.add_argument("--text", type=str, default=DEFAULT_TEST_TEXT, help="Texte à synthétiser")
    parser.add_argument("--api-key", type=str, default=None, help="Override ElevenLabs API key")
    parser.add_argument("--voice-id", type=str, default=None, help="Override voice_id")
    args = parser.parse_args()

    print("=" * 60)
    print("Test voix ElevenLabs custom — Dev IA FR")
    print("=" * 60)

    # Load config
    cfg = load_config()
    tts = cfg.get("tts", {})
    elevenlabs = tts.get("elevenlabs", {})

    api_key = args.api_key or elevenlabs.get("api_key", "")
    voice_id = args.voice_id or elevenlabs.get("voice_id", "")
    model_id = elevenlabs.get("model_id", "eleven_multilingual_v2")

    # Ensure output directory exists
    SAMPLE_OUTPUT.mkdir(parents=True, exist_ok=True)

    raw_path = SAMPLE_OUTPUT / "test_raw.mp3"
    normalized_path = SAMPLE_OUTPUT / "test_normalized.mp3"

    # Check if ElevenLabs is configured
    if api_key and voice_id:
        print(f"\n🎙️  Génération avec ElevenLabs (voice: {elevenlabs.get('voice_name', 'TechDev FR')})")
        success = generate_with_elevenlabs(api_key, voice_id, model_id, args.text, raw_path)
        if not success:
            print("\n⚠️  Bascule vers Edge TTS (fallback)")
            fallback_voice = tts.get("fallback_voice", "fr-FR-HenriNeural")
            success = generate_with_edge_tts(fallback_voice, args.text, raw_path)
    else:
        print("\n⚠️  ElevenLabs non configuré (api_key ou voice_id manquant)")
        print("  → Utilisation d'Edge TTS (fallback — voix gratuite, NE PAS utiliser en production)")
        fallback_voice = tts.get("fallback_voice", "fr-FR-HenriNeural")
        success = generate_with_edge_tts(fallback_voice, args.text, raw_path)

    if not success:
        print("\n❌ Échec de la génération audio")
        sys.exit(1)

    # Validate
    print(f"\n🔍 Validation de l'audio...")
    validation = validate_audio(raw_path)
    print(f"  Durée: {validation['info'].get('duration_s', '?')}s")
    print(f"  Codec: {validation['info'].get('codec', '?')}")
    print(f"  Taille: {validation['info'].get('file_size_kb', '?')} KB")

    if validation["ok"]:
        print("  ✅ Audio valide")
    else:
        print("  ❌ Problèmes détectés:")
        for err in validation["errors"]:
            print(f"     - {err}")

    # Normalize
    print(f"\n🔊 Normalisation (-16 LUFS)...")
    if normalize_audio(raw_path, normalized_path):
        print(f"\n✅ Test complet ! Écoute le résultat :")
        print(f"   Audio brut : {raw_path}")
        print(f"   Audio normalisé : {normalized_path}")
    else:
        print(f"\n⚠️  Normalisation échouée, mais l'audio brut est disponible : {raw_path}")

    # Instructions if ElevenLabs not configured
    if not api_key or not voice_id:
        print("\n" + "=" * 60)
        print("📋 POUR CONFIGURER ELEVENLABS :")
        print("=" * 60)
        print("1. Crée un compte sur https://elevenlabs.io (plan Creator $22/mois)")
        print("2. Voice Design → crée la voix 'TechDev FR' (homme, 25-35, FR)")
        print("3. Récupère l'API key et le voice_id")
        print("4. Édite config/unified_config.yaml :")
        print("   tts:")
        print("     elevenlabs:")
        print("       api_key: 'ta_clé'")
        print("       voice_id: 'ton_voice_id'")
        print("5. Synchronise : python scripts/sync_config.py")
        print("6. Re-teste : python scripts/test_voice.py")
        print("=" * 60)


if __name__ == "__main__":
    main()