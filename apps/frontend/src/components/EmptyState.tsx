export function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center h-full text-gray-400 gap-4 py-16">
      {/* Cosmic background glow */}
      <div className="relative">
        {/* Outer glow rings */}
        <div className="absolute inset-0 -m-8 rounded-full bg-purple-500/5 blur-xl" />
        <div className="absolute inset-0 -m-4 rounded-full bg-purple-500/10 blur-md" />

        {/* Constellation SVG icon */}
        <svg
          className="w-16 h-16 text-purple-400 relative z-10"
          viewBox="0 0 64 64"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
        >
          {/* Stars */}
          <circle cx="12" cy="12" r="2" fill="currentColor" className="animate-pulse" style={{ animationDelay: '0ms' }} />
          <circle cx="32" cy="8" r="1.5" fill="currentColor" className="animate-pulse" style={{ animationDelay: '200ms' }} />
          <circle cx="52" cy="16" r="2" fill="currentColor" className="animate-pulse" style={{ animationDelay: '400ms' }} />
          <circle cx="20" cy="32" r="1" fill="currentColor" className="animate-pulse" style={{ animationDelay: '100ms' }} />
          <circle cx="44" cy="28" r="1.5" fill="currentColor" className="animate-pulse" style={{ animationDelay: '300ms' }} />
          <circle cx="8" cy="48" r="1.5" fill="currentColor" className="animate-pulse" style={{ animationDelay: '500ms' }} />
          <circle cx="28" cy="44" r="2" fill="currentColor" className="animate-pulse" style={{ animationDelay: '150ms' }} />
          <circle cx="48" cy="52" r="1" fill="currentColor" className="animate-pulse" style={{ animationDelay: '350ms' }} />
          <circle cx="56" cy="36" r="1.5" fill="currentColor" className="animate-pulse" style={{ animationDelay: '250ms' }} />

          {/* Constellation lines */}
          <line x1="12" y1="12" x2="32" y2="8" stroke="currentColor" strokeWidth="0.5" strokeOpacity="0.4" />
          <line x1="32" y1="8" x2="52" y2="16" stroke="currentColor" strokeWidth="0.5" strokeOpacity="0.4" />
          <line x1="12" y1="12" x2="20" y2="32" stroke="currentColor" strokeWidth="0.5" strokeOpacity="0.3" />
          <line x1="52" y1="16" x2="44" y2="28" stroke="currentColor" strokeWidth="0.5" strokeOpacity="0.3" />
          <line x1="20" y1="32" x2="44" y2="28" stroke="currentColor" strokeWidth="0.5" strokeOpacity="0.3" />
          <line x1="20" y1="32" x2="28" y2="44" stroke="currentColor" strokeWidth="0.5" strokeOpacity="0.3" />
          <line x1="44" y1="28" x2="56" y2="36" stroke="currentColor" strokeWidth="0.5" strokeOpacity="0.2" />
          <line x1="28" y1="44" x2="48" y2="52" stroke="currentColor" strokeWidth="0.5" strokeOpacity="0.3" />
          <line x1="8" y1="48" x2="28" y2="44" stroke="currentColor" strokeWidth="0.5" strokeOpacity="0.3" />

          {/* Central "god" star — larger, brighter */}
          <circle cx="32" cy="32" r="3" fill="currentColor" className="animate-pulse" style={{ animationDelay: '600ms' }} />
          <circle cx="32" cy="32" r="6" stroke="currentColor" strokeWidth="0.5" strokeOpacity="0.2" className="animate-ping" style={{ animationDuration: '3s' }} />
        </svg>
      </div>

      {/* Text */}
      <div className="text-center space-y-2 max-w-sm">
        <p className="text-sm text-gray-300 leading-relaxed">
          Ask about TFT strategies, comps, augments, or patch notes.
        </p>
        <p className="text-xs text-gray-500">
          Switch modes above to search notes or get coaching.
        </p>
      </div>

      {/* Subtle mode hints */}
      <div className="flex items-center gap-4 mt-2">
        {[
          { label: 'Normal', desc: 'Free chat' },
          { label: 'RAG', desc: 'Search notes' },
          { label: 'Coach', desc: 'Get advice' },
        ].map((m) => (
          <div key={m.label} className="flex items-center gap-1.5 text-xs text-gray-600">
            <span className="text-purple-500/60">{m.label}</span>
            <span>—</span>
            <span>{m.desc}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
