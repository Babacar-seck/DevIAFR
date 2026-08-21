#!/usr/bin/env python3
"""
sync_config.py — Propage unified_config.yaml vers MPT (config.toml) et TST (config.yaml).

Usage:
    python sync_config.py --dry-run    # affiche les diffs sans appliquer
    python sync_config.py              # applique les changements
    python sync_config.py --section tts  # sync uniquement la section TTS
"""

from __future__ import annotations

import argparse
import os
import re
import sys
try:
    import tomllib  # Python 3.11+
except ImportError:
    import tomli as tomllib  # fallback
from pathlib import Path

import yaml

# ── Paths ────────────────────────────────────────────────────────────────────

SCRIPT_DIR = Path(__file__).parent.parent
UNIFIED_CONFIG = SCRIPT_DIR / "config" / "unified_config.yaml"

# Resolve paths relative to home
HOME = Path.home()


def _resolve(path_str: str) -> Path:
    return Path(os.path.expanduser(path_str))


# ── Load unified config ──────────────────────────────────────────────────────


def load_unified() -> dict:
    with open(UNIFIED_CONFIG) as f:
        return yaml.safe_load(f)


# ── MPT config.toml generation ───────────────────────────────────────────────


def patch_mpt_toml(cfg: dict, existing_content: str) -> str:
    """Patch specific keys in the existing MPT config.toml (non-destructive).

    Only modifies the keys we manage. Everything else is preserved.
    """

    tts = cfg.get("tts", {})
    elevenlabs = tts.get("elevenlabs", {})
    llm = cfg.get("llm", {})
    visual = cfg.get("visual", {})
    subtitles = cfg.get("subtitles", {})
    sound = cfg.get("sound_design", {})
    youtube = cfg.get("youtube", {})
    cross = cfg.get("cross_platform", {})
    upload_post = cross.get("upload_post", {})

    content = existing_content

    # Helper: replace a key=value line (simple top-level or [section] scoped)
    def _replace_key(text: str, key: str, new_value: str, section: str | None = None) -> str:
        """Replace a key = "value" or key = value line in the text."""
        if section:
            # Find the section header, then replace the key within it
            pattern = rf'(\[{re.escape(section)}\][^\[]*?){re.escape(key)}\s*=\s*[^ \n]+'
            replacement = rf'\g<1>{key} = {new_value}'
            new_text, count = re.subn(pattern, replacement, text, count=1, flags=re.DOTALL)
        else:
            # Top-level key
            pattern = rf'^{re.escape(key)}\s*=\s*.*$'
            replacement = f'{key} = {new_value}'
            new_text, count = re.subn(pattern, replacement, text, count=1, flags=re.MULTILINE)
        return new_text if count > 0 else text

    def _replace_key_in_section(text: str, section: str, key: str, new_value: str) -> str:
        """Replace key within a [section] block."""
        # Find the section and the key within it
        lines = text.split('\n')
        in_section = False
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith('['):
                in_section = stripped == f'[{section}]'
            elif in_section and stripped.startswith(f'{key}'):
                lines[i] = f'{key} = {new_value}'
                return '\n'.join(lines)
        # Key not found in section — try to add it
        lines = text.split('\n')
        in_section = False
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped == f'[{section}]':
                in_section = True
            elif in_section and stripped.startswith('['):
                # Insert before next section
                lines.insert(i, f'{key} = {new_value}')
                lines.insert(i, '')
                return '\n'.join(lines)
        return text

    # ── [app] section patches ──
    content = _replace_key_in_section(content, "app", "llm_provider", f'"{llm.get("provider", "ollama")}"')
    content = _replace_key_in_section(content, "app", "ollama_base_url", f'"{llm.get("ollama_base_url", "http://localhost:11434/v1")}"')
    content = _replace_key_in_section(content, "app", "ollama_model_name", f'"{llm.get("model", "kimi-k2.7-code:cloud")}"')
    content = _replace_key_in_section(content, "app", "video_source", f'"{visual.get("mpt_video_source", "pexels")}"')
    content = _replace_key_in_section(content, "app", "subtitle_provider", f'"{subtitles.get("provider", "edge")}"')
    content = _replace_key_in_section(content, "app", "upload_post_enabled", "true" if cross.get("enabled", False) else "false")
    content = _replace_key_in_section(content, "app", "upload_post_username", f'"{upload_post.get("username", "")}"')
    content = _replace_key_in_section(content, "app", "upload_post_auto_upload", "true" if upload_post.get("auto_upload", False) else "false")
    content = _replace_key_in_section(content, "app", "upload_post_youtube_privacy_status", f'"{upload_post.get("youtube_privacy_status", "public")}"')

    # ── [elevenlabs] section patches ──
    content = _replace_key_in_section(content, "elevenlabs", "api_key", f'"{elevenlabs.get("api_key", "")}"')
    content = _replace_key_in_section(content, "elevenlabs", "model_id", f'"{elevenlabs.get("model_id", "eleven_multilingual_v2")}"')

    # ── [whisper] section patches ──
    whisper = subtitles.get("whisper", {})
    content = _replace_key_in_section(content, "whisper", "model_size", f'"{whisper.get("model_size", "large-v3")}"')
    content = _replace_key_in_section(content, "whisper", "device", f'"{whisper.get("device", "cpu")}"')
    content = _replace_key_in_section(content, "whisper", "compute_type", f'"{whisper.get("compute_type", "int8")}"')

    # ── [ui] section patches ──
    subtitle_style = subtitles.get("style", {})
    voice_id = elevenlabs.get("voice_id", "")
    if voice_id:
        content = _replace_key_in_section(content, "ui", "tts_server", '"elevenlabs"')
        content = _replace_key_in_section(content, "ui", "voice_name", f'"elevenlabs:{voice_id}"')
    content = _replace_key_in_section(content, "ui", "video_transition_mode", f'"{visual.get("transition_mode", "Shuffle")}"')
    content = _replace_key_in_section(content, "ui", "video_aspect_pexels", f'"{visual.get("short_aspect", "9:16")}"')
    content = _replace_key_in_section(content, "ui", "video_clip_duration", str(visual.get("clip_duration_s", 5)))
    content = _replace_key_in_section(content, "ui", "video_clip_speed", str(visual.get("clip_speed", 1.0)))
    content = _replace_key_in_section(content, "ui", "bgm_type", f'"{sound.get("bgm", {}).get("type", "random")}"')
    content = _replace_key_in_section(content, "ui", "bgm_volume", str(sound.get("bgm", {}).get("volume", 0.2)))
    content = _replace_key_in_section(content, "ui", "subtitle_enabled", "true" if subtitles.get("provider") != "none" else "false")
    content = _replace_key_in_section(content, "ui", "font_name", f'"{subtitle_style.get("font_name", "Arial-Bold.ttf")}"')
    content = _replace_key_in_section(content, "ui", "subtitle_position", f'"{subtitle_style.get("position", "bottom")}"')
    content = _replace_key_in_section(content, "ui", "text_fore_color", f'"{subtitle_style.get("text_color", "#ffffff")}"')
    content = _replace_key_in_section(content, "ui", "font_size", str(subtitle_style.get("font_size", 50)))
    content = _replace_key_in_section(content, "ui", "stroke_color", f'"{subtitle_style.get("stroke_color", "#000000")}"')
    content = _replace_key_in_section(content, "ui", "stroke_width", str(subtitle_style.get("stroke_width", 1.5)))
    content = _replace_key_in_section(content, "ui", "subtitle_background_enabled", "true" if subtitle_style.get("background_enabled", False) else "false")

    return content


# ── TST config.yaml patching ─────────────────────────────────────────────────


def patch_tst_config_yaml(cfg: dict, existing_content: str) -> str:
    """Patch specific keys in the existing TST config.yaml (non-destructive).

    Uses line-based patching to preserve all unmanaged keys.
    """

    tts = cfg.get("tts", {})
    elevenlabs = tts.get("elevenlabs", {})
    llm = cfg.get("llm", {})
    visual = cfg.get("visual", {})
    youtube = cfg.get("youtube", {})
    channel = cfg.get("channel", {})
    comfyui = visual.get("comfyui", {})

    lines = existing_content.split('\n')
    changes = {}

    # Build a map of key -> new value (YAML top-level "key: value")
    # Only patch keys we manage
    if "llm:" not in existing_content:
        # If llm section doesn't exist, we skip it
        pass

    # Simple key: value replacements (top-level only)
    replacements = {
        # audio section
        "tts_voice": None,  # don't touch
    }

    # Use regex to find and replace specific keys
    def _replace_yaml_key(text: str, key: str, new_value: str) -> str:
        """Replace a 'key: value' line in YAML (top-level or indented)."""
        pattern = rf'^(\s*){re.escape(key)}\s*:\s*.*$'
        replacement = rf'\g<1>{key}: {new_value}'
        new_text, count = re.subn(pattern, replacement, text, count=1, flags=re.MULTILINE)
        return new_text if count > 0 else text

    content = existing_content

    # LLM section
    content = _replace_yaml_key(content, "provider", f'"{llm.get("provider", "ollama")}"')
    content = _replace_yaml_key(content, "model", f'"{llm.get("humanizer_model", "gemini-3.5-flash-lite")}"')
    content = _replace_yaml_key(content, "ollama_base_url", f'"{llm.get("ollama_base_url", "http://localhost:11434/v1")}"')
    content = _replace_yaml_key(content, "max_tokens", str(llm.get("max_tokens", 500)))
    content = _replace_yaml_key(content, "temperature", str(llm.get("temperature", 0.7)))

    # Audio section
    content = _replace_yaml_key(content, "tts_engine", f'"{tts.get("engine", "elevenlabs")}"')
    # Only patch elevenlabs_voice_id if it exists and is empty
    voice_id = elevenlabs.get("voice_id", "")
    if voice_id:
        content = _replace_yaml_key(content, "elevenlabs_voice_id", f'"{voice_id}"')

    # Video section
    content = _replace_yaml_key(content, "fps", str(visual.get("fps", 30)))

    # YouTube section
    content = _replace_yaml_key(content, "category_id", f'"{youtube.get("category_id", "28")}"')
    content = _replace_yaml_key(content, "privacy_status", f'"{youtube.get("privacy_status", "public")}"')
    content = _replace_yaml_key(content, "made_for_kids", str(youtube.get("made_for_kids", False)).lower())

    # Image generation
    content = _replace_yaml_key(content, "comfyui_url", f'"{comfyui.get("url", "http://127.0.0.1:8188")}"')
    content = _replace_yaml_key(content, "comfyui_checkpoint", f'"{comfyui.get("checkpoint", "realvisxlV50_v50LightningBakedvae.safetensors")}"')

    return content


# ── Main ─────────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(description="Sync unified_config.yaml to MPT and TST")
    parser.add_argument("--dry-run", action="store_true", help="Show diffs without applying")
    parser.add_argument("--section", type=str, default="all", help="Sync only a section (tts, llm, youtube, all)")
    args = parser.parse_args()

    if not UNIFIED_CONFIG.exists():
        print(f"ERROR: unified_config.yaml not found at {UNIFIED_CONFIG}")
        sys.exit(1)

    cfg = load_unified()
    print(f"Loaded unified config from {UNIFIED_CONFIG}")

    # ── MPT sync (non-destructive patch) ──
    mpt_path = _resolve(cfg["projects"]["mpt"]["path"])
    mpt_config = mpt_path / cfg["projects"]["mpt"]["config_file"]

    if mpt_config.exists():
        old_mpt = mpt_config.read_text()
    else:
        old_mpt = ""

    new_mpt_content = patch_mpt_toml(cfg, old_mpt)

    mpt_changed = old_mpt != new_mpt_content

    if mpt_changed:
        if args.dry_run:
            print(f"\n{'='*60}")
            print(f"MPT config.toml — CHANGES DETECTED")
            print(f"Target: {mpt_config}")
            print(f"{'='*60}")
            # Show a simple diff summary
            old_lines = set(old_mpt.splitlines())
            new_lines = set(new_mpt_content.splitlines())
            added = new_lines - old_lines
            removed = old_lines - new_lines
            if added:
                print(f"  + {len(added)} lines added")
                for line in sorted(added)[:10]:
                    print(f"    + {line}")
            if removed:
                print(f"  - {len(removed)} lines removed")
                for line in sorted(removed)[:10]:
                    print(f"    - {line}")
        else:
            # Write new config (preserve a backup)
            backup = mpt_config.with_suffix(".toml.bak")
            if mpt_config.exists():
                mpt_config.rename(backup)
            mpt_config.write_text(new_mpt_content)
            print(f"\n✅ MPT config.toml updated: {mpt_config}")
            print(f"   Backup saved: {backup}")
    else:
        print(f"\n⏭️  MPT config.toml — no changes needed")

    # ── TST sync (non-destructive patch) ──
    tst_path = _resolve(cfg["projects"]["tst"]["path"])
    tst_config = tst_path / cfg["projects"]["tst"]["config_file"]

    if tst_config.exists():
        old_tst_content = tst_config.read_text()
    else:
        old_tst_content = ""

    new_tst_content = patch_tst_config_yaml(cfg, old_tst_content)

    tst_changed = old_tst_content != new_tst_content

    if tst_changed:
        if args.dry_run:
            print(f"\n{'='*60}")
            print(f"TST config.yaml — CHANGES DETECTED")
            print(f"Target: {tst_config}")
            print(f"{'='*60}")
            print(f"  (YAML patching — {len(new_tst_content)} bytes new vs {len(old_tst_content)} bytes old)")
        else:
            backup = tst_config.with_suffix(".yaml.bak")
            if tst_config.exists():
                tst_config.rename(backup)
            tst_config.write_text(new_tst_content)
            print(f"\n✅ TST config.yaml updated: {tst_config}")
            print(f"   Backup saved: {backup}")
    else:
        print(f"\n⏭️  TST config.yaml — no changes needed")

    # ── Summary ──
    print(f"\n{'='*60}")
    if args.dry_run:
        print("DRY RUN — no files were modified. Run without --dry-run to apply.")
    else:
        if mpt_changed or tst_changed:
            print("✅ Sync complete — configs updated.")
        else:
            print("✅ Sync complete — everything was already up to date.")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()