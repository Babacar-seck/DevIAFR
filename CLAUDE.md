# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

`DevIAFR` is the **config and orchestration layer** for an AI-driven, multi-persona video production pipeline (originally built for the YouTube channel "Dev IA FR", French-language tech/AI content, now generalized to 6 personas — see below). It centralizes configuration for two sibling projects and propagates it to them, and it now also orchestrates end-to-end video production itself:

- **MPT** (`MoneyPrinterTurbo`) — the video production engine, at `~/MyWorkProjectGithub/MoneyPrinterTurbo` (config: `config.toml`, REST API on `localhost:8080`)
- **TST** (`TestShortYoutube`) — the quality/multi-channel layer, at `~/MyWorkDirectory/TestShortYoutube` (config: `config.yaml`), whose `src.script_generator` is imported directly into DevIAFR's own Python process by `scripts/unified_pipeline.py` (a prior subprocess-isolation alternative, `scripts/_tst_bridge_runner.py`, was removed — direct import is the one and only integration path now; if TST's dependencies aren't installed in DevIAFR's environment, this import will fail)

`config/unified_config.yaml` is the single source of truth for MPT/TST-facing settings; `scripts/sync_config.py` patches the relevant keys into MPT's and TST's own config files non-destructively (regex/line-based patching that preserves unmanaged keys, with a `.bak` backup on every write).

Beyond config propagation, this repo also contains:

- **`scripts/unified_pipeline.py`** — the real end-to-end production pipeline (script generation → RTVC narration → MPT video rendering → SFX post-processing → thumbnail → upload); see the `unified_pipeline.py` examples under "Commands" below.
- **`config/personas/*.yaml`** — a multi-persona system (6 personas as of this writing: `dev_ia_fr`, `finance_par_age`, `psy_stick_fr`, `coran_lumiere_fr`, `mini_melodies_fr`, `motivation_fr`), each a deep-merge overlay on top of `unified_config.yaml`'s defaults (channel branding, voice, storytelling structure, quality thresholds). `run.sh` is the interactive/CLI entry point that selects a persona and drives the pipeline; `scripts/select_persona.py` performs the merge.
- **`api/`** — a FastAPI backend (`api/main.py`, `api/routers/{personas,videos}.py`, `api/db.py` for SQLite-backed video metadata) exposing persona CRUD and video generation/status endpoints.
- **`frontend/`** — a Next.js web UI consuming that API.

This directory **is** a git repository (`origin` → `github.com/Babacar-seck/DevIAFR`) — despite what earlier revisions of this file claimed.

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

```bash
# Run the full production pipeline for a persona (script → RTVC narration →
# MPT render → SFX → thumbnail → upload); interactive if no flags given
./run.sh
./run.sh --persona dev_ia_fr --subject "Comment créer une API REST .NET"
./run.sh --dry-run              # generate the script only, skip MPT rendering
./run.sh --list-personas
./run.sh --check                # environment check only

# Same pipeline, invoked directly (used internally by run.sh and by
# api/routers/videos.py's POST /videos/generate)
python scripts/unified_pipeline.py --subject "..." --channel dev_ia_fr
python scripts/unified_pipeline.py --script path/to/script.txt --channel dev_ia_fr
```

`test_voice.py` shells out to `ffprobe`/`ffmpeg`, which must be installed and on `PATH`.

```bash
# Local/free TTS path via RTVC (Real-Time-Voice-Cloning) — this is what
# unified_pipeline.py actually calls (generate_narration_rtvc(), which shells
# out to voice_clone_rtvc.py) when a persona's config/personas/<id>.yaml has
# tts.engine: "rtvc" (the project-wide default in unified_config.yaml) and a
# voice.voice_sample set.
python scripts/voice_clone_rtvc.py --persona dev_ia_fr --text "Bonjour..." --output out.wav
python scripts/voice_clone_rtvc.py --voice-ref ref_voice.wav --text "Bonjour..." --output out.wav

# A second, mostly-overlapping RTVC CLI also exists (embedding pre-compute,
# --normalize) but is NOT called by unified_pipeline.py or run.sh — nothing
# currently wires it in. Treat as a known duplicate, not the production path:
python scripts/voice_clone_tts.py --text "Bonjour..." --ref ref_voice.wav --output out.wav --normalize
python scripts/voice_clone_tts.py --encode-ref ref_voice.wav --save-embed embed.npy
```

Both RTVC scripts require a sibling repo at `~/MyWorkProjectGithub/Real-Time-Voice-Cloning` with its own venv and `saved_models/default/{encoder,synthesizer,vocoder}.pt`, and must run with RTVC's own Python (`tts.rtvc.venv_python` in `unified_config.yaml`) since `encoder`/`synthesizer`/`vocoder` are imported via `sys.path` + `os.chdir` into that repo. `voice_clone_tts.py` additionally strips any `hermes` entries from `sys.path` first (`_clean_sys_path`) to avoid conflicting with the Hermes agent's own package versions — `voice_clone_rtvc.py` does not do this. This is a fully separate, local-only TTS path from ElevenLabs (`tts.elevenlabs.*` in config) and Edge TTS (`tts.fallback_engine`) — `sync_config.py` does not propagate `tts.rtvc.*` to MPT/TST; RTVC only runs inside DevIAFR's own pipeline.

## Architecture: how config propagation works

1. **`config/unified_config.yaml`** is the only file a human/agent should edit for cross-project settings (LLM provider/model, ElevenLabs TTS, script storytelling structure, visual/render pipeline priority, subtitles, sound design, encoding, YouTube upload/schedule, cross-platform repurposing, quality-score thresholds, anti-ban rules).
2. **`scripts/sync_config.py`** reads that file and calls two patch functions:
   - `patch_mpt_toml(cfg, existing_content)` — rewrites specific keys inside MPT's TOML `[app]`, `[elevenlabs]`, `[whisper]`, `[ui]` sections via regex, using `_replace_key_in_section` (finds the section, replaces the key if present, otherwise inserts it before the next section header).
   - `patch_tst_config_yaml(cfg, existing_content)` — rewrites specific top-level `key: value` lines in TST's YAML via `_replace_yaml_key` (plain regex substitution, not a YAML-aware writer).
   - Both patchers are **additive/surgical**: they only touch keys they know about, so anything MPT/TST manage independently is left alone. When adding a new field to `unified_config.yaml` that needs to reach MPT or TST, you must also add a corresponding line to the relevant patch function — nothing propagates automatically.
   - Every write replaces the target file after renaming the old one to `.bak` (e.g. `config.toml.bak`).
3. Because the two downstream repos live outside this directory (`~/MyWorkProjectGithub/MoneyPrinterTurbo`, `~/MyWorkDirectory/TestShortYoutube`), `sync_config.py` will silently treat a missing target config as an empty string (`old_mpt = ""`) rather than failing — check that the sibling repos actually exist at the paths declared under `projects.mpt.path` / `projects.tst.path` in `unified_config.yaml` before assuming a sync did something.

## Config structure to know

`unified_config.yaml` sections, in file order: `projects` (sibling repo paths), `channel` (branding/niche/tags), `branding` (colors/logo/intro/outro), `llm` (primary provider is Ollama by default, `humanizer_provider` is Gemini for humanization/complex scripts), `tts` (`engine: "rtvc"` is the project-wide default — 100% local/free voice cloning; ElevenLabs is now the optional paid alternative under `tts.elevenlabs.*`, Edge TTS is the final fallback under `tts.fallback_engine`), `script` (mandatory storytelling structure with per-beat duration percentages, plus humanization flags), `visual` (render source priority list, ComfyUI params, transitions), `subtitles` (Whisper model config + burn-in style), `sound_design` (SFX/ducking/BGM — actually wired into `unified_pipeline.py::post_process_sfx()` via `scripts/sfx_designer.py`, which detects scene cuts, procedurally synthesizes a whoosh/impact/pop/riser/transition SFX library into `storage/sfx/`, and can sidechain-duck a BGM track), `post_processing` (color grading via `scripts/color_grading.py`, config-driven single LUT — no per-channel LUT map exists despite what an older duplicate script, `color_grade.py`, assumed; that script was deleted), `thumbnail`, `encoding`, `youtube` (upload schedule), `cross_platform` (TikTok/Instagram publishing via the Upload-Post API, currently disabled; `scripts/cross_publish.py` is the implementation that matches this config shape — a duplicate, `cross_platform.py`, which checked non-existent config keys and shelled out to a script inside MPT, was deleted), `quality` (min score gate + weights), `repurposing`, `analytics`, `competitor_watch`, and `anti_ban` (a checklist of hard rules — see below).

`config/personas/*.yaml` sits alongside `unified_config.yaml` as a second, per-persona config layer (not one of the sections above) — see "What this repo is". Each persona's `voice:` block includes both machine params (`engine`, `voice_id`, `voice_sample`, `speed`) and free-text voice-direction fields (`ton`, `accent`, `age_genre`, `prompt_specifique`) intended for briefing a human voice actor or a more expressive TTS prompt — the latter four are not yet consumed by any synthesis code, only stored and round-tripped through the personas CRUD API (`api/routers/personas.py`).

**Anti-ban rules are load-bearing, not aspirational.** They exist under `anti_ban:` in the config and are restated in the README: never use a free/default voice for narration (detectable → demonetization risk — this now applies to RTVC as much as it did to ElevenLabs: a voice cloned from a generic/stock reference is still a "default" voice in spirit), never publish an LLM script without humanization (anecdotes/emotion/examples), never mass-upload without human review, one custom voice per channel. When touching TTS or script-generation logic, preserve these constraints rather than optimizing them away.

## Secrets

`tts.elevenlabs.api_key` and `cross_platform.upload_post.api_key` live directly in `config/unified_config.yaml` as plaintext fields (currently empty placeholders). **This file is git-tracked** (`git ls-files config/unified_config.yaml` confirms it) — filling in a real key here and committing would put it in git history permanently. Move real secrets to environment variables or a gitignored override file before filling these in for actual use; don't just rely on the placeholders staying empty.
