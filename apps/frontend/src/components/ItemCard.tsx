import type { ItemEntity } from '../api/types';

const CATEGORY_STYLES: Record<string, { label: string; badge: string; badgeText: string; border: string; bg: string }> = {
  AD: {
    label: 'AD',
    badge: 'bg-red-900/40 text-red-300 border border-red-700/40',
    badgeText: 'text-red-400',
    border: 'border-red-600/30',
    bg: 'bg-gray-800/50',
  },
  AP: {
    label: 'AP',
    badge: 'bg-blue-900/40 text-blue-300 border border-blue-700/40',
    badgeText: 'text-blue-400',
    border: 'border-blue-600/30',
    bg: 'bg-gray-800/50',
  },
  Tank: {
    label: 'Tank',
    badge: 'bg-green-900/40 text-green-300 border border-green-700/40',
    badgeText: 'text-green-400',
    border: 'border-green-600/30',
    bg: 'bg-gray-800/50',
  },
  Support: {
    label: 'Support',
    badge: 'bg-purple-900/40 text-purple-300 border border-purple-700/40',
    badgeText: 'text-purple-400',
    border: 'border-purple-600/30',
    bg: 'bg-gray-800/50',
  },
};

interface ItemCardProps {
  item: ItemEntity;
}

export function ItemCard({ item }: ItemCardProps) {
  const style = CATEGORY_STYLES[item.category] || CATEGORY_STYLES.Support;

  return (
    <div className={`rounded-lg border ${style.border} ${style.bg} px-3 py-2 max-w-[360px] hover:-translate-y-0.5 transition-all`}>
      <div className="flex items-center gap-2 mb-1">
        <span className="font-bold text-sm text-gray-100">{item.name}</span>
        <span className={`text-xs px-2 py-0.5 rounded font-bold ${style.badge}`}>
          {style.label}
        </span>
      </div>

      {item.recipe && item.recipe.length > 0 && (
        <div className="text-xs text-gray-400 mb-1">
          <span className="text-gray-500">Recipe:</span>{' '}
          {item.recipe.join(' + ')}
        </div>
      )}

      {item.stats.length > 0 && (
        <div className="flex flex-wrap gap-1 mb-1">
          {item.stats.map((stat, i) => (
            <span key={i} className="text-xs text-green-400 bg-green-900/20 px-1.5 py-0.5 rounded font-mono">
              {stat}
            </span>
          ))}
        </div>
      )}

      {item.effect && (
        <div className="text-xs text-gray-300 leading-relaxed">
          {item.effect}
        </div>
      )}
    </div>
  );
}
