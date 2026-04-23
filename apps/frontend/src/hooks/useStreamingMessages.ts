import { useState, useRef, useCallback, useEffect } from 'react';
import type { Message, Mode, MessageOut, Citation } from '../api/types';
import { streamChat } from '../api/chat';

export interface UseStreamingMessagesReturn {
  messages: Message[];
  isStreaming: boolean;
  error: string | null;
  clearMessages: () => void;
  sendMessage: (opts: { sessionId: string; message: string; mode: Mode }) => void;
  abort: () => void;
  clearError: () => void;
}

/** Load persisted session messages (from API) into local state. */
function toMessages(apiMessages: MessageOut[]): Message[] {
  return apiMessages.map((m) => ({
    role: m.role,
    content: m.content,
    citations: m.citations,
    isStreaming: false,
  }));
}

export function useStreamingMessages(history: MessageOut[]): UseStreamingMessagesReturn {
  const [messages, setMessages] = useState<Message[]>(() => toMessages(history));
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const acRef = useRef<AbortController | null>(null);
  const tokenAccRef = useRef('');
  const endedRef = useRef(false);
  const citationsRef = useRef<Citation[]>([]);

  // Sync when history prop changes
  useEffect(() => {
    if (!isStreaming) {
      setMessages(toMessages(history));
    }
  }, [history, isStreaming]);

  const clearMessages = useCallback(() => {
    setMessages([]);
  }, []);

  const sendMessage = useCallback(
    ({ sessionId, message, mode }: { sessionId: string; message: string; mode: Mode }) => {
      endedRef.current = false;
      tokenAccRef.current = '';
      citationsRef.current = [];
      setError(null);
      setIsStreaming(true);

      const userMsg: Message = { role: 'user', content: message };
      const assistantPlaceholder: Message = { role: 'assistant', content: '', isStreaming: true };
      setMessages((prev) => [...prev, userMsg, assistantPlaceholder]);

      acRef.current = new AbortController();

      streamChat(
        { sessionId, message, mode, stream: true, signal: acRef.current.signal },
        {
          onCitationStart: (citation) => {
            const cit: Citation = {
              id: citation.id,
              source: citation.source,
              heading: citation.heading || '',
              text: '',
              score: 0,
            };
            citationsRef.current.push(cit);
          },
          onCitationProgress: (citation) => {
            const idx = citationsRef.current.findIndex(c => c.id === citation.id);
            if (idx >= 0) {
              citationsRef.current[idx] = {
                ...citationsRef.current[idx],
                text: citation.text_preview || '',
              };
            }
          },
          onCitationEnd: (citation) => {
            const idx = citationsRef.current.findIndex(c => c.id === citation.id);
            if (idx >= 0) {
              citationsRef.current[idx] = {
                ...citationsRef.current[idx],
                text: citation.text,
                score: citation.score,
              };
            }
          },
          onToken: (token) => {
            tokenAccRef.current += token;
            setMessages((prev) => {
              const last = prev[prev.length - 1];
              if (last?.isStreaming) {
                return [...prev.slice(0, -1), { ...last, content: tokenAccRef.current }];
              }
              return prev;
            });
          },
          onDone: (_usage) => {
            if (endedRef.current) return;
            endedRef.current = true;
            setMessages((prev) => {
              const last = prev[prev.length - 1];
              if (last?.isStreaming) {
                return [...prev.slice(0, -1), { ...last, content: tokenAccRef.current, isStreaming: false, citations: [...citationsRef.current] as Citation[] }];
              }
              return prev;
            });
            setIsStreaming(false);
          },
          onError: (err) => {
            if (endedRef.current) return;
            endedRef.current = true;
            const isAbort = err.name === 'AbortError';
            const isTimeout = isAbort && !tokenAccRef.current;
            if (isAbort) {
              setMessages((prev) => {
                const last = prev[prev.length - 1];
                if (last?.isStreaming) {
                  const msg = isTimeout
                    ? 'Request timed out after 60s — Ollama may be slow. Try again.'
                    : tokenAccRef.current;
                  return [...prev.slice(0, -1), { ...last, content: msg, isStreaming: false, citations: [...citationsRef.current] as Citation[] }];
                }
                return prev;
              });
            } else {
              setError(err.message);
              setMessages((prev) => {
                const last = prev[prev.length - 1];
                if (last?.isStreaming) {
                  return [
                    ...prev.slice(0, -1),
                    { ...last, content: `Error: ${err.message}`, isStreaming: false },
                  ];
                }
                return prev;
              });
            }
            setIsStreaming(false);
          },
        },
      );
    },
    [],
  );

  const abort = useCallback(() => {
    acRef.current?.abort();
  }, []);

  const clearError = useCallback(() => setError(null), []);

  useEffect(() => () => acRef.current?.abort(), []);

  return { messages, isStreaming, error, clearMessages, sendMessage, abort, clearError };
}
