import { Video } from '@/lib/api';

interface VideoTableProps {
  videos: Video[];
  onDownload: (id: string) => void;
  onDelete: (id: string) => void;
}

export default function VideoTable({ videos, onDownload, onDelete }: VideoTableProps) {
  if (videos.length === 0) {
    return (
      <div className="text-center py-12 text-gray-400">
        <p className="text-lg">Aucune vidéo produite</p>
        <p className="text-sm mt-2">Lancez une production depuis l'onglet "Production"</p>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full">
        <thead>
          <tr className="border-b border-primary-light">
            <th className="text-left py-3 px-4 text-gray-400 font-medium">Sujet</th>
            <th className="text-left py-3 px-4 text-gray-400 font-medium">Persona</th>
            <th className="text-left py-3 px-4 text-gray-400 font-medium">Score</th>
            <th className="text-left py-3 px-4 text-gray-400 font-medium">Statut</th>
            <th className="text-left py-3 px-4 text-gray-400 font-medium">Date</th>
            <th className="text-right py-3 px-4 text-gray-400 font-medium">Actions</th>
          </tr>
        </thead>
        <tbody>
          {videos.map((video) => (
            <tr key={video.id} className="border-b border-primary-light hover:bg-primary-light/50">
              <td className="py-3 px-4">
                <div className="font-medium">{video.subject}</div>
              </td>
              <td className="py-3 px-4">
                <span className="px-2 py-1 rounded bg-accent/20 text-accent text-sm">
                  {video.persona_id}
                </span>
              </td>
              <td className="py-3 px-4">
                {video.quality_score ? (
                  <span className={`font-semibold ${
                    video.quality_score >= 80 ? 'text-green-500' :
                    video.quality_score >= 60 ? 'text-orange-500' : 'text-red-500'
                  }`}>
                    {video.quality_score}/100
                  </span>
                ) : (
                  <span className="text-gray-500">—</span>
                )}
              </td>
              <td className="py-3 px-4">
                <span className={`px-2 py-1 rounded text-sm ${
                  video.status === 'ready' ? 'bg-green-500/20 text-green-500' :
                  video.status === 'generating' ? 'bg-blue-500/20 text-blue-500' :
                  video.status === 'failed' ? 'bg-red-500/20 text-red-500' :
                  'bg-gray-500/20 text-gray-500'
                }`}>
                  {video.status}
                </span>
              </td>
              <td className="py-3 px-4 text-sm text-gray-400">
                {new Date(video.created_at).toLocaleDateString('fr-FR')}
              </td>
              <td className="py-3 px-4 text-right">
                <div className="flex gap-2 justify-end">
                  {video.status === 'ready' && video.has_video && (
                    <button
                      onClick={() => onDownload(video.id)}
                      className="px-3 py-1 rounded bg-secondary text-primary-dark hover:bg-secondary-light transition-colors text-sm"
                    >
                      ⬇️ Télécharger
                    </button>
                  )}
                  <button
                    onClick={() => onDelete(video.id)}
                    className="px-3 py-1 rounded bg-red-500/20 text-red-500 hover:bg-red-500/30 transition-colors text-sm"
                  >
                    🗑️
                  </button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
