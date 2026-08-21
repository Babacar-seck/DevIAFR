'use client';

import { useEffect, useState } from 'react';
import { getVideos, deleteVideo, getDownloadUrl, Video } from '@/lib/api';
import VideoTable from '@/components/VideoTable';

export default function VideosPage() {
  const [videos, setVideos] = useState<Video[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadVideos();
  }, []);

  async function loadVideos() {
    try {
      setLoading(true);
      const data = await getVideos();
      setVideos(data);
    } catch (err) {
      console.error('Erreur:', err);
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
      await deleteVideo(videoId);
      setVideos(videos.filter(v => v.id !== videoId));
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

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold mb-2">Vidéos</h1>
        <p className="text-gray-400">Historique de toutes vos vidéos produites</p>
      </div>

      <div className="bg-primary-light/50 rounded-lg p-6">
        <VideoTable
          videos={videos}
          onDownload={handleDownload}
          onDelete={handleDelete}
        />
      </div>
    </div>
  );
}
