import { motion } from 'framer-motion';
import type { ChampionEntity } from '../api/types';

const COST_COLORS: Record<number, string> = {
  1: 'text-gray-400',
  2: 'text-green-400',
  3: 'text-blue-400',
  4: 'text-purple-400',
  5: 'text-yellow-400',
};

const COST_GLOW_COLORS: Record<number, string> = {
  4: { from: 'rgba(168,85,247,0.5)', to: 'rgba(168,85,247,0.8)' },
  5: { from: 'rgba(250,204,21,0.5)', to: 'rgba(250,204,21,0.8)' },
};

interface ChampionProfileProps {
  champion: ChampionEntity;
  animate?: boolean;
}

export function ChampionProfile({ champion, animate = true }: ChampionProfileProps) {
  const costColor = COST_COLORS[champion.cost] || 'text-gray-400';
  const glowConfig = COST_GLOW_COLORS[champion.cost];
  const hasGlow = !!glowConfig;

  const traitBadges = champion.traits.map((t, i) => (
    <span
      key={i}
      className="text-xs px-2 py-0.5 rounded bg-purple-900/50 text-purple-300 border border-purple-500/30 font-medium"
    >
      {t.name} {t.count}
    </span>
  ));

  const roleLabel = champion.role === 'carry' ? 'Carry' : champion.role === 'tank' ? 'Tank' : champion.role === 'support' ? 'Support' : 'Flex';

  const cardContent = (
    <div className="rounded-lg border border-purple-500/30 bg-gray-800/50 px-3 py-2 max-w-[380px] hover:-translate-y-0.5 transition-all">
      <div className="flex items-center gap-2 mb-1">
        <span className={`font-bold text-base ${costColor}`}>{champion.name}</span>
        <span className={`text-xs font-semibold ${costColor}`}>{champion.cost}-cost</span>
        <span className="text-xs text-gray-500 ml-auto">{roleLabel}</span>
      </div>

      {champion.traits.length > 0 && (
        <div className="flex flex-wrap gap-1 mb-1">
          {traitBadges}
        </div>
      )}

      {champion.ability && (
        <div className="text-xs text-gray-400">
          <span className="text-purple-400 font-medium">Ability:</span> {champion.ability}
        </div>
      )}
    </div>
  );

  if (hasGlow && animate) {
    return (
      <motion.div
        animate={{
          borderColor: [glowConfig.from, glowConfig.to, glowConfig.from],
          boxShadow: [
            `0 0 4px ${glowConfig.from}`,
            `0 0 8px ${glowConfig.to}`,
            `0 0 4px ${glowConfig.from}`,
          ],
        }}
        transition={{
          duration: 2.5,
          repeat: Infinity,
          ease: 'easeInOut',
        }}
      >
        {cardContent}
      </motion.div>
    );
  }

  return cardContent;
}
