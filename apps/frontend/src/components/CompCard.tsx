import type { CompTrait } from './CompCard';

// ─── Types ────────────────────────────────────────────────────────────────────

export interface CompTrait {
  name: string;
  count: number;
}

export interface CompCardProps {
  compName: string;
  tier: 'S' | 'A' | 'B';
  top4Rate: string;
  avgPlace: string;
  carry: string;
  items: string[];
  units: string[];
  traits: CompTrait[];
}

// ─── Item Color Mapping ────────────────────────────────────────────────────────

const AD_ITEMS = new Set([
  'Giant Slayer', 'Bloodthirster', 'Infinity Edge', 'Rageblade',
  "Runaan's Hurricane", 'Deathblade', 'Hextech Gunblade', 'MortalReminder',
  'Rapid Firecannon', 'Statikk Shiv', "Titan's Resolve", "Warmog's Thresher",
  'Axiom Arc', 'Axiom Arc II', 'Axiom Arc III',
]);

const AP_ITEMS = new Set([
  'Qujin', 'Qujin II', 'Qujin III', "Rabadon's Deathcap", "Rabadon's Deathcap II",
  'Morellonomicon', 'Morellonomicon II', "Luden's Tempest", "Luden's Tempest II",
  'Statikk Shiv', 'Jeweled Gauntlet', 'Jeweled Gauntlet II',
  'Arcane Comet', 'Dawnbringer Spire',
]);

const TANK_ITEMS = new Set([
  "Warmog's Armor", 'Bramble Vest', 'Bramble Vest II', "Gargoyle Stoneplate",
  "Gargoyle Stoneplate II", "Dragon's Claw", 'Adaptive Helm', 'Steadfast Heart',
  'Thornmail', 'Thornmail II', "Randuin's Omen",
  'Electrocharge Spire',
]);

const SUPPORT_ITEMS = new Set([
  'Redemption', "Zeke's Herald", "Zeke's Herald II", 'Locket of the Iron Solari',
  'Locket II', 'Shroud of Stillness', 'Shroud II', 'Crowstorm Cape',
  'En Garde', 'En Garde II', 'Bloodthirster II',
]);

function getItemColor(item: string): { border: string; bg: string; label: string } {
  const name = item.replace(/\[|\]/g, '').trim();
  if (AD_ITEMS.has(name)) {
    return { border: 'rgba(239, 68, 68, 0.5)', bg: 'rgba(239, 68, 68, 0.1)', label: 'AD' };
  }
  if (AP_ITEMS.has(name)) {
    return { border: 'rgba(59, 130, 246, 0.5)', bg: 'rgba(59, 130, 246, 0.1)', label: 'AP' };
  }
  if (TANK_ITEMS.has(name)) {
    return { border: 'rgba(34, 197, 94, 0.5)', bg: 'rgba(34, 197, 94, 0.1)', label: 'Tank' };
  }
  if (SUPPORT_ITEMS.has(name)) {
    return { border: 'rgba(168, 85, 247, 0.5)', bg: 'rgba(168, 85, 247, 0.1)', label: 'Sup' };
  }
  return { border: 'rgba(156, 163, 175, 0.3)', bg: 'rgba(156, 163, 175, 0.08)', label: '' };
}

const TIER_STYLES = {
  S: { bg: 'bg-yellow-950/40', border: 'border-yellow-500/60', text: 'text-yellow-300', badge: 'text-yellow-400' },
  A: { bg: 'bg-gray-800/60', border: 'border-gray-500/60', text: 'text-gray-300', badge: 'text-gray-300' },
  B: { bg: 'bg-orange-950/30', border: 'border-orange-600/60', text: 'text-orange-300', badge: 'text-orange-400' },
};

const ITEM_LABEL_COLORS: Record<string, string> = {
  AD: '#fca5a5',
  AP: '#93c5fd',
  Tank: '#86efac',
  Sup: '#d8b4fe',
  '': '#9ca3af',
};

// ─── CompCard Component ───────────────────────────────────────────────────────

export function CompCard({
  compName,
  tier,
  top4Rate,
  avgPlace,
  carry,
  items,
  units,
  traits,
}: CompCardProps) {
  const tierStyle = TIER_STYLES[tier] || TIER_STYLES.B;

  const glowShadow =
    tier === 'S'
      ? '0 0 8px rgba(251,191,36,0.5)'
      : tier === 'A'
      ? '0 0 6px rgba(156,163,175,0.3)'
      : '0 0 6px rgba(180,83,9,0.3)';

  return (
    <div
      className={`rounded-xl border overflow-hidden mb-3 max-w-[480px] ${tierStyle.bg} ${tierStyle.border}`}
    >
      {/* Header */}
      <div className="flex items-center justify-between px-3 py-2 border-b border-gray-700/40">
        <span className="font-semibold text-sm flex-1 truncate mr-2 text-gray-100 overflow-hidden text-ellipsis whitespace-nowrap">
          {compName}
        </span>
        <span
          className="font-black text-sm px-2 py-0.5 rounded border text-shadow-lg"
          style={{
            color: tier === 'S' ? '#fbbf24' : tier === 'A' ? '#9ca3af' : '#b45309',
            borderColor: tier === 'S' ? '#fbbf24' : tier === 'A' ? '#9ca3af' : '#b45309',
            backgroundColor: 'rgba(0,0,0,0.4)',
            boxShadow: glowShadow,
          }}
        >
          {tier}
        </span>
      </div>

      {/* Stats Row */}
      <div className="flex gap-3 px-3 py-1.5 border-b border-gray-700/40 bg-black/10 text-xs">
        <span>
          <span className="text-gray-500">Top4: </span>
          <span className="text-gray-200 font-semibold">{top4Rate}%</span>
        </span>
        <span>
          <span className="text-gray-500">Avg: </span>
          <span className="text-gray-200 font-semibold">{avgPlace}</span>
        </span>
      </div>

      {/* Carry Row */}
      <div className="flex items-center gap-1.5 px-3 py-1.5 border-b border-gray-700/30">
        <span className="text-xs text-gray-500">Carry:</span>
        <span className="text-sm font-bold text-yellow-400">{carry}</span>
      </div>

      {/* Items Row */}
      <div className="flex flex-wrap gap-1 p-1.5 border-b border-gray-700/30">
        {items.map((item, i) => {
          const clean = item.replace(/\[|\]/g, '').trim();
          const color = getItemColor(item);
          const label = color.label;
          return (
            <span
              key={i}
              className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-xs font-mono"
              style={{
                borderColor: color.border,
                backgroundColor: color.bg,
              }}
            >
              {clean}
              {label && (
                <span
                  className="text-[10px] font-bold ml-0.5"
                  style={{ color: ITEM_LABEL_COLORS[label] }}
                >
                  {label}
                </span>
              )}
            </span>
          );
        })}
      </div>

      {/* Units Row */}
      <div className="flex flex-wrap gap-1 p-1.5 border-b border-gray-700/30">
        {units.map((unit, i) => (
          <span
            key={i}
            className="text-xs text-gray-300 font-medium px-1 py-0.5 bg-white/5 rounded"
          >
            {unit}
          </span>
        ))}
      </div>

      {/* Traits Row */}
      {traits.length > 0 && (
        <div className="flex flex-wrap gap-1 p-1.5">
          {traits.map((t, i) => (
            <span
              key={i}
              className="text-[11px] font-semibold px-1 py-0.5 rounded bg-black/20 border"
              style={{
                borderColor: tier === 'S' ? 'rgba(251,191,36,0.2)' : tier === 'A' ? 'rgba(156,163,175,0.2)' : 'rgba(180,83,9,0.2)',
                color: tier === 'S' ? '#fbbf24' : tier === 'A' ? '#9ca3af' : '#f97316',
              }}
            >
              {t.name} {t.count}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
