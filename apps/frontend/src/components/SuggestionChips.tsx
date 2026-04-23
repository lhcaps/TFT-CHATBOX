import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { getSuggestions } from '../api/chat';
import type { Suggestion } from '../api/types';
import { X } from 'lucide-react';

interface SuggestionChipsProps {
  lastMessage: string;
  onSelect: (text: string) => void;
}

const TYPE_COLORS: Record<string, string> = {
  champion: 'border-blue-500/30 text-blue-300 bg-blue-900/20 hover:bg-blue-800/40',
  item: 'border-red-500/30 text-red-300 bg-red-900/20 hover:bg-red-800/40',
  trait: 'border-purple-500/30 text-purple-300 bg-purple-900/20 hover:bg-purple-800/40',
  augment: 'border-yellow-500/30 text-yellow-300 bg-yellow-900/20 hover:bg-yellow-800/40',
  general: 'border-gray-500/30 text-gray-300 bg-gray-800/40 hover:bg-gray-700/50',
};

export function SuggestionChips({ lastMessage, onSelect }: SuggestionChipsProps) {
  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
  const [dismissed, setDismissed] = useState(false);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    if (!lastMessage || dismissed) return;

    let cancelled = false;

    async function load() {
      const result = await getSuggestions(lastMessage, 3);
      if (!cancelled) {
        setSuggestions(result);
        setVisible(true);
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, [lastMessage, dismissed]);

  const handleDismiss = () => {
    setDismissed(true);
    setVisible(false);
  };

  if (!lastMessage || dismissed) return null;

  return (
    <AnimatePresence>
      {visible && (
        <motion.div
          initial={{ opacity: 0, y: -8 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -8 }}
          transition={{ duration: 0.2 }}
          className="sticky top-0 z-20 bg-gray-900/95 backdrop-blur-sm border-b border-gray-800 px-4 py-2"
        >
          <div className="flex items-center gap-2 max-w-4xl mx-auto">
            <span className="text-xs text-gray-500 shrink-0">Try:</span>
            <div className="flex flex-wrap gap-2 flex-1">
              {suggestions.map((s, i) => {
                const colorClass = TYPE_COLORS[s.type] || TYPE_COLORS.general;
                return (
                  <button
                    key={i}
                    onClick={() => {
                      onSelect(s.text);
                      handleDismiss();
                    }}
                    className={`text-sm px-3 py-1.5 rounded-full border transition-colors ${colorClass}`}
                  >
                    {s.text}
                    <span className="ml-1.5 opacity-60">→</span>
                  </button>
                );
              })}
            </div>
            <button
              onClick={handleDismiss}
              className="text-gray-500 hover:text-gray-300 transition-colors p-1 rounded"
              aria-label="Dismiss suggestions"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
