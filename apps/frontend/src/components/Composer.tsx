import { useState, useRef, useCallback, useEffect } from 'react';
import { Button } from '~/components/ui/button';
import { Textarea } from '~/components/ui/textarea';
import { Send } from 'lucide-react';

interface ComposerProps {
  onSend: (message: string) => void;
  disabled: boolean;
  placeholder?: string;
  coachMode?: boolean;
  activePreset?: string | null;
  onPresetChange?: (preset: string | null) => void;
}

const SCENARIO_PRESETS = [
  { tag: '[fast8]', label: 'Fast 8' },
  { tag: '[hyperoll]', label: 'Hyperoll' },
  { tag: '[1star]', label: '1-Star' },
  { tag: '[lategame]', label: 'Late Game' },
];

export function Composer({ onSend, disabled, placeholder = 'Ask about TFT strategies...', coachMode, activePreset, onPresetChange }: ComposerProps) {
  const [input, setInput] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = 'auto';
    el.style.height = `${Math.min(el.scrollHeight, 120)}px`;
  }, [input]);

  const submit = useCallback(() => {
    const trimmed = input.trim();
    if (!trimmed || disabled) return;
    const message = activePreset ? `${activePreset} ${trimmed}` : trimmed;
    onSend(message);
    setInput('');
    if (textareaRef.current) textareaRef.current.style.height = 'auto';
    textareaRef.current?.focus();
  }, [input, disabled, onSend, activePreset]);

  const handleKeyDown = useCallback((e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      submit();
    }
  }, [submit]);

  return (
    <>
      {coachMode && (
        <div className="px-4 pt-3 pb-1">
          <div className="flex items-center gap-2 max-w-4xl mx-auto mb-1">
            <span className="text-xs text-gray-500">Scenario:</span>
            <div className="flex flex-wrap gap-1.5">
              {SCENARIO_PRESETS.map((preset) => {
                const isActive = activePreset === preset.tag;
                return (
                  <button
                    key={preset.tag}
                    onClick={() => onPresetChange?.(isActive ? null : preset.tag)}
                    title={`Add ${preset.tag} prefix`}
                    className={`text-xs px-2 py-1 rounded border transition-colors ${
                      isActive
                        ? 'bg-purple-600 text-white border-purple-500'
                        : 'bg-gray-700/50 text-gray-400 border-gray-600/40 hover:bg-gray-600/50 hover:text-gray-300'
                    }`}
                  >
                    {preset.label}
                  </button>
                );
              })}
            </div>
          </div>
        </div>
      )}
      <div className="border-t border-gray-700 bg-gray-800 px-4 md:px-6 py-4">
        <div className="flex gap-3 max-w-4xl mx-auto items-end">
          <Textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            disabled={disabled}
            rows={1}
            style={{ minHeight: '48px', maxHeight: '120px' }}
          />
          <Button
            onClick={submit}
            disabled={disabled || !input.trim()}
          >
            <Send className="w-4 h-4" />
            Send
          </Button>
        </div>
      </div>
    </>
  );
}
