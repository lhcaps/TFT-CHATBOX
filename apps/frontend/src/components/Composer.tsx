import { useState, useRef, useCallback } from 'react';

interface ComposerProps {
  onSend: (message: string) => void;
  disabled: boolean;
}

export function Composer({ onSend, disabled }: ComposerProps) {
  const [input, setInput] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSubmit = useCallback(() => {
    const trimmed = input.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setInput('');
    textareaRef.current?.focus();
  }, [input, disabled, onSend]);

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  }, [handleSubmit]);

  return (
    <div className="border-t border-gray-700 bg-gray-800 p-4">
      <div className="flex gap-3 max-w-4xl mx-auto">
        <textarea
          ref={textareaRef}
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask about TFT strategies, comps, or patches..."
          disabled={disabled}
          rows={1}
          className="flex-1 resize-none rounded-xl bg-gray-700 text-white placeholder-gray-400
                     px-4 py-3 focus:outline-none focus:ring-2 focus:ring-blue-500
                     disabled:opacity-50 disabled:cursor-not-allowed"
          style={{ maxHeight: '120px' }}
        />
        <button
          onClick={handleSubmit}
          disabled={disabled || !input.trim()}
          className="px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600
                     disabled:cursor-not-allowed rounded-xl font-medium text-white
                     transition-colors"
        >
          Send
        </button>
      </div>
    </div>
  );
}
