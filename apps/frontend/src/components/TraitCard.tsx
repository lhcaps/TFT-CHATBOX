interface TraitCardProps {
  name: string;
  count: number;
  bonus: string;
}

export function TraitCard({ name, count, bonus }: TraitCardProps) {
  const breakpointColor = count >= 6 ? 'text-purple-400' : count >= 3 ? 'text-blue-400' : 'text-gray-400';

  return (
    <div className="rounded-lg border border-purple-500/30 bg-gray-800/50 px-3 py-2 max-w-[320px] hover:-translate-y-0.5 transition-all">
      <div className="flex items-center gap-2 mb-1">
        <span className="font-bold text-sm text-gray-100">{name}</span>
        <span className={`text-xs font-bold ${breakpointColor}`}>{count}</span>
      </div>

      {bonus && (
        <div className="text-xs text-gray-300 leading-relaxed">
          {bonus}
        </div>
      )}
    </div>
  );
}
