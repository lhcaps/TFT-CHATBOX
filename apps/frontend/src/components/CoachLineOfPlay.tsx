import type { LineOfPlay, PivotLine } from '../api/types';

interface CoachLineOfPlayProps {
  lines: LineOfPlay[];
  pivots?: PivotLine[];
}

export function CoachLineOfPlay({ lines, pivots = [] }: CoachLineOfPlayProps) {
  if (lines.length === 0) return null;

  return (
    <div className="space-y-3 my-2 max-w-[420px]">
      {/* Primary lines */}
      {lines.map((line, i) => (
        <div
          key={i}
          className="rounded-lg border border-purple-500/30 bg-gray-800/60 overflow-hidden"
        >
          {/* Header */}
          <div className="flex items-center gap-2 px-3 py-2 border-b border-purple-500/20 bg-purple-900/20">
            <span className="text-xs font-bold text-purple-400 uppercase tracking-wider">
              {i === 0 ? 'PRIMARY' : `OPTION ${i + 1}`}
            </span>
            <span className="font-semibold text-sm text-gray-100">{line.name}</span>
          </div>

          {/* Content */}
          <div className="px-3 py-2 space-y-1.5">
            {/* Econ */}
            {line.econ && (
              <div className="flex gap-2 text-xs">
                <span className="text-gray-500 flex-shrink-0">Econ:</span>
                <span className="text-gray-300">{line.econ}</span>
              </div>
            )}

            {/* Items */}
            {line.items && line.items.length > 0 && (
              <div className="flex gap-2 text-xs">
                <span className="text-gray-500 flex-shrink-0">Items:</span>
                <div className="flex flex-wrap gap-1">
                  {line.items.map((item, j) => (
                    <span
                      key={j}
                      className="text-xs px-1.5 py-0.5 rounded bg-red-900/20 text-red-300 border border-red-800/30"
                    >
                      {item}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Timing */}
            {line.timing && (
              <div className="flex gap-2 text-xs">
                <span className="text-gray-500 flex-shrink-0">Timing:</span>
                <span className="text-gray-300">{line.timing}</span>
              </div>
            )}

            {/* Risk */}
            {line.risk && (
              <div className="flex gap-2 text-xs">
                <span className="text-orange-400 flex-shrink-0">Risk:</span>
                <span className="text-orange-300">{line.risk}</span>
              </div>
            )}
          </div>
        </div>
      ))}

      {/* Pivot fallback */}
      {pivots.length > 0 && (
        <div className="rounded-lg border border-yellow-600/30 bg-yellow-900/10 overflow-hidden">
          <div className="flex items-center gap-2 px-3 py-2 border-b border-yellow-600/20 bg-yellow-900/20">
            <span className="text-xs font-bold text-yellow-400 uppercase tracking-wider">
              PIVOT FALLBACK
            </span>
          </div>
          <div className="px-3 py-2 space-y-2">
            {pivots.map((pivot, i) => (
              <div key={i} className="text-xs">
                <span className="font-semibold text-yellow-300">{pivot.name}: </span>
                <span className="text-gray-300">{pivot.timing}</span>
                {pivot.transferable && (
                  <div className="mt-0.5">
                    <span className="text-gray-500">Transfer: </span>
                    <span className="text-gray-400">{pivot.transferable}</span>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
