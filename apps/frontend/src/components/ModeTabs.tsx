type Mode = 'normal' | 'rag' | 'coach';

interface ModeTabsProps {
  value: Mode;
  onChange: (mode: Mode) => void;
}

const MODES: { id: Mode; label: string; description: string }[] = [
  { id: 'normal', label: 'Normal', description: 'Free chat with the AI' },
  { id: 'rag', label: 'Notes', description: 'Search your Obsidian notes' },
  { id: 'coach', label: 'Coach', description: 'Strategic advice grounded in your notes' },
];

export function ModeTabs({ value, onChange }: ModeTabsProps) {
  return (
    <div className="flex gap-1 bg-gray-800 rounded-xl p-1">
      {MODES.map(mode => (
        <button
          key={mode.id}
          onClick={() => onChange(mode.id)}
          className={`flex-1 px-4 py-2 rounded-lg text-sm font-medium transition-colors
                     ${value === mode.id
                       ? 'bg-blue-600 text-white'
                       : 'text-gray-400 hover:text-white hover:bg-gray-700'
                     }`}
          title={mode.description}
        >
          {mode.label}
        </button>
      ))}
    </div>
  );
}
