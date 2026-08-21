"""
routers/personas.py — CRUD des personas (WEB-02).

Les personas sont stockés en YAML dans config/personas/*.yaml, avec la
structure imbriquée déjà utilisée par select_persona.py et run.sh
(channel.niche/language, voice.engine/voice_id, script.storytelling.structure,
quality.min_score) — pas la forme aplatie du modèle Pydantic exposé par
l'API, pour rester compatible avec le reste du pipeline (select_persona.py,
sync_config.py) qui lit ces fichiers directement.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path

import yaml
from fastapi import APIRouter, HTTPException

from models.schemas import (
    Persona,
    PersonaCreate,
    PersonaUpdate,
    ScriptConfig,
    StorytellingStep,
    VoiceConfig,
)

PERSONAS_DIR = Path(__file__).resolve().parents[2] / "config" / "personas"

router = APIRouter()


def _persona_path(persona_id: str) -> Path:
    return PERSONAS_DIR / f"{persona_id}.yaml"


def _yaml_to_persona(persona_id: str, raw: dict, file_path: Path) -> Persona:
    """Convertit la structure YAML imbriquée vers le schéma API aplati."""
    channel = raw.get("channel", {})
    branding_colors = raw.get("branding", {}).get("colors", {})
    voice_raw = raw.get("voice", {})
    script_raw = raw.get("script", {})
    structure_raw = script_raw.get("storytelling", {}).get("structure", [])
    quality_raw = raw.get("quality", {})

    stat = file_path.stat()

    return Persona(
        id=raw.get("id", persona_id),
        name=raw.get("name", persona_id),
        niche=channel.get("niche", ""),
        language=channel.get("language", "fr"),
        tone=script_raw.get("tone", "conversationnel"),
        voice=VoiceConfig(**{
            "engine": voice_raw.get("engine", "elevenlabs"),
            "voice_id": voice_raw.get("voice_id", ""),
            "style": voice_raw.get("style", "confident"),
            "speed": voice_raw.get("speed", 1.0),
            "pitch": voice_raw.get("pitch", 0),
            "ton": voice_raw.get("ton"),
            "accent": voice_raw.get("accent"),
            "age_genre": voice_raw.get("age_genre"),
            "prompt_specifique": voice_raw.get("prompt_specifique"),
        }) if voice_raw else None,
        branding={"colors": branding_colors} if branding_colors else None,
        script=ScriptConfig(
            tone=script_raw.get("tone", "conversationnel, expert"),
            structure=[
                StorytellingStep(
                    name=step.get("name", ""),
                    duration_pct=step.get("duration_pct", 0),
                    description=step.get("description", ""),
                )
                for step in structure_raw
            ],
        ),
        quality_min=quality_raw.get("min_score", 70),
        created_at=datetime.fromtimestamp(stat.st_ctime, tz=timezone.utc),
        updated_at=datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc),
        file_path=str(file_path.relative_to(PERSONAS_DIR.parent.parent)),
    )


def _persona_to_yaml(data: PersonaCreate) -> dict:
    """Convertit le schéma API aplati vers la structure YAML imbriquée."""
    voice = data.voice or VoiceConfig()
    branding_colors = (data.branding or {}).get("colors", {}) if data.branding else {}
    script = data.script or ScriptConfig()

    return {
        "name": data.name,
        "id": data.id,
        "channel": {
            "name": data.name,
            "niche": data.niche,
            "language": data.language,
        },
        "branding": {
            "colors": {
                "primary": branding_colors.get("primary", "#1a1a2e"),
                "accent": branding_colors.get("accent", "#00d4ff"),
                "secondary": branding_colors.get("secondary", "#7b2cbf"),
                "text": branding_colors.get("text", "#ffffff"),
            }
        },
        "voice": {
            "engine": voice.engine,
            "voice_id": voice.voice_id,
            "style": voice.style,
            "speed": voice.speed,
            "pitch": voice.pitch,
            "ton": voice.ton,
            "accent": voice.accent,
            "age_genre": voice.age_genre,
            "prompt_specifique": voice.prompt_specifique,
        },
        "script": {
            "tone": data.tone or script.tone,
            "storytelling": {
                "structure": [
                    {
                        "name": step.name,
                        "duration_pct": step.duration_pct,
                        "description": step.description,
                    }
                    for step in script.structure
                ]
            },
        },
        "quality": {"min_score": data.quality_min},
    }


def _load_raw(persona_id: str) -> dict:
    path = _persona_path(persona_id)
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Persona '{persona_id}' introuvable")
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


@router.get("", response_model=list[Persona])
async def list_personas():
    """Liste tous les personas disponibles."""
    PERSONAS_DIR.mkdir(parents=True, exist_ok=True)
    personas = []
    for yaml_file in sorted(PERSONAS_DIR.glob("*.yaml")):
        with open(yaml_file, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f) or {}
        personas.append(_yaml_to_persona(yaml_file.stem, raw, yaml_file))
    return personas


@router.get("/{persona_id}", response_model=Persona)
async def get_persona(persona_id: str):
    """Récupère un persona spécifique."""
    raw = _load_raw(persona_id)
    return _yaml_to_persona(persona_id, raw, _persona_path(persona_id))


@router.post("", response_model=Persona, status_code=201)
async def create_persona(data: PersonaCreate):
    """Crée un nouveau persona."""
    if not re.match(r"^[a-z0-9_]+$", data.id):
        raise HTTPException(status_code=422, detail="id doit être en snake_case (a-z0-9_)")

    path = _persona_path(data.id)
    if path.exists():
        raise HTTPException(status_code=422, detail=f"Persona '{data.id}' existe déjà")

    PERSONAS_DIR.mkdir(parents=True, exist_ok=True)
    yaml_content = _persona_to_yaml(data)
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(yaml_content, f, allow_unicode=True, sort_keys=False)

    return _yaml_to_persona(data.id, yaml_content, path)


@router.put("/{persona_id}", response_model=Persona)
async def update_persona(persona_id: str, data: PersonaUpdate):
    """Met à jour un persona existant (fusion partielle)."""
    raw = _load_raw(persona_id)
    path = _persona_path(persona_id)
    current = _yaml_to_persona(persona_id, raw, path)

    merged = current.model_dump(exclude={"created_at", "updated_at", "file_path"})
    updates = data.model_dump(exclude_unset=True)
    merged.update({k: v for k, v in updates.items() if v is not None})

    create_payload = PersonaCreate(**merged)
    yaml_content = _persona_to_yaml(create_payload)
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(yaml_content, f, allow_unicode=True, sort_keys=False)

    return _yaml_to_persona(persona_id, yaml_content, path)


@router.delete("/{persona_id}", status_code=204)
async def delete_persona(persona_id: str):
    """Supprime un persona."""
    path = _persona_path(persona_id)
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Persona '{persona_id}' introuvable")
    path.unlink()
