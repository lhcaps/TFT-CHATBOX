interface CitationCardProps {
  id: string;
  source: string;
  heading: string;
  text: string;
  score: number;
  onClick?: () => void;
}

export function CitationCard({ source, heading, text, score, onClick }: CitationCardProps) {
  const percent = Math.round(score * 100);

  return (
    <div
      onClick={onClick}
      className="bg-gray-800 border border-gray-700 rounded-lg p-3 cursor-pointer
                 hover:border-gray-600 transition-colors"
    >
      <div className="flex items-center justify-between mb-1">
        <span className="text-xs font-mono text-gray-400 truncate" title={source}>
          {source}
        </span>
        <span className="text-xs text-gray-500">{percent}% match</span>
      </div>
      {heading && (
        <div className="text-xs text-gray-500 truncate mb-1" title={heading}>
          {heading}
        </div>
      )}
      <p className="text-sm text-gray-300 line-clamp-3">{text}</p>
    </div>
  );
}
