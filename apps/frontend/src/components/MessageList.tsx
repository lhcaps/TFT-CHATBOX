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

interface MessageListProps {
  messages: Message[];
  isStreaming: boolean;
}

export function MessageList({ messages, isStreaming }: MessageListProps) {
  return (
    <div className="flex-1 overflow-y-auto space-y-4 p-4">
      {messages.map((msg, i) => (
        <div
          key={i}
          className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
        >
          <div
            className={`max-w-[70%] rounded-2xl px-4 py-3 ${
              msg.role === 'user'
                ? 'bg-blue-600 text-white'
                : msg.role === 'assistant'
                ? 'bg-gray-800 text-gray-100'
                : 'bg-gray-700 text-gray-300'
            }`}
          >
            <div className="prose prose-invert prose-sm max-w-none">
              <p className="whitespace-pre-wrap">{msg.content}</p>
            </div>
            {msg.citations && msg.citations.length > 0 && (
              <div className="mt-2 pt-2 border-t border-gray-700 text-xs text-gray-400">
                {msg.citations.length} source{msg.citations.length !== 1 ? 's' : ''}
              </div>
            )}
          </div>
        </div>
      ))}
      {isStreaming && (
        <div className="flex justify-start">
          <div className="bg-gray-800 rounded-2xl px-4 py-3">
            <div className="flex gap-1">
              <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
              <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
              <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
