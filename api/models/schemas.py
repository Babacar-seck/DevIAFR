"""
Schémas Pydantic pour l'API DevIAFR.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


# === Persona Schemas ===

class StorytellingStep(BaseModel):
    """Étape de structure storytelling."""
    name: str
    duration_pct: int = Field(ge=0, le=100)
    description: str


class ScriptConfig(BaseModel):
    """Configuration du script."""
    tone: str = "conversationnel, expert"
    structure: list[StorytellingStep] = []


class BrandingColors(BaseModel):
    """Couleurs du branding."""
    primary: str = "#1a1a2e"
    secondary: str = "#00d4ff"
    accent: str = "#7b2cbf"
    text: str = "#ffffff"


class VoiceConfig(BaseModel):
    """Configuration voix."""
    engine: str = "elevenlabs"
    voice_id: str = ""
    style: str = "confident"
    speed: float = 1.0
    pitch: int = 0
    ton: Optional[str] = None
    accent: Optional[str] = None
    age_genre: Optional[str] = None
    prompt_specifique: Optional[str] = None


class PersonaBase(BaseModel):
    """Champs de base d'un persona."""
    name: str = Field(..., min_length=1, max_length=100)
    id: str = Field(..., pattern=r"^[a-z0-9_]+$")
    niche: str = ""
    language: str = "fr"
    tone: str = "conversationnel"
    voice: Optional[VoiceConfig] = None
    branding: Optional[dict] = None
    script: Optional[ScriptConfig] = None
    quality_min: int = Field(default=70, ge=0, le=100)


class PersonaCreate(PersonaBase):
    """Schéma pour créer un persona."""
    pass


class PersonaUpdate(BaseModel):
    """Schéma pour mettre à jour un persona (champs optionnels)."""
    name: Optional[str] = None
    niche: Optional[str] = None
    language: Optional[str] = None
    tone: Optional[str] = None
    voice: Optional[VoiceConfig] = None
    branding: Optional[dict] = None
    script: Optional[ScriptConfig] = None
    quality_min: Optional[int] = Field(default=None, ge=0, le=100)


class Persona(PersonaBase):
    """Schéma complet d'un persona."""
    created_at: datetime
    updated_at: datetime
    file_path: str


# === Video Schemas ===

class VideoGenerateRequest(BaseModel):
    """Requête pour générer une vidéo."""
    persona_id: str = Field(..., min_length=1)
    subject: str = Field(..., min_length=5, max_length=500)
    dry_run: bool = False
    auto_upload: bool = False


class VideoInfo(BaseModel):
    """Informations sur une vidéo produite."""
    id: str
    persona_id: str
    subject: str
    status: str  # pending | generating | ready | failed
    script_path: Optional[str] = None
    video_path: Optional[str] = None
    thumbnail_path: Optional[str] = None
    quality_score: Optional[int] = None
    script_content: Optional[str] = None
    error: Optional[str] = None
    created_at: datetime
    duration_s: Optional[float] = None


class SubjectSuggestion(BaseModel):
    """Sujet de vidéo suggéré par IA à partir des tendances réelles (Google Trends)."""
    subject: str
    based_on_trend: Optional[str] = None
    why_viral: Optional[str] = None


class VideoListItem(BaseModel):
    """Vidéo dans une liste (métadonnées légères)."""
    id: str
    persona_id: str
    subject: str
    status: str
    quality_score: Optional[int] = None
    created_at: datetime
    has_video: bool = False


class Stats(BaseModel):
    """Statistiques globales."""
    total_videos: int
    videos_this_week: int
    avg_quality_score: float
    top_persona: str
    total_personas: int
