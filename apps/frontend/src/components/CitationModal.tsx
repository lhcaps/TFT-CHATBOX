interface CitationModalProps {
  citation: {
    id: string;
    source: string;
    heading: string;
    text: string;
    score: number;
  } | null;
  onClose: () => void;
}

export function CitationModal({ citation, onClose }: CitationModalProps) {
  if (!citation) return null;

  const percent = Math.round(citation.score * 100);

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className="bg-gray-800 border border-gray-600 rounded-2xl p-6 max-w-2xl w-full mx-4 max-h-[80vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-start justify-content-between gap-4 mb-4">
          <div className="flex-1 min-w-0">
            <span className="text-xs font-mono text-purple-400 block truncate" title={citation.source}>
              {citation.source}
            </span>
            {citation.heading && (
              <span className="text-xs text-gray-500 block truncate mt-1" title={citation.heading}>
                {citation.heading}
              </span>
            )}
          </div>
          <div className="flex items-center gap-3 flex-shrink-0">
            <span className="text-xs text-gray-500">{percent}% match</span>
            <button
              onClick={() => {
                navigator.clipboard.writeText(`${citation.source}\n${citation.heading}\n${citation.text}`);
              }}
              className="text-gray-400 hover:text-gray-200 transition-colors text-xs"
              title="Copy citation"
            >
              Copy
            </button>
            <button
              onClick={onClose}
              className="text-gray-500 hover:text-white transition-colors"
              aria-label="Close modal"
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        {/* Full citation text */}
        <div className="text-sm text-gray-300 whitespace-pre-wrap leading-relaxed">
          {citation.text}
        </div>
      </div>
    </div>
  );
}
