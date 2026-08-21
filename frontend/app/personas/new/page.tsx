'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { createPersona } from '@/lib/api';

export default function NewPersonaPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [form, setForm] = useState({
    name: '',
    id: '',
    niche: '',
    language: 'fr',
    tone: 'conversationnel',
    quality_min: 70,
  });

  function generateId(name: string): string {
    return name
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, '_')
      .replace(/^_|_$/g, '');
  }

  function handleChange(field: string, value: string | number) {
    setForm((prev) => {
      const updated = { ...prev, [field]: value };
      // Auto-générer l'ID depuis le nom
      if (field === 'name') {
        updated.id = generateId(value as string);
      }
      return updated;
    });
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);

    try {
      setLoading(true);
      await createPersona(form);
      router.push('/personas');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erreur inconnue');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-2xl mx-auto">
      <h1 className="text-3xl font-bold mb-2">Nouveau persona</h1>
      <p className="text-gray-400 mb-8">Créez un nouveau persona pour votre production vidéo</p>

      {error && (
        <div className="mb-6 p-4 rounded bg-red-500/20 text-red-500 border border-red-500/30">
          ❌ {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Nom */}
        <div>
          <label className="block text-sm font-medium mb-2">
            Nom <span className="text-red-500">*</span>
          </label>
          <input
            type="text"
            required
            value={form.name}
            onChange={(e) => handleChange('name', e.target.value)}
            placeholder="ex: Crypto FR"
            className="w-full px-4 py-2 rounded bg-primary-light border border-primary-light focus:border-secondary focus:outline-none"
          />
        </div>

        {/* ID */}
        <div>
          <label className="block text-sm font-medium mb-2">
            ID <span className="text-red-500">*</span>
          </label>
          <input
            type="text"
            required
            value={form.id}
            onChange={(e) => handleChange('id', e.target.value)}
            placeholder="ex: crypto_fr"
            pattern="^[a-z0-9_]+$"
            className="w-full px-4 py-2 rounded bg-primary-light border border-primary-light focus:border-secondary focus:outline-none font-mono"
          />
          <p className="text-xs text-gray-500 mt-1">Lettres minuscules, chiffres et underscores uniquement</p>
        </div>

        {/* Niche */}
        <div>
          <label className="block text-sm font-medium mb-2">Niche</label>
          <input
            type="text"
            value={form.niche}
            onChange={(e) => handleChange('niche', e.target.value)}
            placeholder="ex: Cryptomonnaies / Finance"
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
            placeholder="ex: conversationnel, expert, pédagogique"
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
          <div className="flex justify-between text-xs text-gray-500 mt-1">
            <span>0 (aucun filtre)</span>
            <span>100 (parfait)</span>
          </div>
        </div>

        {/* Actions */}
        <div className="flex gap-4 pt-6">
          <button
            type="submit"
            disabled={loading}
            className="flex-1 px-6 py-3 bg-secondary text-primary-dark rounded font-semibold hover:bg-secondary-light transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Création...' : 'Créer le persona'}
          </button>
          <button
            type="button"
            onClick={() => router.push('/personas')}
            className="px-6 py-3 bg-primary-light text-gray-300 rounded hover:bg-primary-light/70 transition-colors"
          >
            Annuler
          </button>
        </div>
      </form>
    </div>
  );
}
