import { useEffect, useRef, useState } from 'react';
import type { Message, EntityCard, StreamingCitation } from '../api/types';
import { CitationCard } from './CitationCard';
import { CitationModal } from './CitationModal';
import { EmptyState } from './EmptyState';
import { CompCard } from './CompCard';
import { ChampionProfile } from './ChampionProfile';
import { ItemCard } from './ItemCard';
import { TraitCard } from './TraitCard';
import { AugmentCard } from './AugmentCard';
import { CoachLineOfPlay } from './CoachLineOfPlay';
import { parseEntityBlocks, parseCompCard, parseCoachBlocks, hasCoachContent } from '../utils/compParser';

interface MessageListProps {
  messages: Message[];
  isStreaming: boolean;
  streamingCitations?: Record<string, StreamingCitation>;
  onCitationStart?: (citation: { id: string; source: string; heading: string }) => void;
  onCitationProgress?: (citation: { id: string; text_preview: string }) => void;
  onCitationEnd?: (citation: { id: string; text: string; score: number; source: string; heading: string }) => void;
}

export function MessageList({ messages, isStreaming, streamingCitations = {} }: MessageListProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isStreaming]);

  const [selectedCitation, setSelectedCitation] = useState<{
    id: string; source: string; heading: string; text: string; score: number;
  } | null>(null);
  const [sourceFilter, setSourceFilter] = useState<string>('all');

  return (
    <div className="flex-1 overflow-y-auto overflow-x-hidden space-y-4 p-6">
      {messages.length === 0 && !isStreaming && <EmptyState />}

      {messages.map((msg, i) => (
        <div
          key={i}
          className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'} min-w-0`}
        >
          <div
            className={`max-w-[70%] md:max-w-[90%] lg:max-w-[70%] rounded-2xl px-4 py-3 ${
              msg.role === 'user'
                ? 'bg-blue-600 text-white rounded-br-md'
                : msg.role === 'assistant'
                ? 'bg-gray-800 text-gray-100 rounded-bl-md'
                : 'bg-gray-700 text-gray-300'
            }`}
          >
            <div className="prose prose-invert prose-sm max-w-none">
              <MessageContent content={msg.content} messageRole={msg.role} />
            </div>
            {msg.citations && msg.citations.length > 0 && (
              <div className="mt-2 pt-2 border-t border-gray-700 overflow-x-auto">
                <div className="text-xs text-gray-400 mb-2 font-medium">
                  {msg.citations.length} source{msg.citations.length !== 1 ? 's' : ''}
                </div>

                {/* Source filter */}
                <div className="flex gap-2 mb-2">
                  {(['all', 'obsidian', 'patch', 'metatft'] as const).map((s) => (
                    <button
                      key={s}
                      onClick={() => setSourceFilter(s)}
                      className={`text-xs px-2 py-1 rounded ${
                        sourceFilter === s
                          ? 'bg-purple-600 text-white'
                          : 'bg-gray-700 text-gray-400 hover:bg-gray-600'
                      }`}
                    >
                      {s === 'all' ? 'All' : s.charAt(0).toUpperCase() + s.slice(1)}
                    </button>
                  ))}
                </div>

                <div className="grid gap-2">
                  {msg.citations
                    .filter((c) => {
                      if (sourceFilter === 'all') return true;
                      const s = c.source.toLowerCase();
                      if (sourceFilter === 'obsidian') return s.includes('obsidian') || (!s.includes('patch') && !s.includes('metatft'));
                      if (sourceFilter === 'patch') return s.includes('patch');
                      if (sourceFilter === 'metatft') return s.includes('metatft');
                      return true;
                    })
                    .map((c) => (
                      <CitationCard
                        key={c.id}
                        citation={c}
                        onClick={() => setSelectedCitation(c)}
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
          <div className="bg-gray-800/80 border border-purple-500/20 rounded-2xl rounded-bl-md px-4 py-3">
            <div className="flex gap-1">
              <span className="w-2 h-2 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
              <span className="w-2 h-2 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
              <span className="w-2 h-2 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
            </div>
          </div>
        </div>
      )}

      {/* Streaming citations (RAG2-03 progressive reveal) */}
      {isStreaming && Object.keys(streamingCitations).length > 0 && (
        <div className="flex justify-start pl-4">
          <div className="max-w-[70%] rounded-2xl rounded-bl-md px-4 py-3 bg-gray-800/40 border border-gray-700/50">
            <div className="text-xs text-gray-400 mb-2 font-medium">
              {Object.keys(streamingCitations).length} source{Object.keys(streamingCitations).length !== 1 ? 's' : ''} (loading...)
            </div>
            <div className="grid gap-2">
              {Object.values(streamingCitations).map((cit) => (
                <StreamingCitationCard key={cit.id} citation={cit} onClick={() => setSelectedCitation({
                  id: cit.id,
                  source: cit.source,
                  heading: cit.heading,
                  text: cit.text,
                  score: cit.score,
                })} />
              ))}
            </div>
          </div>
        </div>
      )}

      <div ref={bottomRef} />

      <CitationModal
        citation={selectedCitation}
        onClose={() => setSelectedCitation(null)}
      />
    </div>
  );
}

// ─── MessageContent ────────────────────────────────────────────────────────────

function EntityCardRenderer({ entity }: { entity: EntityCard }) {
  switch (entity.type) {
    case 'champion':
      return <ChampionProfile champion={entity} />;
    case 'item':
      return <ItemCard item={entity} />;
    case 'trait':
      return <TraitCard name={entity.name} count={entity.count} bonus={entity.bonus} />;
    case 'augment':
      return (
        <AugmentCard
          name={entity.name}
          tier={entity.tier}
          effect={entity.effect}
          relatedChampions={entity.relatedChampions}
        />
      );
    default:
      return (
        <code className="block rounded border border-gray-600/40 bg-gray-800/50 px-2 py-1 my-1 text-xs font-mono text-gray-400">
          {JSON.stringify(entity)}
        </code>
      );
  }
}

function MessageContent({ content, messageRole }: { content: string; messageRole?: string }) {
  // Check for coach line-of-play content in assistant messages
  if (messageRole === 'assistant' && hasCoachContent(content)) {
    const coach = parseCoachBlocks(content);
    if (coach.lines.length > 0 || coach.pivots.length > 0) {
      return (
        <>
          <CoachLineOfPlay lines={coach.lines} pivots={coach.pivots} />
          {coach.text && (
            <p className="whitespace-pre-wrap wrap-break-word leading-relaxed">
              {coach.text}
            </p>
          )}
        </>
      );
    }
  }

  const blocks = parseEntityBlocks(content);

  return (
    <>
      {blocks.map((block, i) => {
        if (block.kind === 'comp') {
          const parsed = parseCompCard(block.raw);
          if (parsed) {
            return <CompCard key={i} {...parsed} />;
          }
        }
        if (block.kind === 'entity' && block.entity) {
          return <EntityCardRenderer key={i} entity={block.entity} />;
        }
        return (
          <p key={i} className="whitespace-pre-wrap wrap-break-word leading-relaxed">
            {block.raw.trim()}
          </p>
        );
      })}
    </>
  );
}

// ─── Streaming Citation Card (RAG2-03) ────────────────────────────────────────────

function StreamingCitationCard({ citation, onClick }: { citation: StreamingCitation; onClick?: () => void }) {
  const isLoading = citation.status === 'loading';
  const isProgress = citation.status === 'progress';

  return (
    <div
      onClick={onClick}
      className="border border-gray-700 rounded-xl p-3 bg-gray-800/50 transition-colors hover:border-gray-600"
    >
      <div className="flex items-center justify-between gap-2 mb-1">
        <span className="text-xs font-mono text-gray-400 truncate flex-1" title={citation.source}>
          {citation.source}
        </span>
        {citation.status === 'complete' && (
          <span className="text-xs text-gray-500 shrink-0">
            {Math.round(citation.score * 100)}%
          </span>
        )}
        {isLoading && (
          <span className="text-xs text-purple-400 animate-pulse shrink-0">
            Loading...
          </span>
        )}
        {isProgress && (
          <span className="text-xs text-yellow-400 shrink-0">
            ...
          </span>
        )}
      </div>
      {citation.heading && (
        <div className="text-xs text-gray-500 truncate mb-1" title={citation.heading}>
          {citation.heading}
        </div>
      )}
      {isLoading && (
        <div className="space-y-1">
          <div className="h-3 bg-gray-700 rounded animate-pulse w-full" />
          <div className="h-3 bg-gray-700 rounded animate-pulse w-3/4" />
        </div>
      )}
      {isProgress && (
        <p className="text-sm text-gray-400 italic">
          {citation.textPreview || '...'}
        </p>
      )}
      {citation.status === 'complete' && (
        <p className="text-sm text-gray-300">
          {citation.text.length > 200
            ? citation.text.slice(0, 200) + '...'
            : citation.text}
        </p>
      )}
    </div>
  );
}

// ─── Block Parser ───────────────────────────────────────────────────────────────
// parseCompBlocks and parseCompCard are now in ../utils/compParser.ts
