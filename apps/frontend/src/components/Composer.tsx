import { useState, useRef, useCallback, useEffect } from 'react';

interface ComposerProps {
  onSend: (message: string) => void;
  disabled: boolean;
  placeholder?: string;
}

export function Composer({ onSend, disabled, placeholder = 'Ask about TFT strategies...' }: ComposerProps) {
  const [input, setInput] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-grow textarea
  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = 'auto';
    el.style.height = `${Math.min(el.scrollHeight, 120)}px`;
  }, [input]);

  const submit = useCallback(() => {
    const trimmed = input.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setInput('');
    // Reset height
    if (textareaRef.current) textareaRef.current.style.height = 'auto';
    textareaRef.current?.focus();
  }, [input, disabled, onSend]);

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      submit();
    }
  }, [submit]);

  return (
    <div className="border-t border-gray-700 bg-gray-800 px-6 py-4">
      <div className="flex gap-3 max-w-4xl mx-auto items-end">
        <textarea
          ref={textareaRef}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          disabled={disabled}
          rows={1}
          className="flex-1 resize-none rounded-xl bg-gray-700 text-white placeholder-gray-500
                     px-4 py-3 focus:outline-none focus:ring-2 focus:ring-blue-500
                     disabled:opacity-50 disabled:cursor-not-allowed text-sm leading-relaxed"
          style={{ minHeight: '48px', maxHeight: '120px' }}
        />
        <button
          onClick={submit}
          disabled={disabled || !input.trim()}
          className="px-5 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600
                     disabled:cursor-not-allowed rounded-xl font-medium text-sm text-white
                     transition-colors flex-shrink-0 flex items-center gap-2"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
          </svg>
          Send
        </button>
      </div>
    </div>
  );
}
