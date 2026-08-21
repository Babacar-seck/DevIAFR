#!/usr/bin/env python3
"""
Voice Cloning avec Real-Time-Voice-Cloning (RTVC)
Remplace ElevenLabs par une solution 100% locale et gratuite.

Usage:
    python voice_clone_rtvc.py --voice-ref voice_samples/dev_ia_fr.wav --text "Bonjour" --output output.wav
    python voice_clone_rtvc.py --persona dev_ia_fr --text "Bonjour" --output output.wav
"""

import argparse
import sys
from pathlib import Path

# Ajouter RTVC au path
RTVC_PATH = Path.home() / "MyWorkProjectGithub" / "Real-Time-Voice-Cloning"
sys.path.insert(0, str(RTVC_PATH))

import numpy as np
import librosa
import soundfile as sf
from pathlib import Path

# Import RTVC modules
from encoder import inference as encoder
from synthesizer.inference import Synthesizer
from vocoder import inference as vocoder
from utils.default_models import ensure_default_models


class RTVCVoiceCloner:
    """Clonage de voix avec RTVC (Real-Time Voice Cloning)"""
    
    def __init__(self, device="cpu"):
        """
        Initialise les modèles RTVC.
        
        Args:
            device: "cpu" ou "cuda" (GPU NVIDIA)
        """
        self.device = device
        self.rtvc_path = RTVC_PATH
        self.saved_models = self.rtvc_path / "saved_models"
        
        # Chemins des modèles
        self.enc_model = self.saved_models / "default" / "encoder.pt"
        self.syn_model = self.saved_models / "default" / "synthesizer.pt"
        self.voc_model = self.saved_models / "default" / "vocoder.pt"
        
        # Charger les modèles
        self._load_models()
    
    def _load_models(self):
        """Charge les 3 modèles RTVC (encoder, synthesizer, vocoder)"""
        print("🔧 Chargement des modèles RTVC...")
        
        # S'assurer que les modèles sont téléchargés
        ensure_default_models(self.saved_models)
        
        # Encoder: crée l'embedding de voix
        encoder.load_model(self.enc_model)
        print("  ✓ Encoder chargé")
        
        # Synthesizer: génère le spectrogramme
        self.synthesizer = Synthesizer(self.syn_model)
        print("  ✓ Synthesizer chargé")
        
        # Vocoder: convertit le spectrogramme en audio
        vocoder.load_model(self.voc_model)
        print("  ✓ Vocoder chargé")
        
        print("✅ Modèles RTVC prêts\n")
    
    def clone_voice(self, text: str, voice_ref_path: str, output_path: str) -> str:
        """
        Clone une voix et génère l'audio pour le texte donné.
        
        Args:
            text: Texte à synthétiser
            voice_ref_path: Chemin vers l'audio de référence (5-10 secondes)
            output_path: Chemin de sortie pour l'audio généré
            
        Returns:
            Chemin vers le fichier audio généré
        """
        print(f"🎤 Clonage de voix...")
        print(f"  Référence: {voice_ref_path}")
        print(f"  Texte: {text[:80]}...")
        
        # 1. Charger l'audio de référence
        print("  📥 Chargement de l'audio de référence...")
        wav, _ = librosa.load(voice_ref_path, sr=16000)
        
        # 2. Créer l'embedding de la voix
        print("  🔍 Création de l'embedding de voix...")
        speaker_embedding = encoder.embed_utterance(wav)
        
        # 3. Générer le spectrogramme
        print("  🎵 Génération du spectrogramme...")
        specs = self.synthesizer.synthesize_spectrograms(
            [text],
            [speaker_embedding]
        )
        
        # 4. Convertir en audio avec le vocoder
        print("  🔊 Conversion en audio...")
        generated_wav = vocoder.infer_waveform(specs[0])
        
        # 5. Sauvegarder
        print(f"  💾 Sauvegarde: {output_path}")
        sf.write(output_path, generated_wav, self.synthesizer.sample_rate)
        
        print(f"✅ Audio généré: {output_path}\n")
        return output_path


def get_voice_sample_for_persona(persona_id: str) -> str:
    """
    Retourne le chemin vers l'échantillon de voix pour un persona.
    
    Args:
        persona_id: ID du persona (ex: "dev_ia_fr")
        
    Returns:
        Chemin vers le fichier WAV de référence
    """
    voice_samples_dir = Path(__file__).parent.parent / "voice_samples"
    voice_samples_dir.mkdir(exist_ok=True)
    
    sample_path = voice_samples_dir / f"{persona_id}.wav"
    
    if not sample_path.exists():
        print(f"⚠️  Échantillon de voix manquant: {sample_path}")
        print(f"\n📝 Pour créer un échantillon de voix pour {persona_id}:")
        print(f"   1. Enregistrez 5-10 secondes de votre voix")
        print(f"   2. Sauvegardez en WAV (16kHz, mono)")
        print(f"   3. Placez le fichier ici: {sample_path}")
        print(f"\n💡 Astuce: Utilisez Audacity ou un enregistreur vocal")
        print(f"   - Format: WAV")
        print(f"   - Fréquence: 16000 Hz")
        print(f"   - Canaux: Mono")
        print(f"   - Durée: 5-10 secondes")
        print(f"   - Contenu: Parlez naturellement (ex: 'Bonjour, je vais vous présenter...')")
        sys.exit(1)
    
    return str(sample_path)


def main():
    parser = argparse.ArgumentParser(
        description="Clonage de voix avec RTVC (Real-Time Voice Cloning)"
    )
    parser.add_argument(
        "--voice-ref",
        help="Chemin vers l'audio de référence (5-10 sec, WAV 16kHz)"
    )
    parser.add_argument(
        "--persona",
        help="ID du persona (ex: dev_ia_fr) - utilise voice_samples/{persona}.wav"
    )
    parser.add_argument(
        "--text",
        required=True,
        help="Texte à synthétiser"
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Chemin de sortie pour l'audio généré"
    )
    parser.add_argument(
        "--device",
        choices=["cpu", "cuda"],
        default="cpu",
        help="Device pour le processing (default: cpu)"
    )
    
    args = parser.parse_args()
    
    # Déterminer le chemin de l'échantillon de voix
    if args.persona:
        voice_ref = get_voice_sample_for_persona(args.persona)
    elif args.voice_ref:
        voice_ref = args.voice_ref
    else:
        parser.error("Vous devez spécifier --voice-ref ou --persona")
    
    # Créer le cloneur
    cloner = RTVCVoiceCloner(device=args.device)
    
    # Générer l'audio
    cloner.clone_voice(
        text=args.text,
        voice_ref_path=voice_ref,
        output_path=args.output
    )


if __name__ == "__main__":
    main()
