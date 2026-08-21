'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { getPersona, updatePersona, deletePersona, Persona } from '@/lib/api';

export default function EditPersonaPage() {
  const params = useParams();
  const router = useRouter();
  const personaId = params.id as string;

  const [persona, setPersona] = useState<Persona | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const [form, setForm] = useState({
    name: '',
    niche: '',
    language: 'fr',
    tone: '',
    quality_min: 70,
  });

  useEffect(() => {
    loadPersona();
  }, [personaId]);

  async function loadPersona() {
    try {
      setLoading(true);
      const data = await getPersona(personaId);
      setPersona(data);
      setForm({
        name: data.name,
        niche: data.niche,
        language: data.language,
        tone: data.tone,
        quality_min: data.quality_min,
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erreur inconnue');
    } finally {
      setLoading(false);
    }
  }

  function handleChange(field: string, value: string | number) {
    setForm((prev) => ({ ...prev, [field]: value }));
    setSuccess(false);
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSuccess(false);

    try {
      setSaving(true);
      await updatePersona(personaId, form);
      setSuccess(true);
      setTimeout(() => setSuccess(false), 3000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erreur inconnue');
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete() {
    if (!confirm(`Supprimer le persona "${persona?.name}" ? Cette action est irréversible.`)) {
      return;
    }

    try {
      await deletePersona(personaId);
      router.push('/personas');
    } catch (err) {
      alert('Erreur lors de la suppression');
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-secondary"></div>
      </div>
    );
  }

  if (!persona) {
    return (
      <div className="text-center py-12">
        <p className="text-red-500">Persona non trouvé</p>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold mb-2">Modifier {persona.name}</h1>
          <p className="text-gray-400">ID: <code className="text-secondary">{persona.id}</code></p>
        </div>
        <button
          onClick={handleDelete}
          className="px-4 py-2 bg-red-500/20 text-red-500 rounded hover:bg-red-500/30 transition-colors"
        >
          🗑️ Supprimer
        </button>
      </div>

      {error && (
        <div className="mb-6 p-4 rounded bg-red-500/20 text-red-500 border border-red-500/30">
          ❌ {error}
        </div>
      )}

      {success && (
        <div className="mb-6 p-4 rounded bg-green-500/20 text-green-500 border border-green-500/30">
          ✅ Modifications sauvegardées
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Nom */}
        <div>
          <label className="block text-sm font-medium mb-2">Nom</label>
          <input
            type="text"
            value={form.name}
            onChange={(e) => handleChange('name', e.target.value)}
            className="w-full px-4 py-2 rounded bg-primary-light border border-primary-light focus:border-secondary focus:outline-none"
          />
        </div>

        {/* Niche */}
        <div>
          <label className="block text-sm font-medium mb-2">Niche</label>
          <input
            type="text"
            value={form.niche}
            onChange={(e) => handleChange('niche', e.target.value)}
            className="w-full px-4 py-2 rounded bg-primary-light border border-primary-light focus:border-secondary focus:outline-none"
          />
        </div>

        {/* Langue */}
        <div>
          <label className="block text-sm font-medium mb-2">Langue</label>
          <select
            value={form.language}
            onChange={(e) => handleChange('language', e.target.value)}
            className="w-full px-4 py-2 rounded bg-primary-light border border-primary-light focus:border-secondary focus:outline-none"
          >
            <option value="fr">Français</option>
            <option value="en">Anglais</option>
            <option value="es">Espagnol</option>
          </select>
        </div>

        {/* Ton */}
        <div>
          <label className="block text-sm font-medium mb-2">Ton</label>
          <textarea
            value={form.tone}
            onChange={(e) => handleChange('tone', e.target.value)}
            rows={3}
            className="w-full px-4 py-2 rounded bg-primary-light border border-primary-light focus:border-secondary focus:outline-none resize-none"
          />
        </div>

        {/* Qualité minimum */}
        <div>
          <label className="block text-sm font-medium mb-2">
            Score qualité minimum: <span className="text-secondary font-bold">{form.quality_min}/100</span>
          </label>
          <input
            type="range"
            min="0"
            max="100"
            value={form.quality_min}
            onChange={(e) => handleChange('quality_min', parseInt(e.target.value))}
            className="w-full"
          />
        </div>

        {/* Actions */}
        <div className="flex gap-4 pt-6">
          <button
            type="submit"
            disabled={saving}
            className="flex-1 px-6 py-3 bg-secondary text-primary-dark rounded font-semibold hover:bg-secondary-light transition-colors disabled:opacity-50"
          >
            {saving ? 'Sauvegarde...' : 'Sauvegarder'}
          </button>
          <button
            type="button"
            onClick={() => router.push('/personas')}
            className="px-6 py-3 bg-primary-light text-gray-300 rounded hover:bg-primary-light/70 transition-colors"
          >
            Retour
          </button>
        </div>
      </form>
    </div>
  );
}
