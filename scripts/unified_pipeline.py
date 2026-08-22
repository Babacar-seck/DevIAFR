#!/usr/bin/env python3
"""
unified_pipeline.py — Pipeline de production vidéo unifié MPT × TST.

Orchestre la production d'une vidéo de bout en bout :
1. Génération du script humanisé (via humanize_script.py)
2. Production vidéo via MPT (API locale)
3. Post-processing (SFX, miniature, sous-titres)
4. Upload et publication

Usage:
    python unified_pipeline.py --subject "Comment créer une API REST .NET" --channel dev_ia_fr
    python unified_pipeline.py --script scripts/output/script_humanized.txt --channel dev_ia_fr
"""

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

import requests
import yaml

SCRIPT_DIR = Path(__file__).parent
DEVIAFR_ROOT = SCRIPT_DIR.parent
UNIFIED_CONFIG = DEVIAFR_ROOT / "config" / "unified_config.yaml"
OUTPUT_DIR = DEVIAFR_ROOT / "storage" / "output"


def load_config() -> dict:
    """Charge unified_config.yaml."""
    with open(UNIFIED_CONFIG) as f:
        return yaml.safe_load(f)


def generate_script(subject: str, cfg: dict) -> str:
    """Étape 1 : génère (TST) puis humanise (humanize_script.py) le script.

    humanize_script() retourne du texte brut (prose LLM structurée par le
    prompt storytelling), pas un objet JSON — on le sauvegarde tel quel en
    .txt, comme le fait humanize_script.py::main() et comme le lit
    api/routers/videos.py (script.txt).
    """
    print("\n[1/5] Génération du script humanisé...")

    script_output = SCRIPT_DIR / "output" / f"script_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    script_output.parent.mkdir(parents=True, exist_ok=True)

    tst_path = Path(cfg["projects"]["tst"]["path"]).expanduser()
    sys.path.insert(0, str(tst_path / "src"))
    from script_generator import generate_script as tst_generate_script

    sys.path.insert(0, str(SCRIPT_DIR))
    from humanize_script import humanize_script

    brut = tst_generate_script(topic=subject, format_type="top5", content_profile="ai_tech")
    humanized = humanize_script(brut, subject, cfg)

    script_output.write_text(humanized, encoding="utf-8")

    # Sidecar JSON (title/hook/body/cta/hashtags/description) — humanize_script()
    # ne renvoie que de la prose narrative, donc c'est la seule source de
    # métadonnées structurées pour l'upload YouTube (cf. uploader.py::_build_metadata).
    metadata_output = script_output.with_suffix(".json")
    metadata_output.write_text(json.dumps(brut, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"✓ Script humanisé : {script_output}")
    print(f"✓ Métadonnées upload : {metadata_output}")

    return str(script_output)


def _extract_narration_text(script_path: str) -> str:
    """Extrait le texte de narration d'un fichier script (JSON structuré ou texte brut)."""
    content = Path(script_path).read_text(encoding="utf-8").strip()
    try:
        data = json.loads(content)
    except (json.JSONDecodeError, TypeError):
        return content
    if isinstance(data, dict):
        parts = [str(data[key]) for key in ("hook", "body", "cta") if data.get(key)]
        if parts:
            return "\n\n".join(parts)
    return content


def generate_narration_rtvc(script_path: str, channel: str, cfg: dict) -> str | None:
    """Étape 1.5 : synthétise la narration localement via RTVC (voix du persona).

    Optionnelle : retourne None (et laisse MPT utiliser sa propre TTS) si
    tts.engine != "rtvc", si le persona n'a pas de voice_sample, ou si RTVC
    n'est pas disponible. Ne bloque jamais la production vidéo.
    """
    print("\n[1.5/5] Génération de la narration (RTVC)...")

    tts_cfg = cfg.get("tts", {})
    if tts_cfg.get("engine") != "rtvc":
        print("  ⚠ tts.engine != 'rtvc' dans unified_config.yaml — narration RTVC ignorée")
        return None

    persona_path = DEVIAFR_ROOT / "config" / "personas" / f"{channel}.yaml"
    if not persona_path.exists():
        print(f"  ⚠ Persona introuvable ({persona_path}) — narration RTVC ignorée")
        return None
    with open(persona_path, encoding="utf-8") as f:
        persona_cfg = yaml.safe_load(f) or {}

    voice_sample_rel = (persona_cfg.get("voice") or {}).get("voice_sample")
    if not voice_sample_rel:
        print(f"  ⚠ Aucune voice_sample définie pour '{channel}' — narration RTVC ignorée")
        return None
    voice_ref = DEVIAFR_ROOT / "storage" / voice_sample_rel
    if not voice_ref.exists():
        print(f"  ⚠ Référence vocale introuvable : {voice_ref} — narration RTVC ignorée")
        return None

    narration_text = _extract_narration_text(script_path)
    if not narration_text:
        print("  ⚠ Script vide — narration RTVC ignorée")
        return None

    rtvc_venv_python = Path(
        tts_cfg.get("rtvc", {}).get(
            "venv_python", "~/MyWorkProjectGithub/Real-Time-Voice-Cloning/.venv/bin/python"
        )
    ).expanduser()
    if not rtvc_venv_python.exists():
        print(f"  ⚠ Python RTVC introuvable : {rtvc_venv_python} — narration RTVC ignorée")
        return None

    narration_path = OUTPUT_DIR / f"narration_{channel}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
    narration_path.parent.mkdir(parents=True, exist_ok=True)

    proc = subprocess.run(
        [str(rtvc_venv_python), str(SCRIPT_DIR / "voice_clone_rtvc.py"),
         "--voice-ref", str(voice_ref),
         "--text", narration_text,
         "--output", str(narration_path)],
        cwd=str(DEVIAFR_ROOT),
        capture_output=True, text=True, timeout=600,
    )
    if proc.returncode != 0 or not narration_path.exists():
        error = (proc.stderr or proc.stdout or "erreur inconnue")[-500:]
        print(f"  ✗ Échec narration RTVC (fallback TTS MPT) : {error}")
        return None

    print(f"  ✓ Narration RTVC : {narration_path}")
    return str(narration_path)


def produce_video_mpt(script_path: str, subject: str, cfg: dict, narration_path: str | None = None) -> str:
    """Étape 2 : produit la vidéo via MPT API."""
    print("\n[2/5] Production vidéo via MPT...")

    script_content = Path(script_path).read_text()

    # Configuration MPT depuis unified_config
    mpt_cfg = cfg.get("projects", {}).get("mpt", {})
    mpt_url = mpt_cfg.get("api_url", "http://localhost:8080")
    mpt_timeout = mpt_cfg.get("timeout_s", 300)

    # Paramètres vidéo depuis unified_config
    visual_cfg = cfg.get("visual", {})
    subtitles_cfg = cfg.get("subtitles", {})
    # Le style de sous-titres vit sous subtitles.style.* dans le vrai schéma
    # (voir config/unified_config.yaml) — pas directement sous subtitles.* —
    # donc ces champs retombaient tous silencieusement sur leurs défauts codés
    # en dur, y compris une police ("Arial-Bold.ttf") absente des fonts MPT.
    style_cfg = subtitles_cfg.get("style", {})

    payload = {
        "video_subject": subject,
        "video_script": script_content,
        "video_aspect": visual_cfg.get("aspect", "9:16"),
        "video_concat_mode": "random",
        "video_transition_mode": visual_cfg.get("transition_mode", "shuffle"),
        "enable_bgm": True,
        "bgm_volume": visual_cfg.get("bgm_volume", 0.2),
        "font_name": style_cfg.get("font_name", "Charm-Bold.ttf"),
        "text_fore_color": style_cfg.get("text_color", "#FFFFFF"),
        "text_back_color": "#00000080",  # pas d'équivalent dans subtitles.style.*
        "font_size": style_cfg.get("font_size", 50),
        "stroke_color": style_cfg.get("stroke_color", "#000000"),
        "stroke_width": style_cfg.get("stroke_width", 1.5),
    }
    if narration_path:
        # Chemin absolu serveur : MPT accepte tout fichier existant hors de son
        # task_dir tant qu'il est fourni en chemin absolu (cf.
        # resolve_custom_audio_file dans MPT/app/services/task.py). Cela
        # court-circuite la TTS interne de MPT et utilise Whisper pour les
        # sous-titres, comme documenté sur VideoParams.custom_audio_file.
        payload["custom_audio_file"] = narration_path

    print(f"  → Appel MPT API : {mpt_url}/api/v1/videos")
    print(f"  → Sujet : {subject}")
    print(f"  → Aspect : {payload['video_aspect']}")
    if narration_path:
        print(f"  → Narration custom (RTVC) : {narration_path}")

    try:
        response = requests.post(
            f"{mpt_url}/api/v1/videos",
            json=payload,
            timeout=mpt_timeout,
        )

        if response.status_code == 200:
            # MPT enveloppe toutes ses réponses dans {"status":.., "data":..}
            # (app/utils/utils.py::get_response) — task_id est sous data, pas
            # à la racine.
            task_id = response.json().get("data", {}).get("task_id", "unknown")
            print(f"✓ Tâche MPT créée : {task_id}")

            # Poll pour attendre la fin. La route de statut réelle de MPT est
            # GET /api/v1/tasks/{task_id} (pas /api/v1/videos/{id}/status),
            # et l'état est un int (app/models/const.py :
            # TASK_STATE_FAILED=-1, TASK_STATE_COMPLETE=1), pas une string.
            print("  → Attente de la production...")
            status_url = f"{mpt_url}/api/v1/tasks/{task_id}"
            TASK_STATE_FAILED, TASK_STATE_COMPLETE = -1, 1
            for _ in range(60):  # 5 minutes max
                time.sleep(5)
                status_resp = requests.get(status_url, timeout=30)
                if status_resp.status_code == 200:
                    task_data = status_resp.json().get("data", {})
                    state = task_data.get("state")
                    if state == TASK_STATE_COMPLETE:
                        videos = task_data.get("videos") or []
                        if not videos:
                            print("✗ Tâche complétée mais aucune vidéo produite")
                            sys.exit(1)
                        # videos[i] est une URI type "/tasks/{task_id}/final-1.mp4"
                        # (app/controllers/v1/video.py::_task_file_to_uri, avec
                        # endpoint="" dans ce déploiement) — pas un chemin local
                        # ni une URL absolue. Le fichier vit sur le process MPT,
                        # potentiellement une autre machine ; on le rapatrie via
                        # /api/v1/download/{path relatif à tasks_dir}.
                        relative_path = videos[0].removeprefix("/tasks/")
                        video_bytes = requests.get(
                            f"{mpt_url}/api/v1/download/{relative_path}", timeout=mpt_timeout
                        ).content
                        local_video_path = OUTPUT_DIR / f"video_{task_id}.mp4"
                        local_video_path.parent.mkdir(parents=True, exist_ok=True)
                        local_video_path.write_bytes(video_bytes)
                        print(f"✓ Vidéo produite : {local_video_path}")
                        return str(local_video_path)
                    elif state == TASK_STATE_FAILED:
                        error = task_data.get("error", "Unknown error")
                        print(f"✗ Production échouée : {error}")
                        sys.exit(1)
                    else:
                        print(f"    État : {state}...")
                else:
                    print(f"    Poll error : {status_resp.status_code}")

            print("✗ Timeout : production trop longue")
            sys.exit(1)

        else:
            print(f"✗ Erreur MPT : {response.status_code}")
            print(f"  {response.text[:200]}")
            sys.exit(1)

    except requests.exceptions.ConnectionError:
        print(f"✗ Impossible de se connecter à MPT : {mpt_url}")
        print("  Vérifie que MPT tourne : cd ~/MyWorkProjectGithub/MoneyPrinterTurbo && .venv/bin/python webui.py")
        sys.exit(1)
    except Exception as e:
        print(f"✗ Erreur : {e}")
        sys.exit(1)


def post_process_sfx(video_path: str, cfg: dict) -> str:
    """Étape 3 : ajoute les effets sonores (SFX) via sfx_designer.py.

    sfx_designer.apply_sound_design() détecte les coupures de scène, y place
    un whoosh (fondu inclus) et applique un ducking sidechain sur la BGM si
    une piste est fournie. La bibliothèque SFX est synthétisée
    procéduralement (pas de fichiers externes requis).
    """
    print("\n[3/5] Post-processing : SFX...")

    sound_cfg = cfg.get("sound_design", {})
    if not sound_cfg.get("enabled", True):
        print("  ⚠ Sound design désactivé dans unified_config.yaml (sound_design.enabled)")
        return video_path

    if not Path(video_path).exists():
        print(f"  ⚠ Fichier vidéo inexistant : {video_path}")
        print("  → Skip SFX (mode test ou fichier manquant)")
        return video_path

    sys.path.insert(0, str(SCRIPT_DIR))
    from sfx_designer import apply_sound_design

    output_path = Path(video_path).with_name(f"{Path(video_path).stem}_sfx.mp4")

    # Pas de source BGM concrète configurée pour l'instant (sound_design.bgm.type
    # reste "random" sans chemin de fichier réel) — apply_sound_design() gère
    # bgm_path=None en sautant simplement le ducking.
    bgm_path = None

    try:
        apply_sound_design(Path(video_path), output_path, cfg, bgm_path=bgm_path)
    except subprocess.CalledProcessError as exc:
        print(f"  ✗ Échec sound design (fallback vidéo sans SFX) : {exc}")
        return video_path

    print(f"✓ Vidéo avec SFX : {output_path}")
    return str(output_path)


def generate_thumbnail(video_path: str, subject: str, cfg: dict) -> str:
    """Étape 4 : génère la miniature."""
    print("\n[4/5] Génération de la miniature...")

    thumbnail_cfg = cfg.get("thumbnail", {})
    backend = thumbnail_cfg.get("backend", "procedural")

    thumbnail_dir = DEVIAFR_ROOT / "storage" / "thumbnails"
    thumbnail_dir.mkdir(parents=True, exist_ok=True)
    thumbnail_path = thumbnail_dir / f"thumb_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"

    if backend == "comfyui":
        comfyui_url = thumbnail_cfg.get("comfyui_url", "http://localhost:8188")
        workflow_path = thumbnail_cfg.get("workflow_path")

        if not workflow_path or not Path(workflow_path).exists():
            print(f"  ⚠ Workflow ComfyUI manquant : {workflow_path}")
            backend = "procedural"

    if backend == "procedural":
        # Miniature procédurale simple avec PIL
        from PIL import Image, ImageDraw, ImageFont

        width = thumbnail_cfg.get("width", 1280)
        height = thumbnail_cfg.get("height", 720)

        img = Image.new("RGB", (width, height), color=(30, 30, 30))
        draw = ImageDraw.Draw(img)

        # Titre
        font_size = thumbnail_cfg.get("title_font_size", 80)
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except:
            font = ImageFont.load_default()

        # Wrap le texte
        words = subject.split()
        lines = []
        current_line = ""
        for word in words:
            test_line = f"{current_line} {word}".strip()
            bbox = draw.textbbox((0, 0), test_line, font=font)
            if bbox[2] - bbox[0] < width * 0.9:
                current_line = test_line
            else:
                lines.append(current_line)
                current_line = word
        if current_line:
            lines.append(current_line)

        # Dessine le texte
        y = height // 2 - (len(lines) * font_size) // 2
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            text_width = bbox[2] - bbox[0]
            x = (width - text_width) // 2
            draw.text((x, y), line, fill=(255, 255, 255), font=font)
            y += font_size + 10

        img.save(thumbnail_path)
        print(f"✓ Miniature procédurale : {thumbnail_path}")
        return str(thumbnail_path)

    print(f"✗ Backend non supporté : {backend}")
    sys.exit(1)


def _load_or_generate_metadata(script_path: str, subject: str | None, cfg: dict) -> dict:
    """Charge le JSON de métadonnées associé au script, ou le génère via LLM si absent.

    Le sidecar existe quand generate_script() a tourné dans ce process (chemin
    --subject). Quand unified_pipeline.py est appelé avec --script — notamment
    depuis api/routers/videos.py, qui génère le script via humanize_script.py
    en subprocess sans jamais produire ce sidecar — on reconstruit les mêmes
    champs par extraction LLM plutôt que par heuristique (ex. "1re ligne = titre").
    """
    metadata_path = Path(script_path).with_suffix(".json")
    if metadata_path.exists():
        return json.loads(metadata_path.read_text(encoding="utf-8"))

    print(f"  ⚠ Pas de métadonnées JSON ({metadata_path.name}) — extraction via LLM")

    tst_path = Path(cfg["projects"]["tst"]["path"]).expanduser()
    sys.path.insert(0, str(tst_path / "src"))
    from script_generator import _parse_json_response

    sys.path.insert(0, str(SCRIPT_DIR))
    from humanize_script import call_llm

    script_text = Path(script_path).read_text(encoding="utf-8")
    prompt = f"""Tu es un expert SEO YouTube Shorts francophone. Voici un script vidéo déjà écrit — extrait-en les métadonnées YouTube.

SUJET : {subject or "non précisé"}

SCRIPT :
{script_text}

Retourne UNIQUEMENT un JSON valide avec cette structure :
{{
  "title": "titre accrocheur < 80 chars avec majuscules sur 1-2 mots clés",
  "hook": "phrase d'accroche (max 10 mots, choc ou question provocante)",
  "body": ["phrase 1", "phrase 2", "..."],
  "cta": "appel à l'action final",
  "hashtags": ["IA", "Shorts", "..."],
  "description": "description YouTube 2-3 lignes"
}}"""
    raw = call_llm(prompt, cfg, max_tokens=1000, temperature=0.5)
    metadata = _parse_json_response(raw)

    metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  ✓ Métadonnées générées et sauvegardées : {metadata_path}")
    return metadata


def upload_video(video_path: str, script_path: str, thumbnail_path: str, subject: str | None, cfg: dict):
    """Étape 5 : upload et publication."""
    print("\n[5/5] Upload et publication...")

    youtube_cfg = cfg.get("youtube", {})
    upload_enabled = youtube_cfg.get("upload_enabled", False)

    if not upload_enabled:
        print("  ⚠ Upload désactivé (youtube.upload_enabled: false dans unified_config.yaml)")
        print(f"  → Vidéo prête : {video_path}")
        print(f"  → Script : {script_path}")
        print(f"  → Miniature : {thumbnail_path}")
        return

    tst_cfg = cfg.get("projects", {}).get("tst", {})
    tst_path = tst_cfg.get("path")
    if not tst_path or not Path(tst_path).expanduser().exists():
        print(f"✗ TST non trouvé : {tst_path}")
        sys.exit(1)
    tst_path = Path(tst_path).expanduser()

    sys.path.insert(0, str(tst_path / "src"))
    from uploader import upload_short

    metadata = _load_or_generate_metadata(script_path, subject, cfg)
    privacy = youtube_cfg.get("privacy_status", "private")

    print(f"  → Upload via TST uploader.py (privacy={privacy})")
    url = upload_short(
        Path(video_path),
        metadata,
        privacy=privacy,
        thumbnail_path=thumbnail_path,
    )
    print(f"✓ Vidéo uploadée : {url}")

    print(f"\n✓ Pipeline terminé !")
    print(f"  Vidéo : {video_path}")
    print(f"  Script : {script_path}")
    print(f"  Miniature : {thumbnail_path}")
    print(f"  URL YouTube : {url}")


def main():
    parser = argparse.ArgumentParser(description="Pipeline de production vidéo unifié MPT × TST")
    parser.add_argument("--subject", type=str, help="Sujet de la vidéo")
    parser.add_argument("--script", type=str, help="Fichier script existant (skip étape 1)")
    parser.add_argument("--channel", type=str, default="dev_ia_fr", help="Nom du channel")
    parser.add_argument("--skip-mpt", action="store_true", help="Skip production MPT (utilise vidéo existante)")
    parser.add_argument("--video", type=str, help="Vidéo existante (pour --skip-mpt)")
    args = parser.parse_args()

    if not args.subject and not args.script:
        print("Erreur: --subject ou --script requis", file=sys.stderr)
        sys.exit(1)

    if args.skip_mpt and not args.video:
        print("Erreur: --video requis avec --skip-mpt", file=sys.stderr)
        sys.exit(1)

    cfg = load_config()

    print("=" * 60)
    print("Pipeline de production vidéo unifié")
    print("=" * 60)
    print(f"Channel : {args.channel}")
    print(f"Sujet : {args.subject or 'Script personnalisé'}")

    # Étape 1 : Script
    if args.script:
        script_path = args.script
        print(f"\n✓ Script fourni : {script_path}")
    else:
        script_path = generate_script(args.subject, cfg)

    # Étape 2 : Production MPT
    if args.skip_mpt:
        video_path = args.video
        print(f"\n✓ Vidéo fournie (skip MPT) : {video_path}")
    else:
        narration_path = generate_narration_rtvc(script_path, args.channel, cfg)
        video_path = produce_video_mpt(script_path, args.subject, cfg, narration_path=narration_path)

    # Étape 3 : Post-processing SFX
    video_path = post_process_sfx(video_path, cfg)

    # Étape 4 : Miniature
    thumbnail_path = generate_thumbnail(video_path, args.subject, cfg)

    # Étape 5 : Upload
    upload_video(video_path, script_path, thumbnail_path, args.subject, cfg)

    print("\n" + "=" * 60)
    print("✓ Pipeline terminé avec succès !")
    print("=" * 60)


if __name__ == "__main__":
    main()
