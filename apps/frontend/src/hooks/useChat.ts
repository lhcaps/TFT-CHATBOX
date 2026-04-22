import { useState, useRef, useCallback, useEffect } from 'react';
import type { Message, Mode } from '../api/types';
import type { Citation } from '../api/types';
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

  const clearMessages = useCallback(() => {
    setMessages([]);
  }, []);

  const sendMessage = useCallback(
    ({ sessionId, message, mode }: { sessionId: string; message: string; mode: Mode }) => {
      // Reset stream state before starting a new stream
      streamEndedRef.current = false;
      streamingTokenRef.current = '';

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
          onCitation: (citation) => {
            setMessages((prev) => {
              const last = prev[prev.length - 1];
              if (last) {
                const existing: Citation[] = (last.citations ?? []) as Citation[];
                return [...prev.slice(0, -1), { ...last, citations: [...existing, citation as unknown as Citation] }];
              }
              return prev;
            });
          },
          onDone: (_usage) => {
            if (streamEndedRef.current) return; // guard against double-call
            streamEndedRef.current = true;
            setMessages((prev) => {
              const last = prev[prev.length - 1];
              if (last?.isStreaming) {
                return [
                  ...prev.slice(0, -1),
                  { ...last, content: streamingTokenRef.current, isStreaming: false, citations: (last.citations ?? []) as Citation[] },
                ];
              }
              return prev;
            });
            setIsStreaming(false);
          },
          onError: (err) => {
            if (streamEndedRef.current) return; // guard against double-call
            streamEndedRef.current = true;
            const isAbort = (err as Error).name === 'AbortError';
            if (isAbort) {
              // Abort is user-initiated — don't show as an error, just stop streaming
              setMessages((prev) => {
                const last = prev[prev.length - 1];
                if (last?.isStreaming) {
                  return [
                    ...prev.slice(0, -1),
                    { ...last, content: streamingTokenRef.current, isStreaming: false },
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

  // Cleanup on unmount
  useEffect(() => {
    return () => abortControllerRef.current?.abort();
  }, []);

  return { messages, isStreaming, error, clearMessages, sendMessage, abort, clearError };
}
