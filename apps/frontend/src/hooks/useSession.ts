import { useState, useCallback } from 'react';
import type { Session, Mode, MessageOut } from '../api/types';
import { listSessions, createSession, deleteSession, getSessionMessages, getSession } from '../api/sessions';

export interface UseSessionReturn {
  sessions: Session[];
  currentSession: Session | null;
  messages: MessageOut[];
  loading: boolean;
  messagesLoading: boolean;
  error: string | null;
  loadSessions: () => Promise<void>;
  switchSession: (id: string) => Promise<void>;
  newSession: (mode?: Mode) => Promise<Session>;
  removeSession: (id: string) => Promise<void>;
  setCurrentMode: (mode: Mode) => void;
}

export function useSession(): UseSessionReturn {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [currentSession, setCurrentSession] = useState<Session | null>(null);
  const [messages, setMessages] = useState<MessageOut[]>([]);
  const [loading, setLoading] = useState(false);
  const [messagesLoading, setMessagesLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadSessions = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const all = await listSessions();
      setSessions(all);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }, []);

  const switchSession = useCallback(async (id: string) => {
    // Always fetch fresh session data to avoid stale closure issues
    setMessagesLoading(true);
    try {
      const session = await getSession(id);
      setCurrentSession(session);
      const msgs = await getSessionMessages(id);
      setMessages(msgs);
    } catch {
      setCurrentSession((prev) => (prev?.id === id ? prev : null));
      setMessages([]);
    } finally {
      setMessagesLoading(false);
    }
  }, []);

  const newSession = useCallback(async (mode: Mode = 'rag'): Promise<Session> => {
    const s = await createSession(undefined, mode);
    setSessions((prev) => [s, ...prev]);
    setCurrentSession(s);
    setMessages([]);
    return s;
  }, []);

  const removeSession = useCallback(async (id: string) => {
    await deleteSession(id);
    setSessions((prev) => {
      const remaining = prev.filter((s) => s.id !== id);
      if (currentSession?.id === id) {
        setCurrentSession(remaining[0] ?? null);
        setMessages(remaining[0] ? [] : []); // will be reloaded by switchSession
      }
      return remaining;
    });
  }, [currentSession]);

  const setCurrentMode = useCallback((mode: Mode) => {
    if (currentSession) {
      const updated = { ...currentSession, mode };
      setCurrentSession(updated);
      setSessions((prev) =>
        prev.map((s) => (s.id === currentSession.id ? updated : s)),
      );
    }
  }, [currentSession]);

  return {
    sessions,
    currentSession,
    messages,
    loading,
    messagesLoading,
    error,
    loadSessions,
    switchSession,
    newSession,
    removeSession,
    setCurrentMode,
  };
}
