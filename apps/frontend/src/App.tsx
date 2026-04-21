import { useEffect, useCallback } from 'react';
import type { Mode } from './api/types';
import { useSession } from './hooks/useSession';
import { useStreamingMessages } from './hooks/useStreamingMessages';
import { ChatShell } from './components/ChatShell';

export default function App() {
  const {
    sessions,
    currentSession,
    messages: sessionMessages,
    loading,
    error: sessionsError,
    loadSessions,
    switchSession,
    newSession,
    removeSession,
    setCurrentMode,
  } = useSession();

  const {
    messages,
    isStreaming,
    error: chatError,
    sendMessage,
    abort,
    clearError,
  } = useStreamingMessages(sessionMessages);

  useEffect(() => {
    loadSessions();
  }, [loadSessions]);

  const handleNewSession = useCallback(async () => {
    await newSession();
  }, [newSession]);

  const handleSelectSession = useCallback(
    async (id: string) => { await switchSession(id); },
    [switchSession],
  );

  const handleDeleteSession = useCallback(async (id: string) => { await removeSession(id); }, [removeSession]);

  const handleModeChange = useCallback((mode: Mode) => { setCurrentMode(mode); }, [setCurrentMode]);

  const handleSend = useCallback(
    (message: string) => {
      if (!currentSession) return;
      sendMessage({ sessionId: currentSession.id, message, mode: currentSession.mode });
    },
    [currentSession, sendMessage],
  );

  return (
    <ChatShell
      messages={messages}
      isStreaming={isStreaming}
      onSend={handleSend}
      onAbort={abort}
      sessions={sessions}
      currentSession={currentSession}
      onNewSession={handleNewSession}
      onSelectSession={handleSelectSession}
      onDeleteSession={handleDeleteSession}
      currentMode={currentSession?.mode ?? 'normal'}
      onModeChange={handleModeChange}
      error={chatError ?? sessionsError}
      onClearError={clearError}
      loading={loading}
    />
  );
}
