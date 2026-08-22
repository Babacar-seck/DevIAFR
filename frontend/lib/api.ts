const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// === Types ===

export interface Persona {
  id: string;
  name: string;
  niche: string;
  language: string;
  tone: string;
  quality_min: number;
  voice?: {
    engine: string;
    voice_id: string;
    style: string;
  };
  branding?: {
    colors?: {
      primary: string;
      secondary: string;
      accent: string;
    };
  };
  created_at: string;
  updated_at: string;
}

export interface Video {
  id: string;
  persona_id: string;
  subject: string;
  status: 'pending' | 'generating' | 'ready' | 'failed';
  script_path?: string;
  video_path?: string;
  thumbnail_path?: string;
  quality_score?: number;
  script_content?: string;
  error?: string;
  created_at: string;
  has_video?: boolean;
}

export interface SubjectSuggestion {
  subject: string;
  based_on_trend?: string;
  why_viral?: string;
}

export interface Stats {
  total_videos: number;
  videos_this_week: number;
  avg_quality_score: number;
  top_persona: string;
  total_personas: number;
}

// === API Functions ===

export async function getPersonas(): Promise<Persona[]> {
  const res = await fetch(`${API_URL}/api/personas`);
  if (!res.ok) throw new Error('Failed to fetch personas');
  return res.json();
}

export async function getPersona(id: string): Promise<Persona> {
  const res = await fetch(`${API_URL}/api/personas/${id}`);
  if (!res.ok) throw new Error(`Failed to fetch persona ${id}`);
  return res.json();
}

export async function createPersona(data: Partial<Persona>): Promise<Persona> {
  const res = await fetch(`${API_URL}/api/personas`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail || 'Failed to create persona');
  }
  return res.json();
}

export async function updatePersona(id: string, data: Partial<Persona>): Promise<Persona> {
  const res = await fetch(`${API_URL}/api/personas/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail || 'Failed to update persona');
  }
  return res.json();
}

export async function deletePersona(id: string): Promise<void> {
  const res = await fetch(`${API_URL}/api/personas/${id}`, {
    method: 'DELETE',
  });
  if (!res.ok) throw new Error(`Failed to delete persona ${id}`);
}

export async function getVideos(): Promise<Video[]> {
  const res = await fetch(`${API_URL}/api/videos`);
  if (!res.ok) throw new Error('Failed to fetch videos');
  return res.json();
}

export async function getVideo(id: string): Promise<Video> {
  const res = await fetch(`${API_URL}/api/videos/${id}`);
  if (!res.ok) throw new Error(`Failed to fetch video ${id}`);
  return res.json();
}

export async function generateVideo(
  personaId: string,
  subject: string,
  dryRun: boolean = false
): Promise<Video> {
  const res = await fetch(`${API_URL}/api/videos/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      persona_id: personaId,
      subject,
      dry_run: dryRun,
    }),
  });
  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail || 'Failed to generate video');
  }
  return res.json();
}

export async function suggestSubject(personaId: string): Promise<SubjectSuggestion> {
  const res = await fetch(
    `${API_URL}/api/videos/suggest-subject?persona_id=${encodeURIComponent(personaId)}`,
    { method: 'POST' }
  );
  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail || 'Failed to suggest subject');
  }
  return res.json();
}

export async function deleteVideo(id: string): Promise<void> {
  const res = await fetch(`${API_URL}/api/videos/${id}`, {
    method: 'DELETE',
  });
  if (!res.ok) throw new Error(`Failed to delete video ${id}`);
}

export async function getStats(): Promise<Stats> {
  const res = await fetch(`${API_URL}/api/videos/stats`);
  if (!res.ok) throw new Error('Failed to fetch stats');
  return res.json();
}

export function getDownloadUrl(videoId: string, type: 'video' | 'script' | 'thumbnail'): string {
  return `${API_URL}/api/videos/${videoId}/${type}`;
}
