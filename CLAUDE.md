# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

`DevIAFR` is the **config and orchestration layer** for an AI-driven video production pipeline for the YouTube channel "Dev IA FR" (French-language tech/AI content for developers). It does not contain the video-generation engine itself — it centralizes configuration for two sibling projects and propagates it to them:

- **MPT** (`MoneyPrinterTurbo`) — the video production engine, at `~/MyWorkProjectGithub/MoneyPrinterTurbo` (config: `config.toml`)
- **TST** (`TestShortYoutube`) — the quality/multi-channel layer, at `~/MyWorkDirectory/TestShortYoutube` (config: `config.yaml`)

`config/unified_config.yaml` is the single source of truth; `scripts/sync_config.py` patches the relevant keys into MPT's and TST's own config files non-destructively (regex/line-based patching that preserves unmanaged keys, with a `.bak` backup on every write).

This directory is not a git repository.

## Commands

```bash
# Preview what sync_config.py would change in MPT/TST configs, without writing
python scripts/sync_config.py --dry-run

# Apply the sync (writes MPT config.toml and TST config.yaml, with .bak backups)
python scripts/sync_config.py

# Sync only one section (e.g. tts, llm, youtube)
python scripts/sync_config.py --section tts

# Generate a 10s ElevenLabs voice sample using tts.elevenlabs settings from
# unified_config.yaml, validate it (ffprobe), and normalize to -16 LUFS.
# Falls back to Edge TTS if ElevenLabs isn't configured or the API call fails.
python scripts/test_voice.py
python scripts/test_voice.py --text "Texte custom à synthétiser"
python scripts/test_voice.py --api-key "xxx" --voice-id "xxx"   # override config
```

`scripts/unified_pipeline.py` (the actual production pipeline invocation, e.g. `--subject ... --channel dev_ia_fr --format long`) is referenced in the README but does not exist yet — it's tracked as a future ticket (UNIFY-03).

`test_voice.py` shells out to `ffprobe`/`ffmpeg`, which must be installed and on `PATH`.

```bash
# Alternative, fully local/free TTS path: voice cloning via RTVC
# (Real-Time-Voice-Cloning), instead of the ElevenLabs API used by test_voice.py.
python scripts/voice_clone_tts.py --text "Bonjour..." --ref ref_voice.wav --output out.wav
python scripts/voice_clone_tts.py --text "Bonjour..." --ref ref_voice.wav --output out.wav --normalize

# Pre-compute a reusable voice embedding instead of re-encoding the reference each time
python scripts/voice_clone_tts.py --encode-ref ref_voice.wav --save-embed embed.npy
python scripts/voice_clone_tts.py --text "Bonjour..." --load-embed embed.npy --output out.wav
```

`voice_clone_tts.py` requires a sibling repo at `~/MyWorkProjectGithub/Real-Time-Voice-Cloning` with its own venv and `saved_models/default/{encoder,synthesizer,vocoder}.pt`. It must effectively run with RTVC's own Python/venv (its `encoder`/`synthesizer`/`vocoder` packages are imported by adding RTVC's path to `sys.path` and `os.chdir`-ing into it), and it explicitly strips any `hermes` entries from `sys.path` first (`_clean_sys_path`) to avoid conflicting with the Hermes agent's own package versions. Default reference voice is expected at `storage/voice_samples/reference_voice.wav`; if absent it falls back to an RTVC sample voice and prints instructions for recording a real one. This is a second, independent TTS path from the ElevenLabs one in `test_voice.py` — the two are not unified through `unified_config.yaml`/`sync_config.py`.

## Architecture: how config propagation works

1. **`config/unified_config.yaml`** is the only file a human/agent should edit for cross-project settings (LLM provider/model, ElevenLabs TTS, script storytelling structure, visual/render pipeline priority, subtitles, sound design, encoding, YouTube upload/schedule, cross-platform repurposing, quality-score thresholds, anti-ban rules).
2. **`scripts/sync_config.py`** reads that file and calls two patch functions:
   - `patch_mpt_toml(cfg, existing_content)` — rewrites specific keys inside MPT's TOML `[app]`, `[elevenlabs]`, `[whisper]`, `[ui]` sections via regex, using `_replace_key_in_section` (finds the section, replaces the key if present, otherwise inserts it before the next section header).
   - `patch_tst_config_yaml(cfg, existing_content)` — rewrites specific top-level `key: value` lines in TST's YAML via `_replace_yaml_key` (plain regex substitution, not a YAML-aware writer).
   - Both patchers are **additive/surgical**: they only touch keys they know about, so anything MPT/TST manage independently is left alone. When adding a new field to `unified_config.yaml` that needs to reach MPT or TST, you must also add a corresponding line to the relevant patch function — nothing propagates automatically.
   - Every write replaces the target file after renaming the old one to `.bak` (e.g. `config.toml.bak`).
3. Because the two downstream repos live outside this directory (`~/MyWorkProjectGithub/MoneyPrinterTurbo`, `~/MyWorkDirectory/TestShortYoutube`), `sync_config.py` will silently treat a missing target config as an empty string (`old_mpt = ""`) rather than failing — check that the sibling repos actually exist at the paths declared under `projects.mpt.path` / `projects.tst.path` in `unified_config.yaml` before assuming a sync did something.

## Config structure to know

`unified_config.yaml` sections, in file order: `projects` (sibling repo paths), `channel` (branding/niche/tags), `branding` (colors/logo/intro/outro), `llm` (primary provider is Ollama by default, `humanizer_provider` is Gemini for humanization/complex scripts), `tts` (ElevenLabs is primary, Edge TTS is the fallback engine), `script` (mandatory storytelling structure with per-beat duration percentages, plus humanization flags), `visual` (render source priority list, ComfyUI params, transitions), `subtitles` (Whisper model config + burn-in style), `sound_design` (SFX/ducking/BGM), `post_processing`, `thumbnail`, `encoding`, `youtube` (upload schedule), `cross_platform` (TikTok/Instagram repurposing via Upload-Post, currently disabled), `quality` (min score gate + weights), `repurposing`, `analytics`, `competitor_watch`, and `anti_ban` (a checklist of hard rules — see below).

**Anti-ban rules are load-bearing, not aspirational.** They exist under `anti_ban:` in the config and are restated in the README: never use a free/default ElevenLabs voice (detectable → demonetization risk), never publish an LLM script without humanization (anecdotes/emotion/examples), never mass-upload without human review, one custom voice per channel. When touching TTS or script-generation logic, preserve these constraints rather than optimizing them away.

## Secrets

`tts.elevenlabs.api_key` and `cross_platform.upload_post.api_key` live directly in `config/unified_config.yaml` as plaintext fields (currently empty placeholders). Since this is not a git repo there's no `.gitignore` protection to rely on — be careful if this directory is ever put under version control or copied elsewhere.
