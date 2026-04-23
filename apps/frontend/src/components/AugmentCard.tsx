const TIER_STYLES: Record<string, { label: string; badge: string; border: string }> = {
  Silver: {
    label: 'Silver',
    badge: 'bg-gray-700/60 text-gray-300 border border-gray-600/40',
    border: 'border-gray-500/30',
  },
  Gold: {
    label: 'Gold',
    badge: 'bg-yellow-900/40 text-yellow-400 border border-yellow-600/40',
    border: 'border-yellow-500/30',
  },
  Prismatic: {
    label: 'Prismatic',
    badge: 'bg-purple-900/40 text-purple-400 border border-purple-600/40',
    border: 'border-purple-500/30',
  },
};

interface AugmentCardProps {
  name: string;
  tier: 'Silver' | 'Gold' | 'Prismatic';
  effect: string;
  relatedChampions?: string[];
}

export function AugmentCard({ name, tier, effect, relatedChampions }: AugmentCardProps) {
  const style = TIER_STYLES[tier] || TIER_STYLES.Silver;

  return (
    <div className={`rounded-lg border ${style.border} bg-gray-800/50 px-3 py-2 max-w-[380px] hover:-translate-y-0.5 transition-all`}>
      <div className="flex items-center gap-2 mb-2">
        <span className="font-bold text-sm text-gray-100">{name}</span>
        <span className={`text-xs px-2 py-0.5 rounded font-bold ${style.badge}`}>
          {style.label}
        </span>
      </div>

      {effect && (
        <div className="text-xs text-gray-300 leading-relaxed mb-2">
          {effect}
        </div>
      )}

      {relatedChampions && relatedChampions.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {relatedChampions.map((champ, i) => (
            <span
              key={i}
              className="text-[11px] px-1.5 py-0.5 rounded bg-blue-900/30 text-blue-300 border border-blue-700/30"
            >
              {champ}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
