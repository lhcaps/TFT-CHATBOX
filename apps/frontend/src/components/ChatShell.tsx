import { Button } from '~/components/ui/button';
import { MessageList } from './MessageList';
import { Composer } from './Composer';
import { ModeTabs } from './ModeTabs';
import { Plus, Trash2, Square } from 'lucide-react';
import type { Message, Mode } from '../api/types';

interface Session {
  id: string;
  title: string | null;
  mode: Mode;
}

interface ChatShellProps {
  messages: Message[];
  isStreaming: boolean;
  messagesLoading?: boolean;
  onSend: (message: string) => void;
  onAbort: () => void;
  sessions: Session[];
  currentSession: Session | null;
  onNewSession: () => void;
  onSelectSession: (id: string) => void;
  onDeleteSession: (id: string) => void;
  currentMode: Mode;
  onModeChange: (mode: Mode) => void;
  error: string | null;
  onClearError: () => void;
  loading: boolean;
}

export function ChatShell({
  messages,
  isStreaming,
  messagesLoading = false,
  onSend,
  onAbort,
  sessions,
  currentSession,
  onNewSession,
  onSelectSession,
  onDeleteSession,
  currentMode,
  onModeChange,
  error,
  onClearError,
  loading,
}: ChatShellProps) {
  return (
    <div className="flex h-screen bg-gray-900 text-white overflow-hidden">
      {/* Sidebar */}
      <aside className="w-64 flex-shrink-0 flex flex-col border-r border-gray-700 bg-gray-800">
        <div className="p-4 border-b border-gray-700">
          <Button onClick={onNewSession} className="w-full">
            <Plus className="w-4 h-4" />
            New Chat
          </Button>
        </div>

        <div className="flex-1 overflow-y-auto space-y-1 p-2">
          {loading && sessions.length === 0 ? (
            <p className="px-3 py-2 text-gray-500 text-sm">Loading...</p>
          ) : sessions.length === 0 ? (
            <p className="px-3 py-2 text-gray-500 text-sm">No sessions yet</p>
          ) : (
            sessions.map((s) => (
              <div
                key={s.id}
                className={`group flex items-center gap-2 rounded-xl px-3 py-2 cursor-pointer text-sm transition-colors
                           ${currentSession?.id === s.id ? 'bg-gray-700 text-white' : 'text-gray-400 hover:bg-gray-700 hover:text-white'}`}
                onClick={() => onSelectSession(s.id)}
              >
                <span className="flex-1 truncate">{s.title ?? 'New conversation'}</span>
                <span className="hidden group-hover:flex items-center gap-1 flex-shrink-0">
                  <span className="text-xs bg-gray-600 px-1.5 py-0.5 rounded">{s.mode}</span>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={(e: React.MouseEvent) => { e.stopPropagation(); onDeleteSession(s.id); }}
                    title="Delete session"
                    className="text-gray-500 hover:text-red-400 h-7 w-7"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </Button>
                </span>
              </div>
            ))
          )}
        </div>
      </aside>

      {/* Main chat area */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Header */}
        <header className="flex-shrink-0 flex items-center justify-between px-6 py-3 border-b border-gray-700 bg-gray-800 gap-4">
          <h1 className="text-sm font-semibold text-gray-300 truncate">
            {currentSession ? (currentSession.title ?? 'New conversation') : 'TFT Local Copilot'}
          </h1>
          <div className="w-64">
            <ModeTabs value={currentMode} onChange={onModeChange} />
          </div>
        </header>

        {/* Error banner */}
        {error && (
          <div className="flex-shrink-0 flex items-center gap-3 px-6 py-2 bg-red-900/40 border-b border-red-800 text-red-300 text-sm">
            <svg className="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span className="flex-1">{error}</span>
            <button onClick={onClearError} className="hover:text-white flex-shrink-0">
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        )}

        {/* Message list */}
        <div className="flex-1 relative">
          {messagesLoading && (
            <div className="absolute inset-0 flex items-center justify-center bg-gray-900/80 z-10">
              <div className="flex flex-col items-center gap-2">
                <div className="w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
                <span className="text-xs text-gray-400">Loading...</span>
              </div>
            </div>
          )}
          <MessageList messages={messages} isStreaming={isStreaming} />
        </div>

        {/* Composer */}
        <Composer
          onSend={onSend}
          disabled={isStreaming || !currentSession}
          placeholder={currentSession ? undefined : 'Start a new chat to begin...'}
        />

        {/* Stop button */}
        {isStreaming && (
          <div className="flex-shrink-0 flex justify-center pb-2">
            <Button variant="destructive" onClick={onAbort}>
              <Square className="w-4 h-4 fill-current" />
              Stop
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}
