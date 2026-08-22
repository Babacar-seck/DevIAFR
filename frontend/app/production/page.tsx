'use client';

import { useEffect, useState } from 'react';
import { getPersonas, generateVideo, suggestSubject, Persona, Video, SubjectSuggestion } from '@/lib/api';

export default function ProductionPage() {
  const [personas, setPersonas] = useState<Persona[]>([]);
  const [selectedPersona, setSelectedPersona] = useState<string>('');
  const [subject, setSubject] = useState('');
  const [dryRun, setDryRun] = useState(false);
  const [loading, setLoading] = useState(false);
  const [video, setVideo] = useState<Video | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [suggesting, setSuggesting] = useState(false);
  const [suggestion, setSuggestion] = useState<SubjectSuggestion | null>(null);

  useEffect(() => {
    loadPersonas();
  }, []);

  async function loadPersonas() {
    try {
      const data = await getPersonas();
      setPersonas(data);
      if (data.length > 0) {
        setSelectedPersona(data[0].id);
      }
    } catch (err) {
      console.error('Erreur:', err);
    }
  }

  async function handleGenerate(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setVideo(null);

    try {
      setLoading(true);
      const result = await generateVideo(selectedPersona, subject, dryRun);
      setVideo(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erreur inconnue');
    } finally {
      setLoading(false);
    }
  }

  async function handleSuggestSubject() {
    if (!selectedPersona) return;
    setError(null);
    try {
      setSuggesting(true);
      const result = await suggestSubject(selectedPersona);
      setSubject(result.subject);
      setSuggestion(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erreur inconnue');
    } finally {
      setSuggesting(false);
    }
  }

  function handleReset() {
    setVideo(null);
    setSubject('');
    setSuggestion(null);
    setError(null);
  }

  const selectedPersonaData = personas.find(p => p.id === selectedPersona);

  return (
    <div className="max-w-3xl mx-auto">
      <h1 className="text-3xl font-bold mb-2">Production vidéo</h1>
      <p className="text-gray-400 mb-8">Produisez une nouvelle vidéo avec le persona de votre choix</p>

      {error && (
        <div className="mb-6 p-4 rounded bg-red-500/20 text-red-500 border border-red-500/30">
          ❌ {error}
        </div>
      )}

      {!video ? (
        <form onSubmit={handleGenerate} className="space-y-6">
          {/* Sélection persona */}
          <div>
            <label className="block text-sm font-medium mb-2">Persona</label>
            <select
              value={selectedPersona}
              onChange={(e) => setSelectedPersona(e.target.value)}
              className="w-full px-4 py-2 rounded bg-primary-light border border-primary-light focus:border-secondary focus:outline-none"
            >
              {personas.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name} — {p.niche}
                </option>
              ))}
            </select>
          </div>

          {/* Preview persona */}
          {selectedPersonaData && (
            <div className="p-4 rounded bg-primary-light/50 border border-primary-light">
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-gray-400">Ton:</span>{' '}
                  <span className="text-gray-300">{selectedPersonaData.tone}</span>
                </div>
                <div>
                  <span className="text-gray-400">Langue:</span>{' '}
                  <span className="text-gray-300">{selectedPersonaData.language.toUpperCase()}</span>
                </div>
                <div>
                  <span className="text-gray-400">Qualité min:</span>{' '}
                  <span className="text-gray-300">{selectedPersonaData.quality_min}/100</span>
                </div>
                {selectedPersonaData.voice && (
                  <div>
                    <span className="text-gray-400">Voix:</span>{' '}
                    <span className="text-gray-300">{selectedPersonaData.voice.engine}</span>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Sujet */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="block text-sm font-medium">
                Sujet de la vidéo <span className="text-red-500">*</span>
              </label>
              <button
                type="button"
                onClick={handleSuggestSubject}
                disabled={suggesting || !selectedPersona}
                className="text-xs px-3 py-1 rounded bg-primary-light border border-primary-light hover:border-secondary transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {suggesting ? '⏳ Analyse des tendances...' : '✨ Suggérer un sujet tendance'}
              </button>
            </div>
            <input
              type="text"
              required
              value={subject}
              onChange={(e) => {
                setSubject(e.target.value);
                setSuggestion(null);
              }}
              placeholder="ex: Les 5 erreurs fatales en architecture .NET"
              className="w-full px-4 py-2 rounded bg-primary-light border border-primary-light focus:border-secondary focus:outline-none"
            />
            {suggestion ? (
              <p className="text-xs text-secondary mt-1">
                📈 Basé sur : {suggestion.based_on_trend || 'tendances actuelles'}
                {suggestion.why_viral ? ` — ${suggestion.why_viral}` : ''}
              </p>
            ) : (
              <p className="text-xs text-gray-500 mt-1">
                Suggestions: "Comment investir à 25 ans", "Pourquoi 90% des gens échouent", etc.
              </p>
            )}
          </div>

          {/* Options */}
          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="dryRun"
              checked={dryRun}
              onChange={(e) => setDryRun(e.target.checked)}
              className="w-4 h-4"
            />
            <label htmlFor="dryRun" className="text-sm text-gray-300">
              Mode test (générer le script seulement, pas de vidéo)
            </label>
          </div>

          {/* Submit */}
          <button
            type="submit"
            disabled={loading || !subject}
            className="w-full px-6 py-3 bg-secondary text-primary-dark rounded font-semibold hover:bg-secondary-light transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? (
              <span className="flex items-center justify-center gap-2">
                <span className="animate-spin">⏳</span>
                Production en cours (5-10 min)...
              </span>
            ) : (
              '🎬 Produire la vidéo'
            )}
          </button>
        </form>
      ) : (
        <div className="space-y-6">
          {/* Succès */}
          <div className="p-4 rounded bg-green-500/20 text-green-500 border border-green-500/30">
            ✅ {video.status === 'ready' ? 'Vidéo produite avec succès !' : 'Script généré (mode test)'}
          </div>

          {/* Preview script */}
          {video.script_content && (
            <div>
              <h3 className="text-lg font-semibold mb-2">📄 Script</h3>
              <div className="p-4 rounded bg-primary-light/50 border border-primary-light max-h-96 overflow-y-auto">
                <pre className="text-sm text-gray-300 whitespace-pre-wrap">{video.script_content}</pre>
              </div>
            </div>
          )}

          {/* Preview vidéo */}
          {video.video_path && (
            <div>
              <h3 className="text-lg font-semibold mb-2">🎬 Vidéo</h3>
              <video
                controls
                className="w-full rounded bg-black"
                src={`http://localhost:8000/api/videos/${video.id}/download`}
              />
            </div>
          )}

          {/* Preview miniature */}
          {video.thumbnail_path && (
            <div>
              <h3 className="text-lg font-semibold mb-2">🖼️ Miniature</h3>
              <img
                src={`http://localhost:8000/api/videos/${video.id}/thumbnail`}
                alt="Miniature"
                className="w-full rounded"
              />
            </div>
          )}

          {/* Actions */}
          <div className="flex gap-4">
            {video.status === 'ready' && video.video_path && (
              <a
                href={`http://localhost:8000/api/videos/${video.id}/download`}
                target="_blank"
                className="flex-1 px-6 py-3 bg-secondary text-primary-dark rounded font-semibold hover:bg-secondary-light transition-colors text-center"
              >
                ⬇️ Télécharger la vidéo
              </a>
            )}
            <button
              onClick={handleReset}
              className="flex-1 px-6 py-3 bg-primary-light text-gray-300 rounded hover:bg-primary-light/70 transition-colors"
            >
              🔄 Produire une autre vidéo
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
