import type { Citation } from '~/api/types';

interface CitationCardProps {
  citation: Citation;
  onClick?: () => void;
}

export function CitationCard({ citation, onClick }: CitationCardProps) {
  const percent = Math.round(citation.score * 100);

  // Truncate text to ~200 chars
  const truncatedText = citation.text.length > 200
    ? citation.text.slice(0, 200).trimEnd() + '...'
    : citation.text;

  return (
    <div
      onClick={onClick}
      className="cursor-pointer hover:border-gray-600 transition-colors border border-gray-700 rounded-xl p-3 bg-gray-800/50"
    >
      <div className="flex items-center justify-between gap-2 mb-1">
        <span className="text-xs font-mono text-gray-400 truncate flex-1" title={citation.source}>
          {citation.source}
        </span>
        <span className="text-xs text-gray-500 flex-shrink-0">{percent}%</span>
      </div>
      {citation.heading && (
        <div className="text-xs text-gray-500 truncate mb-1" title={citation.heading}>
          {citation.heading}
        </div>
      )}
      <p className="text-sm text-gray-300">{truncatedText}</p>
      {citation.text.length > 200 && (
        <div className="text-xs text-purple-400 mt-1">Click to read more</div>
      )}
    </div>
  );
}
