#!/usr/bin/env python3
"""
voice_clone_tts.py — TTS via Real-Time-Voice-Cloning (RTVC) pour Dev IA FR.

Clone une voix de référence (quelques secondes d'audio) et génère du speech
à partir de texte. 100% local, gratuit, indétectable par YouTube.

Usage:
    # Générer l'audio avec la voix de référence
    python voice_clone_tts.py --text "Bonjour..." --ref ref_voice.wav --output out.wav

    # Avec normalisation -16 LUFS
    python voice_clone_tts.py --text "Bonjour..." --ref ref_voice.wav --output out.wav --normalize

    # Encoder seulement (créer un embedding réutilisable)
    python voice_clone_tts.py --encode-ref ref_voice.wav --save-embed embed.npy

    # Générer avec un embedding pré-calculé
    python voice_clone_tts.py --text "Bonjour..." --load-embed embed.npy --output out.wav
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

# ── RTVC paths ──
RTVC_PATH = Path.home() / "MyWorkProjectGithub" / "Real-Time-Voice-Cloning"
RTVC_VENV = RTVC_PATH / ".venv" / "bin" / "python"

# ── DevIAFR paths ──
DEVIAFR = Path.home() / "MyWorkDirectory" / "DevIAFR"
VOICE_SAMPLES = DEVIAFR / "storage" / "voice_samples"
DEFAULT_REF = VOICE_SAMPLES / "reference_voice.wav"  # ta voix de référence


def _clean_sys_path():
    """Remove Hermes agent paths so RTVC's venv packages don't conflict."""
    sys.path = [p for p in sys.path if "hermes" not in p]


def _load_rtvc():
    """Import RTVC modules (must be run with RTVC's venv Python)."""
    _clean_sys_path()
    # Add RTVC to sys.path so its modules (encoder, synthesizer, vocoder) are importable
    rtvc_src = str(RTVC_PATH)
    if rtvc_src not in sys.path:
        sys.path.insert(0, rtvc_src)
    os.chdir(str(RTVC_PATH))
    from encoder import inference as encoder
    from synthesizer.inference import Synthesizer
    from vocoder import inference as vocoder
    return encoder, Synthesizer, vocoder


def generate_speech(
    text: str,
    ref_audio_path: Path | None = None,
    embed_path: Path | None = None,
    output_path: Path = None,
    normalize: bool = False,
    models_dir: Path = None,
) -> Path:
    """Generate speech from text using a cloned voice.

    Args:
        text: The text to synthesize.
        ref_audio_path: Path to reference voice audio (mp3, wav, etc.).
        embed_path: Path to a pre-computed embedding (.npy).
        output_path: Where to save the generated audio.
        normalize: If True, normalize to -16 LUFS with ffmpeg.
        models_dir: Directory containing saved_models/default/{encoder,synthesizer,vocoder}.pt

    Returns:
        Path to the generated audio file.
    """
    if output_path is None:
        output_path = VOICE_SAMPLES / "rtvc_output.wav"
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if models_dir is None:
        models_dir = RTVC_PATH / "saved_models" / "default"

    print(f"🎙️  RTVC Voice Cloning TTS")
    print(f"   Text: {text[:80]}...")
    print(f"   Output: {output_path}")

    encoder, Synthesizer, vocoder_cls = _load_rtvc()

    # Load models
    print("   Loading models...")
    encoder.load_model(models_dir / "encoder.pt")
    synthesizer = Synthesizer(models_dir / "synthesizer.pt")
    vocoder_cls.load_model(models_dir / "vocoder.pt")

    # Get embedding
    if embed_path and embed_path.exists():
        print(f"   Loading pre-computed embedding: {embed_path}")
        import numpy as np
        embed = np.load(str(embed_path))
    elif ref_audio_path and ref_audio_path.exists():
        print(f"   Encoding reference voice: {ref_audio_path}")
        preprocessed_wav = encoder.preprocess_wav(ref_audio_path)
        embed = encoder.embed_utterance(preprocessed_wav)
        print(f"   Embedding shape: {embed.shape}")
    else:
        raise FileNotFoundError(
            f"Neither reference audio ({ref_audio_path}) nor embedding ({embed_path}) found. "
            f"Provide --ref or --load-embed."
        )

    # Synthesize spectrogram
    print("   Synthesizing spectrogram...")
    specs = synthesizer.synthesize_spectrograms([text], [embed])
    spec = specs[0]

    # Generate waveform
    print("   Generating waveform (this takes a few seconds on CPU)...")
    import numpy as np
    generated_wav = vocoder_cls.infer_waveform(spec)
    generated_wav = np.pad(generated_wav, (0, synthesizer.sample_rate), mode="constant")
    generated_wav = encoder.preprocess_wav(generated_wav)

    # Save
    import soundfile as sf
    sf.write(str(output_path), generated_wav.astype(np.float32), synthesizer.sample_rate)
    duration = len(generated_wav) / synthesizer.sample_rate
    print(f"   ✅ Saved: {output_path} ({duration:.1f}s)")

    # Normalize
    if normalize:
        normalized = output_path.with_suffix(".normalized.mp3")
        print(f"   Normalizing to -16 LUFS...")
        cmd = [
            "ffmpeg", "-y", "-i", str(output_path),
            "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
            "-c:a", "libmp3lame", "-b:a", "192k",
            str(normalized),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"   ✅ Normalized: {normalized}")
            return normalized
        else:
            print(f"   ⚠️  Normalization failed: {result.stderr[:100]}")

    return output_path


def encode_reference(ref_audio_path: Path, save_embed_path: Path | None = None) -> Path:
    """Encode a reference voice into an embedding for reuse.

    Args:
        ref_audio_path: Path to the reference voice audio.
        save_embed_path: Where to save the embedding (.npy).

    Returns:
        Path to the saved embedding.
    """
    if save_embed_path is None:
        save_embed_path = VOICE_SAMPLES / "voice_embedding.npy"
    save_embed_path = Path(save_embed_path)
    save_embed_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"🎙️  Encoding reference voice: {ref_audio_path}")

    encoder, _, _ = _load_rtvc()
    encoder.load_model(RTVC_PATH / "saved_models" / "default" / "encoder.pt")

    preprocessed_wav = encoder.preprocess_wav(ref_audio_path)
    embed = encoder.embed_utterance(preprocessed_wav)

    import numpy as np
    np.save(str(save_embed_path), embed)
    print(f"   ✅ Embedding saved: {save_embed_path} (shape: {embed.shape})")
    return save_embed_path


def main():
    parser = argparse.ArgumentParser(description="RTVC Voice Cloning TTS for Dev IA FR")
    parser.add_argument("--text", type=str, help="Text to synthesize")
    parser.add_argument("--ref", type=Path, help="Reference voice audio file")
    parser.add_argument("--load-embed", type=Path, help="Pre-computed embedding (.npy)")
    parser.add_argument("--save-embed", type=Path, help="Save embedding from ref voice")
    parser.add_argument("--encode-ref", type=Path, help="Only encode a reference voice")
    parser.add_argument("--output", type=Path, default=None, help="Output audio path")
    parser.add_argument("--normalize", action="store_true", help="Normalize to -16 LUFS")
    args = parser.parse_args()

    if args.encode_ref:
        encode_reference(args.encode_ref, args.save_embed)
        return

    if not args.text:
        # Default test text
        args.text = (
            "Salut, bienvenue sur Dev IA FR. "
            "Aujourd'hui, on va voir comment intégrer Claude AI dans une application .NET. "
            "Franchement, quand j'ai testé pour la première fois, j'ai été bluffé. "
            "Allez, c'est parti !"
        )
        print(f"(Using default test text: {args.text[:60]}...)")

    if not args.ref and not args.load_embed:
        # Use default reference voice if available
        if DEFAULT_REF.exists():
            args.ref = DEFAULT_REF
            print(f"(Using default reference voice: {DEFAULT_REF})")
        else:
            # Use a sample from RTVC
            sample = RTVC_PATH / "samples" / "1320_00000.mp3"
            if sample.exists():
                args.ref = sample
                print(f"(Using RTVC sample voice: {sample})")
                print(f"⚠️  Record your own reference voice at {DEFAULT_REF} for your custom voice!")
            else:
                print("ERROR: No reference voice found. Provide --ref or --load-embed.")
                sys.exit(1)

    generate_speech(
        text=args.text,
        ref_audio_path=args.ref,
        embed_path=args.load_embed,
        output_path=args.output,
        normalize=args.normalize,
    )

    # Show instructions for custom voice
    if args.ref and args.ref.name in ("1320_00000.mp3",):
        print("\n" + "=" * 60)
        print("📋 POUR UTILISER TA PROPRE VOIX :")
        print("=" * 60)
        print(f"1. Enregistre 10-30s de ta voix (lis un texte à voix haute)")
        print(f"2. Sauvegarde le fichier audio à :")
        print(f"   {DEFAULT_REF}")
        print(f"3. Re-teste : python voice_clone_tts.py --normalize")
        print(f"4. Ou encode seulement l'embedding :")
        print(f"   python voice_clone_tts.py --encode-ref {DEFAULT_REF}")
        print(f"   python voice_clone_tts.py --text '...' --load-embed storage/voice_samples/voice_embedding.npy")
        print("=" * 60)


if __name__ == "__main__":
    main()