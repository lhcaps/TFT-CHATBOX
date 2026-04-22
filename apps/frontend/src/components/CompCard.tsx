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
  'Rapid Firecannon', 'Statikk Shiv', 'Titan\'s Resolve', 'Warmog\'s Thresher',
  'Axiom Arc', 'Axiom Arc II', 'Axiom Arc III',
]);

const AP_ITEMS = new Set([
  'Qujin', 'Qujin II', 'Qujin III', "Rabadon's Deathcap", "Rabadon's Deathcap II",
  'Morellonomicon', 'Morellonomicon II', 'Luden\'s Tempest', 'Luden\'s Tempest II',
  'Statikk Shiv', 'Jeweled Gauntlet', 'Jeweled Gauntlet II',
  'Arcane Comet', 'Dawnbringer Spire',
]);

const TANK_ITEMS = new Set([
  "Warmog's Armor", 'Bramble Vest', 'Bramble Vest II', "Gargoyle Stoneplate",
  "Gargoyle Stoneplate II", 'Dragon\'s Claw', 'Adaptive Helm', 'Steadfast Heart',
  "Thornmail", 'Thornmail II', 'Randuin\'s Omen',
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

const TIER_COLORS = {
  S: { bg: 'rgba(251, 191, 36, 0.15)', border: '#fbbf24', text: '#fef3c7', label: 'S' },
  A: { bg: 'rgba(156, 163, 175, 0.15)', border: '#9ca3af', text: '#e5e7eb', label: 'A' },
  B: { bg: 'rgba(180, 83, 9, 0.15)', border: '#b45309', text: '#fde68a', label: 'B' },
};

const TIER_COLORS_SIDE: Record<string, string> = {
  S: '#fbbf24',
  A: '#9ca3af',
  B: '#d97706',
};

const ITEM_LABEL_COLORS: Record<string, string> = {
  AD: '#fca5a5',
  AP: '#93c5fd',
  Tank: '#86efac',
  Sup: '#d8b4fe',
  '': '#9ca3af',
};

// ─── CompCard Component ────────────────────────────────────────────────────

export function CompCard({
  compName,
  tier,
  top4Rate,
  avgPlace,
  carry,
  items,
  units,
  traits,
}: CompCardProps): JSX.Element {
  const tierStyle = TIER_COLORS[tier] || TIER_COLORS.B;

  return (
    <div
      style={{
        border: `1px solid ${tierStyle.border}`,
        borderRadius: '10px',
        background: tierStyle.bg,
        overflow: 'hidden',
        marginBottom: '12px',
        fontSize: '0.8rem',
        maxWidth: '480px',
      }}
    >
      {/* Header */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '8px 12px',
          borderBottom: `1px solid ${tierStyle.border}`,
          background: 'rgba(0,0,0,0.15)',
        }}
      >
        <span
          style={{
            fontWeight: 600,
            fontSize: '0.85rem',
            color: '#f1f5f9',
            flex: 1,
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap' as const,
            marginRight: '8px',
          }}
        >
          {compName}
        </span>
        <span
          style={{
            fontWeight: 800,
            fontSize: '0.9rem',
            color: tierStyle.text,
            background: 'rgba(0,0,0,0.3)',
            padding: '1px 7px',
            borderRadius: '4px',
            border: `1px solid ${tierStyle.border}`,
            flexShrink: 0,
          }}
        >
          {tierStyle.label}
        </span>
      </div>

      {/* Stats Row */}
      <div
        style={{
          display: 'flex',
          gap: '12px',
          padding: '6px 12px',
          borderBottom: `1px solid ${tierStyle.border}`,
          background: 'rgba(0,0,0,0.08)',
          fontSize: '0.72rem',
          color: '#94a3b8',
        }}
      >
        <span>
          <span style={{ color: '#64748b' }}>Top4: </span>
          <span style={{ color: '#e2e8f0', fontWeight: 600 }}>{top4Rate}%</span>
        </span>
        <span>
          <span style={{ color: '#64748b' }}>Avg: </span>
          <span style={{ color: '#e2e8f0', fontWeight: 600 }}>{avgPlace}</span>
        </span>
      </div>

      {/* Carry */}
      <div
        style={{
          padding: '6px 12px',
          borderBottom: '1px solid rgba(100,116,139,0.2)',
          display: 'flex',
          alignItems: 'center',
          gap: '6px',
        }}
      >
        <span style={{ color: '#64748b', fontSize: '0.72rem' }}>Carry:</span>
        <span style={{ color: '#fbbf24', fontWeight: 700, fontSize: '0.78rem' }}>
          {carry}
        </span>
      </div>

      {/* Items */}
      <div
        style={{
          padding: '6px 12px',
          borderBottom: '1px solid rgba(100,116,139,0.2)',
          display: 'flex',
          flexWrap: 'wrap' as const,
          gap: '4px',
        }}
      >
        {items.map((item, i) => {
          const clean = item.replace(/\[|\]/g, '').trim();
          const color = getItemColor(item);
          const label = color.label;
          return (
            <span
              key={i}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '3px',
                padding: '2px 6px',
                borderRadius: '4px',
                border: `1px solid ${color.border}`,
                background: color.bg,
                fontSize: '0.7rem',
                fontFamily: 'monospace',
              }}
            >
              {clean}
              {label && (
                <span
                  style={{
                    fontSize: '0.6rem',
                    color: ITEM_LABEL_COLORS[label],
                    fontWeight: 700,
                    marginLeft: '2px',
                  }}
                >
                  {label}
                </span>
              )}
            </span>
          );
        })}
      </div>

      {/* Units */}
      <div
        style={{
          padding: '6px 12px',
          borderBottom: '1px solid rgba(100,116,139,0.2)',
          display: 'flex',
          flexWrap: 'wrap' as const,
          gap: '4px',
        }}
      >
        {units.map((unit, i) => (
          <span
            key={i}
            style={{
              color: '#e2e8f0',
              fontSize: '0.72rem',
              fontWeight: 500,
              padding: '1px 5px',
              background: 'rgba(255,255,255,0.06)',
              borderRadius: '3px',
            }}
          >
            {unit}
          </span>
        ))}
      </div>

      {/* Traits */}
      {traits.length > 0 && (
        <div
          style={{
            padding: '5px 12px',
            display: 'flex',
            flexWrap: 'wrap' as const,
            gap: '4px',
          }}
        >
          {traits.map((t, i) => (
            <span
              key={i}
              style={{
                color: TIER_COLORS_SIDE[tier] || '#9ca3af',
                fontSize: '0.68rem',
                fontWeight: 600,
                padding: '1px 5px',
                borderRadius: '3px',
                background: 'rgba(0,0,0,0.2)',
                border: `1px solid ${tierStyle.border}33`,
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
