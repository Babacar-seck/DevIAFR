'use client';

import { useEffect, useState } from 'react';
import { getStats, getVideos, getDownloadUrl, Video, Stats } from '@/lib/api';
import StatsCard from '@/components/StatsCard';
import VideoTable from '@/components/VideoTable';

export default function DashboardPage() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [videos, setVideos] = useState<Video[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    try {
      setLoading(true);
      const [statsData, videosData] = await Promise.all([
        getStats(),
        getVideos(),
      ]);
      setStats(statsData);
      setVideos(videosData);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erreur inconnue');
    } finally {
      setLoading(false);
    }
  }

  function handleDownload(videoId: string) {
    window.open(getDownloadUrl(videoId, 'video'), '_blank');
  }

  async function handleDelete(videoId: string) {
    if (!confirm('Supprimer cette vidéo ?')) return;
    
    try {
      const { deleteVideo } = await import('@/lib/api');
      await deleteVideo(videoId);
      setVideos(videos.filter(v => v.id !== videoId));
    } catch (err) {
      alert('Erreur lors de la suppression');
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-secondary mx-auto"></div>
          <p className="mt-4 text-gray-400">Chargement...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <p className="text-red-500 text-lg">❌ {error}</p>
          <button
            onClick={loadData}
            className="mt-4 px-4 py-2 bg-secondary text-primary-dark rounded hover:bg-secondary-light"
          >
            Réessayer
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold mb-2">Dashboard</h1>
        <p className="text-gray-400">Vue d'ensemble de votre production vidéo</p>
      </div>

      {/* Stats */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <StatsCard
            title="Total vidéos"
            value={stats.total_videos}
            icon="🎬"
            color="secondary"
          />
          <StatsCard
            title="Cette semaine"
            value={stats.videos_this_week}
            icon="📅"
            color="accent"
          />
          <StatsCard
            title="Score moyen"
            value={`${stats.avg_quality_score}/100`}
            icon="⭐"
            color="green"
          />
          <StatsCard
            title="Top persona"
            value={stats.top_persona}
            icon="🏆"
            color="orange"
          />
        </div>
      )}

      {/* Vidéos récentes */}
      <div className="bg-primary-light/50 rounded-lg p-6">
        <h2 className="text-xl font-semibold mb-4">Vidéos récentes</h2>
        <VideoTable
          videos={videos}
          onDownload={handleDownload}
          onDelete={handleDelete}
        />
      </div>
    </div>
  );
}
