interface CitationCardProps {
  id: string;
  source: string;
  text: string;
  similarity: number;
  onClick?: () => void;
}

export function CitationCard({ source, text, similarity, onClick }: CitationCardProps) {
  const percent = Math.round(similarity * 100);

  return (
    <div
      onClick={onClick}
      className="bg-gray-800 border border-gray-700 rounded-lg p-3 cursor-pointer
                 hover:border-gray-600 transition-colors"
    >
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs font-mono text-gray-400 truncate">{source}</span>
        <span className="text-xs text-gray-500">{percent}% match</span>
      </div>
      <p className="text-sm text-gray-300 line-clamp-3">{text}</p>
    </div>
  );
}
