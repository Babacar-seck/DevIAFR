"""
db.py — Stockage SQLite des métadonnées vidéos pour l'API DevIAFR.

Stockage local simple (pas de PostgreSQL, cf. contraintes WEB-01/WEB-04).
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

DB_PATH = Path(__file__).resolve().parent.parent / "storage" / "api_videos.db"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS videos (
    id TEXT PRIMARY KEY,
    persona_id TEXT NOT NULL,
    subject TEXT NOT NULL,
    status TEXT NOT NULL,
    script_path TEXT,
    video_path TEXT,
    thumbnail_path TEXT,
    quality_score INTEGER,
    script_content TEXT,
    error TEXT,
    created_at TEXT NOT NULL,
    duration_s REAL
);
"""


@contextmanager
def _connect() -> Iterator[sqlite3.Connection]:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with _connect() as conn:
        conn.execute(_SCHEMA)


def insert_video(video: dict[str, Any]) -> None:
    with _connect() as conn:
        conn.execute(
            """INSERT INTO videos
               (id, persona_id, subject, status, script_path, video_path,
                thumbnail_path, quality_score, script_content, error, created_at, duration_s)
               VALUES (:id, :persona_id, :subject, :status, :script_path, :video_path,
                       :thumbnail_path, :quality_score, :script_content, :error, :created_at, :duration_s)""",
            {
                "id": video["id"],
                "persona_id": video["persona_id"],
                "subject": video["subject"],
                "status": video["status"],
                "script_path": video.get("script_path"),
                "video_path": video.get("video_path"),
                "thumbnail_path": video.get("thumbnail_path"),
                "quality_score": video.get("quality_score"),
                "script_content": video.get("script_content"),
                "error": video.get("error"),
                "created_at": video.get("created_at", datetime.now(timezone.utc).isoformat()),
                "duration_s": video.get("duration_s"),
            },
        )


def update_video(video_id: str, **fields: Any) -> None:
    if not fields:
        return
    set_clause = ", ".join(f"{key} = :{key}" for key in fields)
    with _connect() as conn:
        conn.execute(
            f"UPDATE videos SET {set_clause} WHERE id = :id",
            {**fields, "id": video_id},
        )


def get_video(video_id: str) -> dict[str, Any] | None:
    with _connect() as conn:
        row = conn.execute("SELECT * FROM videos WHERE id = ?", (video_id,)).fetchone()
        return dict(row) if row else None


def list_videos(limit: int = 50) -> list[dict[str, Any]]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM videos ORDER BY created_at DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(row) for row in rows]


def delete_video(video_id: str) -> bool:
    with _connect() as conn:
        cur = conn.execute("DELETE FROM videos WHERE id = ?", (video_id,))
        return cur.rowcount > 0


def compute_stats(total_personas: int) -> dict[str, Any]:
    with _connect() as conn:
        total = conn.execute("SELECT COUNT(*) AS n FROM videos").fetchone()["n"]

        week_ago = datetime.now(timezone.utc).timestamp() - 7 * 86400
        rows = conn.execute("SELECT created_at, quality_score, persona_id FROM videos").fetchall()

        videos_this_week = 0
        scores = []
        persona_counts: dict[str, int] = {}
        for row in rows:
            try:
                created = datetime.fromisoformat(row["created_at"]).timestamp()
            except (TypeError, ValueError):
                created = 0
            if created >= week_ago:
                videos_this_week += 1
            if row["quality_score"] is not None:
                scores.append(row["quality_score"])
            persona_counts[row["persona_id"]] = persona_counts.get(row["persona_id"], 0) + 1

        top_persona = max(persona_counts, key=persona_counts.get) if persona_counts else ""
        avg_score = sum(scores) / len(scores) if scores else 0.0

        return {
            "total_videos": total,
            "videos_this_week": videos_this_week,
            "avg_quality_score": round(avg_score, 1),
            "top_persona": top_persona,
            "total_personas": total_personas,
        }
