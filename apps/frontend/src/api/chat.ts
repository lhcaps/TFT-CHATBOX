export async function sendChatMessage(params: {
  message: string;
  session_id?: string;
  mode: 'normal' | 'rag' | 'coach';
  top_k?: number;
  stream?: boolean;
}) {
  const { message, session_id, mode, top_k = 6, stream = true } = params;

  const response = await fetch('/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, session_id, mode, top_k, stream }),
  });

  if (!response.ok) {
    throw new Error(`Chat request failed: ${response.statusText}`);
  }

  return response;
}

export function streamChatResponse(
  reader: ReadableStreamDefaultReader<Uint8Array>,
  onChunk: (text: string) => void,
  onDone: () => void,
  onError: (err: Error) => void
) {
  const decoder = new TextDecoder();
  let buffer = '';

  function pump() {
    reader.read().then(({ done, value }) => {
      if (done) {
        if (buffer) onChunk(buffer);
        onDone();
        return;
      }

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          onChunk(line.slice(6));
        }
      }

      pump();
    }).catch(onError);
  }

  pump();
}
