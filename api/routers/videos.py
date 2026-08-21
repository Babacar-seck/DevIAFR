"""
routers/videos.py — Production, statut et téléchargement des vidéos (WEB-03, WEB-04).

Production synchrone (pas de Celery, cf. contraintes WEB-01) : la requête
POST /generate bloque jusqu'à la fin (ou jusqu'au timeout). Appelle
scripts/humanize_script.py puis, si dry_run=False, scripts/unified_pipeline.py
en subprocess (même approche d'isolation que run.sh — évite d'importer ces
scripts dans le process de l'API).
"""

from __future__ import annotations

import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

import db
from models.schemas import Stats, VideoGenerateRequest, VideoInfo, VideoListItem

DEVIAFR_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = DEVIAFR_ROOT / "scripts"
PERSONAS_DIR = DEVIAFR_ROOT / "config" / "personas"
OUTPUT_DIR = DEVIAFR_ROOT / "storage" / "output"

SCRIPT_TIMEOUT_S = 180
PRODUCTION_TIMEOUT_S = 600  # 10 minutes, cf. acceptation WEB-03

router = APIRouter()


def _row_to_info(row: dict) -> VideoInfo:
    return VideoInfo(
        id=row["id"],
        persona_id=row["persona_id"],
        subject=row["subject"],
        status=row["status"],
        script_path=row.get("script_path"),
        video_path=row.get("video_path"),
        thumbnail_path=row.get("thumbnail_path"),
        quality_score=row.get("quality_score"),
        script_content=row.get("script_content"),
        error=row.get("error"),
        created_at=datetime.fromisoformat(row["created_at"]),
        duration_s=row.get("duration_s"),
    )


@router.post("/generate", response_model=VideoInfo, status_code=201)
async def generate_video(request: VideoGenerateRequest):
    """Lance la production d'une vidéo (script humanisé + rendu si dry_run=False)."""
    persona_path = PERSONAS_DIR / f"{request.persona_id}.yaml"
    if not persona_path.exists():
        raise HTTPException(status_code=404, detail=f"Persona '{request.persona_id}' introuvable")

    video_id = uuid.uuid4().hex
    video_dir = OUTPUT_DIR / video_id
    video_dir.mkdir(parents=True, exist_ok=True)
    created_at = datetime.now(timezone.utc)

    db.insert_video({
        "id": video_id,
        "persona_id": request.persona_id,
        "subject": request.subject,
        "status": "generating",
        "created_at": created_at.isoformat(),
    })

    # Étape 1 : script humanisé (toujours nécessaire, dry_run ou non)
    script_path = video_dir / "script.txt"
    proc = subprocess.run(
        [sys.executable, str(SCRIPTS_DIR / "humanize_script.py"),
         "--subject", request.subject, "--output", str(script_path)],
        cwd=str(DEVIAFR_ROOT),
        capture_output=True, text=True, timeout=SCRIPT_TIMEOUT_S,
    )

    if proc.returncode != 0 or not script_path.exists():
        error = (proc.stderr or proc.stdout or "Échec génération script")[-500:]
        db.update_video(video_id, status="failed", error=error)
        row = db.get_video(video_id)
        return _row_to_info(row)

    script_content = script_path.read_text(encoding="utf-8")
    db.update_video(
        video_id,
        script_path=str(script_path.relative_to(DEVIAFR_ROOT)),
        script_content=script_content,
    )

    if request.dry_run:
        db.update_video(video_id, status="ready")
        row = db.get_video(video_id)
        return _row_to_info(row)

    # Étape 2 : production vidéo complète via unified_pipeline.py (nécessite MPT actif)
    try:
        proc = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "unified_pipeline.py"),
             "--script", str(script_path), "--channel", request.persona_id,
             "--subject", request.subject],
            cwd=str(DEVIAFR_ROOT),
            capture_output=True, text=True, timeout=PRODUCTION_TIMEOUT_S,
        )
    except subprocess.TimeoutExpired:
        db.update_video(video_id, status="failed", error="Timeout production (>10 min)")
        row = db.get_video(video_id)
        return _row_to_info(row)

    if proc.returncode != 0:
        error = (proc.stderr or proc.stdout or "Échec production vidéo")[-500:]
        db.update_video(video_id, status="failed", error=error)
        row = db.get_video(video_id)
        return _row_to_info(row)

    # Parse la sortie de unified_pipeline.py pour récupérer les chemins produits
    video_path = None
    thumbnail_path = None
    for line in proc.stdout.splitlines():
        if "Vidéo produite" in line and ":" in line:
            video_path = line.split(":", 1)[1].strip()
        if "Miniature" in line and ":" in line:
            thumbnail_path = line.split(":", 1)[1].strip()

    db.update_video(video_id, status="ready", video_path=video_path, thumbnail_path=thumbnail_path)
    row = db.get_video(video_id)
    return _row_to_info(row)


@router.get("/stats", response_model=Stats)
async def get_stats():
    """Statistiques globales (WEB-06)."""
    total_personas = len(list(PERSONAS_DIR.glob("*.yaml"))) if PERSONAS_DIR.exists() else 0
    stats = db.compute_stats(total_personas)
    return Stats(**stats)


@router.get("", response_model=list[VideoListItem])
async def list_videos(limit: int = 50):
    """Liste les vidéos produites (les plus récentes en premier)."""
    rows = db.list_videos(limit=limit)
    return [
        VideoListItem(
            id=row["id"],
            persona_id=row["persona_id"],
            subject=row["subject"],
            status=row["status"],
            quality_score=row.get("quality_score"),
            created_at=datetime.fromisoformat(row["created_at"]),
        )
        for row in rows
    ]


@router.get("/{video_id}", response_model=VideoInfo)
async def get_video(video_id: str):
    """Détail d'une vidéo produite."""
    row = db.get_video(video_id)
    if not row:
        raise HTTPException(status_code=404, detail="Vidéo introuvable")
    return _row_to_info(row)


@router.delete("/{video_id}", status_code=204)
async def delete_video(video_id: str):
    """Supprime une vidéo (métadonnées + dossier de sortie)."""
    row = db.get_video(video_id)
    if not row:
        raise HTTPException(status_code=404, detail="Vidéo introuvable")

    video_dir = OUTPUT_DIR / video_id
    if video_dir.exists():
        import shutil
        shutil.rmtree(video_dir, ignore_errors=True)

    db.delete_video(video_id)


def _resolve_asset(video_id: str, field: str) -> Path:
    row = db.get_video(video_id)
    if not row:
        raise HTTPException(status_code=404, detail="Vidéo introuvable")
    rel_path = row.get(field)
    if not rel_path:
        raise HTTPException(status_code=404, detail=f"{field} non disponible pour cette vidéo")
    path = Path(rel_path)
    if not path.is_absolute():
        path = DEVIAFR_ROOT / path
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Fichier introuvable : {path}")
    return path


@router.get("/{video_id}/download")
async def download_video(video_id: str):
    """Télécharge le fichier vidéo (streaming)."""
    path = _resolve_asset(video_id, "video_path")
    return FileResponse(path, media_type="video/mp4", filename=path.name)


@router.get("/{video_id}/script")
async def download_script(video_id: str):
    """Télécharge le script (.txt)."""
    path = _resolve_asset(video_id, "script_path")
    return FileResponse(path, media_type="text/plain", filename=path.name)


@router.get("/{video_id}/thumbnail")
async def download_thumbnail(video_id: str):
    """Télécharge la miniature (.png)."""
    path = _resolve_asset(video_id, "thumbnail_path")
    return FileResponse(path, media_type="image/png", filename=path.name)
