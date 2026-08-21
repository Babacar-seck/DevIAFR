'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { getPersonas, Persona } from '@/lib/api';

export default function PersonasPage() {
  const [personas, setPersonas] = useState<Persona[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadPersonas();
  }, []);

  async function loadPersonas() {
    try {
      setLoading(true);
      const data = await getPersonas();
      setPersonas(data);
    } catch (err) {
      console.error('Erreur:', err);
    } finally {
      setLoading(false);
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-secondary"></div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold mb-2">Personas</h1>
          <p className="text-gray-400">Gérez vos personas de production vidéo</p>
        </div>
        <Link
          href="/personas/new"
          className="px-4 py-2 bg-secondary text-primary-dark rounded hover:bg-secondary-light transition-colors font-semibold"
        >
          + Nouveau persona
        </Link>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {personas.map((persona) => (
          <Link
            key={persona.id}
            href={`/personas/${persona.id}`}
            className="block bg-primary-light/50 rounded-lg p-6 hover:bg-primary-light transition-colors border border-transparent hover:border-secondary/50"
          >
            <div className="flex items-start justify-between mb-4">
              <div>
                <h3 className="text-xl font-semibold mb-1">{persona.name}</h3>
                <p className="text-sm text-gray-400">{persona.niche}</p>
              </div>
              <span className="px-2 py-1 rounded bg-accent/20 text-accent text-xs">
                {persona.language.toUpperCase()}
              </span>
            </div>

            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-400">Ton:</span>
                <span className="text-gray-300">{persona.tone}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Qualité min:</span>
                <span className="text-gray-300">{persona.quality_min}/100</span>
              </div>
              {persona.voice && (
                <div className="flex justify-between">
                  <span className="text-gray-400">Voix:</span>
                  <span className="text-gray-300">{persona.voice.engine}</span>
                </div>
              )}
            </div>

            <div className="mt-4 pt-4 border-t border-primary-light text-xs text-gray-500">
              Mis à jour {new Date(persona.updated_at).toLocaleDateString('fr-FR')}
            </div>
          </Link>
        ))}
      </div>

      {personas.length === 0 && (
        <div className="text-center py-12 text-gray-400">
          <p className="text-lg">Aucun persona créé</p>
          <Link
            href="/personas/new"
            className="inline-block mt-4 px-4 py-2 bg-secondary text-primary-dark rounded hover:bg-secondary-light"
          >
            Créer votre premier persona
          </Link>
        </div>
      )}
    </div>
  );
}
