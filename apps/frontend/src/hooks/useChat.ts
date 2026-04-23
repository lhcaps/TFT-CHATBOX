import { useState, useRef, useCallback, useEffect } from 'react';
import type { Message, Mode, Citation } from '../api/types';
import { streamChat } from '../api/chat';

export interface UseChatReturn {
  messages: Message[];
  isStreaming: boolean;
  error: string | null;
  clearMessages: () => void;
  sendMessage: (opts: { sessionId: string; message: string; mode: Mode }) => void;
  abort: () => void;
  clearError: () => void;
}

export function useChat(): UseChatReturn {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);
  const streamingTokenRef = useRef<string>('');
  const streamEndedRef = useRef(false);
  const citationsRef = useRef<Citation[]>([]);

  const clearMessages = useCallback(() => {
    setMessages([]);
  }, []);

  const sendMessage = useCallback(
    ({ sessionId, message, mode }: { sessionId: string; message: string; mode: Mode }) => {
      streamEndedRef.current = false;
      streamingTokenRef.current = '';
      citationsRef.current = [];

      const userMsg: Message = { role: 'user', content: message };
      const assistantPlaceholder: Message = {
        role: 'assistant',
        content: '',
        isStreaming: true,
      };

      setMessages((prev) => [...prev, userMsg, assistantPlaceholder]);
      setError(null);
      setIsStreaming(true);

      abortControllerRef.current = new AbortController();

      streamChat(
        {
          sessionId,
          message,
          mode,
          stream: true,
          signal: abortControllerRef.current.signal,
        },
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
            streamingTokenRef.current += token;
            setMessages((prev) => {
              const last = prev[prev.length - 1];
              if (last?.isStreaming) {
                return [...prev.slice(0, -1), { ...last, content: streamingTokenRef.current }];
              }
              return prev;
            });
          },
          onDone: (_usage) => {
            if (streamEndedRef.current) return;
            streamEndedRef.current = true;
            setMessages((prev) => {
              const last = prev[prev.length - 1];
              if (last?.isStreaming) {
                return [
                  ...prev.slice(0, -1),
                  { ...last, content: streamingTokenRef.current, isStreaming: false, citations: [...citationsRef.current] as Citation[] },
                ];
              }
              return prev;
            });
            setIsStreaming(false);
          },
          onError: (err) => {
            if (streamEndedRef.current) return;
            streamEndedRef.current = true;
            const isAbort = (err as Error).name === 'AbortError';
            if (isAbort) {
              setMessages((prev) => {
                const last = prev[prev.length - 1];
                if (last?.isStreaming) {
                  return [
                    ...prev.slice(0, -1),
                    { ...last, content: streamingTokenRef.current, isStreaming: false, citations: [...citationsRef.current] as Citation[] },
                  ];
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
    abortControllerRef.current?.abort();
  }, []);

  const clearError = useCallback(() => setError(null), []);

  useEffect(() => {
    return () => abortControllerRef.current?.abort();
  }, []);

  return { messages, isStreaming, error, clearMessages, sendMessage, abort, clearError };
}
