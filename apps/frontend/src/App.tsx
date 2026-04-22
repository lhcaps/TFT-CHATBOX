import { useEffect, useCallback, useRef } from 'react';
import type { Mode } from './api/types';
import { useSession } from './hooks/useSession';
import { useStreamingMessages } from './hooks/useStreamingMessages';
import { useToast } from './hooks/useToast';
import { ChatShell } from './components/ChatShell';
import { GpuStatusBadge } from './components/GpuBadge';
import { PatchStatus } from './components/PatchStatus';
import { ToastContainer } from './components/ui/toast';

export default function App() {
  const {
    sessions,
    currentSession,
    messages: sessionMessages,
    loading,
    messagesLoading,
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

  const { toasts, removeToast, success: toastSuccess } = useToast();

  // Track which session was streamed so we re-fetch the right one after stream ends.
  // This handles the case where the user switches sessions while a stream is running.
  const streamedSessionIdRef = useRef<string | null>(null);

  // After stream completes, re-fetch the session that was streamed so persisted data is reflected.
  // useRef to avoid re-subscribing when switchSession identity changes.
  useEffect(() => {
    if (!isStreaming && streamedSessionIdRef.current) {
      const id = streamedSessionIdRef.current;
      streamedSessionIdRef.current = null;
      switchSession(id);
    }
  }, [isStreaming]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    loadSessions();
  }, [loadSessions]);

  const handleNewSession = useCallback(async () => {
    await newSession();
    toastSuccess('Conversation started');
  }, [newSession, toastSuccess]);

  const handleSelectSession = useCallback(
    async (id: string) => { await switchSession(id); },
    [switchSession],
  );

  const handleDeleteSession = useCallback(async (id: string) => {
    await removeSession(id);
    toastSuccess('Conversation deleted');
  }, [removeSession, toastSuccess]);

  const handleModeChange = useCallback((mode: Mode) => { setCurrentMode(mode); }, [setCurrentMode]);

  const handleSend = useCallback(
    (message: string) => {
      if (!currentSession) return;
      streamedSessionIdRef.current = currentSession.id;
      sendMessage({ sessionId: currentSession.id, message, mode: currentSession.mode });
    },
    [currentSession, sendMessage],
  );

  return (
    <div className="flex flex-col h-screen">
      <header className="flex items-center justify-end px-4 py-1 border-b border-gray-700 bg-gray-800 gap-4 shrink-0">
        <GpuStatusBadge />
        <PatchStatus />
      </header>
      <ChatShell
        messages={messages}
        isStreaming={isStreaming}
        messagesLoading={messagesLoading}
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
      <ToastContainer toasts={toasts} onRemove={removeToast} />
    </div>
  );
}
