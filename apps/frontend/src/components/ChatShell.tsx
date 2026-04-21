interface Message {
  role: 'user' | 'assistant' | 'system' | 'tool';
  content: string;
  citations?: Citation[];
}

interface Citation {
  id: string;
  source: string;
  text: string;
  similarity: number;
}

interface ChatShellProps {
  messages: Message[];
  isStreaming: boolean;
  onAbort: () => void;
}

export function ChatShell({ messages, isStreaming, onAbort }: ChatShellProps) {
  return (
    <div className="flex flex-col h-full bg-gray-900 text-white">
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-2xl rounded-lg p-4 ${
              msg.role === 'user' ? 'bg-blue-600' : 'bg-gray-800'
            }`}>
              <p className="whitespace-pre-wrap">{msg.content}</p>
              {msg.citations && msg.citations.length > 0 && (
                <div className="mt-2 text-sm text-gray-400">
                  Citations: {msg.citations.length}
                </div>
              )}
            </div>
          </div>
        ))}
        {isStreaming && (
          <div className="flex justify-start">
            <div className="bg-gray-800 rounded-lg p-4 max-w-2xl">
              <span className="animate-pulse">Thinking...</span>
            </div>
          </div>
        )}
      </div>
      {isStreaming && (
        <button
          onClick={onAbort}
          className="m-4 px-4 py-2 bg-red-600 hover:bg-red-700 rounded-lg"
        >
          Stop
        </button>
      )}
    </div>
  );
}
