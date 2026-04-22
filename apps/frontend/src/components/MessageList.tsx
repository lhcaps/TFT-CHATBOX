import { useEffect, useRef } from 'react';
import type { Message } from '../api/types';
import { CitationCard } from './CitationCard';
import { CompCard } from './CompCard';
import { parseCompBlocks, parseCompCard } from '../utils/compParser';

interface MessageListProps {
  messages: Message[];
  isStreaming: boolean;
}

export function MessageList({ messages, isStreaming }: MessageListProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isStreaming]);

  return (
    <div className="flex-1 overflow-y-auto space-y-4 p-6">
      {messages.length === 0 && !isStreaming && (
        <div className="flex flex-col items-center justify-center h-full text-gray-500 gap-3 py-16">
          <svg className="w-12 h-12 opacity-40" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
              d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
          </svg>
          <p className="text-sm">Ask about TFT strategies, comps, augments, or patch notes.</p>
          <p className="text-xs text-gray-600">Switch modes above to search notes or get coaching.</p>
        </div>
      )}

      {messages.map((msg, i) => (
        <div
          key={i}
          className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
        >
          <div
            className={`max-w-[70%] rounded-2xl px-4 py-3 ${
              msg.role === 'user'
                ? 'bg-blue-600 text-white rounded-br-md'
                : msg.role === 'assistant'
                ? 'bg-gray-800 text-gray-100 rounded-bl-md'
                : 'bg-gray-700 text-gray-300'
            }`}
          >
            <div className="prose prose-invert prose-sm max-w-none">
              <MessageContent content={msg.content} />
            </div>
            {msg.citations && msg.citations.length > 0 && (
              <div className="mt-2 pt-2 border-t border-gray-700">
                <div className="text-xs text-gray-400 mb-2 font-medium">
                  {msg.citations.length} source{msg.citations.length !== 1 ? 's' : ''}
                </div>
                <div className="grid gap-2">
                  {msg.citations.map((c) => (
                    <CitationCard
                      key={c.id}
                      id={c.id}
                      source={c.source}
                      heading={c.heading}
                      text={c.text}
                      score={c.score}
                    />
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      ))}

      {isStreaming && (
        <div className="flex justify-start">
          <div className="bg-gray-800 rounded-2xl rounded-bl-md px-4 py-3">
            <div className="flex gap-1">
              <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
              <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
              <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
            </div>
          </div>
        </div>
      )}

      <div ref={bottomRef} />
    </div>
  );
}

// ─── MessageContent ────────────────────────────────────────────────────────────

function MessageContent({ content }: { content: string }) {
  const blocks = parseCompBlocks(content);

  return (
    <>
      {blocks.map((block, i) => {
        if (block.type === 'comp') {
          const parsed = parseCompCard(block.raw);
          if (parsed) {
            return <CompCard key={i} {...parsed} />;
          }
        }
        return (
          <p key={i} className="whitespace-pre-wrap leading-relaxed">
            {block.raw.trim()}
          </p>
        );
      })}
    </>
  );
}

// ─── Block Parser ───────────────────────────────────────────────────────────────
// parseCompBlocks and parseCompCard are now in ../utils/compParser.ts

