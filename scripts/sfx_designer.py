#!/usr/bin/env python3
"""sfx_designer.py — Sound design automatique (UNIFY-05).

Enrichit une vidéo finale avec :
1. Détection des coupures de scène (ffmpeg `select=gt(scene,...)`) et
   placement d'un SFX (whoosh) à chaque coupure, avec fondu.
2. Ducking musical : une piste de musique de fond est automatiquement
   compressée (sidechaincompress) quand la voix est active.

La bibliothèque SFX (whoosh, impact, pop, riser, transition) est synthétisée
procéduralement via des filtres audio ffmpeg et mise en cache dans
storage/sfx/ — pas de dépendance réseau ni de question de licence externe.

Usage standalone (test) :
    python scripts/sfx_designer.py input.mp4 output.mp4
    python scripts/sfx_designer.py input.mp4 output.mp4 --bgm musique.mp3
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

import yaml

SCRIPT_DIR = Path(__file__).parent.parent
UNIFIED_CONFIG = SCRIPT_DIR / "config" / "unified_config.yaml"
DEFAULT_SFX_DIR = SCRIPT_DIR / "storage" / "sfx"


def load_config() -> dict:
    with open(UNIFIED_CONFIG) as f:
        return yaml.safe_load(f)


# ── SFX library (synthétisée procéduralement) ───────────────────────────────

def _run_ffmpeg(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)


def _synth_whoosh(out_path: Path) -> None:
    _run_ffmpeg([
        "ffmpeg", "-y", "-f", "lavfi", "-i", "anoisesrc=d=0.4:c=pink:a=0.6",
        "-af", "bandpass=f=1200:width_type=h:w=2000,"
               "afade=t=in:d=0.05,afade=t=out:st=0.3:d=0.1",
        "-ar", "44100", "-ac", "2", str(out_path),
    ])


def _synth_impact(out_path: Path) -> None:
    _run_ffmpeg([
        "ffmpeg", "-y", "-f", "lavfi", "-i", "anoisesrc=d=0.25:c=brown:a=0.9",
        "-af", "lowpass=f=300,afade=t=in:d=0.005,afade=t=out:st=0.05:d=0.2",
        "-ar", "44100", "-ac", "2", str(out_path),
    ])


def _synth_pop(out_path: Path) -> None:
    _run_ffmpeg([
        "ffmpeg", "-y", "-f", "lavfi", "-i", "sine=frequency=800:duration=0.12",
        "-af", "afade=t=in:d=0.005,afade=t=out:st=0.06:d=0.06,volume=0.8",
        "-ar", "44100", "-ac", "2", str(out_path),
    ])


def _synth_riser(out_path: Path) -> None:
    _run_ffmpeg([
        "ffmpeg", "-y", "-f", "lavfi", "-i", "anoisesrc=d=1.0:c=white:a=0.15",
        "-af", "afade=t=in:d=0.9,afade=t=out:st=0.9:d=0.1,volume=3,lowpass=f=4000",
        "-ar", "44100", "-ac", "2", str(out_path),
    ])


def _synth_transition(out_path: Path) -> None:
    _run_ffmpeg([
        "ffmpeg", "-y", "-f", "lavfi", "-i", "anoisesrc=d=0.35:c=pink:a=0.5",
        "-af", "bandpass=f=2000:width_type=h:w=3000,"
               "afade=t=in:d=0.03,afade=t=out:st=0.25:d=0.1",
        "-ar", "44100", "-ac", "2", str(out_path),
    ])


_SFX_SYNTHESIZERS = {
    "whoosh": _synth_whoosh,
    "impact": _synth_impact,
    "pop": _synth_pop,
    "riser": _synth_riser,
    "transition": _synth_transition,
}


def ensure_sfx_library(sfx_dir: Path = DEFAULT_SFX_DIR) -> dict[str, Path]:
    """Génère la bibliothèque SFX si absente et renvoie nom -> chemin .wav."""
    sfx_dir.mkdir(parents=True, exist_ok=True)
    library: dict[str, Path] = {}
    for name, synth in _SFX_SYNTHESIZERS.items():
        path = sfx_dir / f"{name}.wav"
        if not path.exists():
            synth(path)
        library[name] = path
    return library


# ── Détection des coupures de scène ──────────────────────────────────────────

_PTS_TIME_RE = re.compile(r"pts_time:([\d.]+)")


def detect_scene_cuts(video_path: Path, threshold: float = 0.3) -> list[float]:
    """Détecte les timestamps (s) des coupures de scène via le filtre `select`."""
    cmd = [
        "ffmpeg", "-i", str(video_path),
        "-vf", f"select='gt(scene,{threshold})',showinfo",
        "-f", "null", "-",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return [float(m) for m in _PTS_TIME_RE.findall(result.stderr)]


# ── Placement des SFX aux coupures ──────────────────────────────────────────

def place_sfx_at_cuts(
    video_path: Path,
    output_path: Path,
    cut_times: list[float],
    sfx_path: Path,
    sfx_volume_db: float = -12.0,
) -> bool:
    """Mixe un SFX (avec fondu déjà intégré au fichier source) à chaque coupure."""
    if not cut_times:
        _run_ffmpeg(["ffmpeg", "-y", "-i", str(video_path), "-c", "copy", str(output_path)])
        return True

    inputs = ["-i", str(video_path)]
    for _ in cut_times:
        inputs += ["-i", str(sfx_path)]

    sfx_labels = []
    filter_parts = []
    for i, t in enumerate(cut_times):
        delay_ms = int(t * 1000)
        label = f"sfx{i}"
        filter_parts.append(
            f"[{i + 1}:a]volume={sfx_volume_db}dB,adelay={delay_ms}|{delay_ms}[{label}]"
        )
        sfx_labels.append(f"[{label}]")

    mix_inputs = "".join(["[0:a]"] + sfx_labels)
    filter_parts.append(
        f"{mix_inputs}amix=inputs={len(sfx_labels) + 1}:duration=first:dropout_transition=0[mixed]"
    )
    filter_complex = ";".join(filter_parts)

    cmd = [
        "ffmpeg", "-y", *inputs,
        "-filter_complex", filter_complex,
        "-map", "0:v", "-map", "[mixed]",
        "-c:v", "copy", "-c:a", "aac",
        str(output_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode == 0


# ── Ducking musical (sidechain compression) ─────────────────────────────────

def apply_ducking(
    video_path: Path,
    output_path: Path,
    bgm_path: Path,
    threshold: float = 0.05,
    ratio: float = 8.0,
    makeup_db: float = 2.0,
    bgm_volume: float = 0.5,
) -> bool:
    """Mixe une piste de musique de fond, compressée (ducking) quand la voix est active.

    La piste vidéo d'entrée sert de déclencheur sidechain (elle contient la
    voix) ; la piste bgm est celle qu'on compresse, puis les deux sont
    remixées ensemble dans la sortie.
    """
    filter_complex = (
        f"[1:a]volume={bgm_volume}[bgm];"
        f"[0:a][bgm]sidechaincompress=threshold={threshold}:ratio={ratio}:"
        f"makeup={makeup_db}:attack=5:release=200[ducked];"
        f"[0:a][ducked]amix=inputs=2:duration=first:dropout_transition=0[mixed]"
    )
    cmd = [
        "ffmpeg", "-y",
        "-i", str(video_path), "-i", str(bgm_path),
        "-filter_complex", filter_complex,
        "-map", "0:v", "-map", "[mixed]",
        "-c:v", "copy", "-c:a", "aac",
        str(output_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode == 0


# ── Pipeline complet ─────────────────────────────────────────────────────────

def apply_sound_design(
    video_path: Path,
    output_path: Path,
    cfg: dict,
    bgm_path: Path | None = None,
) -> Path:
    """Applique le sound design complet : SFX aux coupures + ducking musical (si bgm fournie)."""
    sound_cfg = cfg.get("sound_design", {})
    if not sound_cfg.get("enabled", True):
        _run_ffmpeg(["ffmpeg", "-y", "-i", str(video_path), "-c", "copy", str(output_path)])
        return output_path

    sfx_dir = Path(sound_cfg.get("sfx_library_path", "storage/sfx"))
    if not sfx_dir.is_absolute():
        sfx_dir = SCRIPT_DIR / sfx_dir
    sfx_volume_db = sound_cfg.get("sfx_volume_db", -12.0)

    library = ensure_sfx_library(sfx_dir)
    cut_times = detect_scene_cuts(video_path)

    with_sfx = output_path.with_suffix(".sfx.mp4")
    place_sfx_at_cuts(video_path, with_sfx, cut_times, library["whoosh"], sfx_volume_db)

    ducking_cfg = sound_cfg.get("ducking", {})
    if bgm_path and ducking_cfg.get("enabled", True):
        apply_ducking(
            with_sfx, output_path, bgm_path,
            threshold=ducking_cfg.get("threshold", 0.05),
            ratio=ducking_cfg.get("ratio", 8),
            makeup_db=ducking_cfg.get("makeup_db", 2),
            bgm_volume=sound_cfg.get("bgm", {}).get("volume", 0.15),
        )
        with_sfx.unlink(missing_ok=True)
    else:
        with_sfx.rename(output_path)

    return output_path


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Sound design automatique (test standalone)")
    parser.add_argument("input", type=Path, help="Vidéo source")
    parser.add_argument("output", type=Path, help="Vidéo de sortie")
    parser.add_argument("--bgm", type=Path, default=None, help="Piste de musique de fond (optionnelle)")
    args = parser.parse_args()

    cfg = load_config()
    result = apply_sound_design(args.input, args.output, cfg, bgm_path=args.bgm)
    print(f"✅ Sound design appliqué : {result}")
