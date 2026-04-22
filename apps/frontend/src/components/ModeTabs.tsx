import { Button } from '~/components/ui/button';

type Mode = 'normal' | 'rag' | 'coach';

interface ModeTabsProps {
  value: Mode;
  onChange: (mode: Mode) => void;
}

const MODES: { id: Mode; label: string; description: string }[] = [
  { id: 'normal', label: 'Normal', description: 'Free chat with the AI — no knowledge base' },
  { id: 'rag', label: 'RAG', description: 'Grounded answers using patch notes, comp data & set info' },
  { id: 'coach', label: 'Coach', description: 'Strategic advice with meta comps and play lines' },
];

export function ModeTabs({ value, onChange }: ModeTabsProps) {
  return (
    <div className="flex gap-1 bg-gray-800 rounded-xl p-1">
      {MODES.map(mode => (
        <Button
          key={mode.id}
          variant={value === mode.id ? 'default' : 'secondary'}
          size="sm"
          onClick={() => onChange(mode.id)}
          title={mode.description}
          className="flex-1"
        >
          {mode.label}
        </Button>
      ))}
    </div>
  );
}
