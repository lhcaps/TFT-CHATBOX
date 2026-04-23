import type { ChatOptions, Suggestion } from './types';

const BASE = '/api';
const CHAT_TIMEOUT_MS = 60_000;

async function sendChatRequest(opts: ChatOptions): Promise<Response> {
  const { sessionId, message, mode, stream = true, signal } = opts;

  // Merge user-provided signal with a 60s timeout
  const timeoutController = new AbortController();
  const timeoutId = setTimeout(() => timeoutController.abort(), CHAT_TIMEOUT_MS);
  const userSignal = signal;

  let finalSignal: AbortSignal = timeoutController.signal;
  if (userSignal) {
    // Race the two signals: if either aborts, the request aborts
    finalSignal = anySignal([timeoutController.signal, userSignal]);
  }

  const res = await fetch(`${BASE}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId, message, mode, stream }),
    signal: finalSignal,
  });

  clearTimeout(timeoutId);

  if (!res.ok) {
    const detail = await res.text().catch(() => res.statusText);
    throw new Error(`Chat failed ${res.status}: ${detail}`);
  }

  return res;
}

/** Combine multiple AbortSignals into one that aborts when any of them abort. */
function anySignal(signals: AbortSignal[]): AbortSignal {
  const controller = new AbortController();
  for (const s of signals) {
    if (s.aborted) { controller.abort(s.reason); return controller.signal; }
    s.addEventListener('abort', () => controller.abort(s.reason));
  }
  return controller.signal;
}

export async function streamChat(
  opts: ChatOptions,
  handlers: {
    onToken: (token: string) => void;
    onCitation: (citation: Record<string, unknown>) => void;
    onDone: (usage: Record<string, number>) => void;
    onError: (err: Error) => void;
  },
): Promise<void> {
  const response = await sendChatRequest(opts);
  if (!response.body) {
    handlers.onError(new Error('Response has no body'));
    return;
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) {
        if (buffer.trim()) {
          // Process any leftover in the buffer
          processChunk(buffer, handlers);
        }
        break;
      }

      buffer += decoder.decode(value, { stream: true });
      const { events, remainder } = extractEvents(buffer);
      buffer = remainder;

      for (const ev of events) {
        switch (ev.type) {
          case 'token':
            handlers.onToken(ev.token);
            break;
          case 'citation':
            handlers.onCitation(ev.citation);
            break;
          case 'done':
            handlers.onDone(ev.usage);
            break;
          case 'error':
            handlers.onError(new Error(ev.message));
            break;
        }
      }
    }
  } catch (err) {
    if ((err as Error).name !== 'AbortError') {
      handlers.onError(err as Error);
    }
  }
}

export async function chatNonStreaming(opts: ChatOptions) {
  const response = await sendChatRequest({ ...opts, stream: false });
  return response.json() as Promise<{
    text: string;
    usage: Record<string, number>;
    done_reason: string;
    citations: unknown[];
  }>;
}

export type { Mode } from './types';
export type { ChatOptions };

// ─── Internal helpers ────────────────────────────────────────────────────────

type Event =
  | { type: 'token'; token: string }
  | { type: 'citation'; citation: Record<string, unknown> }
  | { type: 'done'; usage: Record<string, number> }
  | { type: 'error'; message: string };

/** Split a buffer into complete SSE events and a remainder. */
function extractEvents(buffer: string): { events: Event[]; remainder: string } {
  const events: Event[] = [];
  // SSE events are separated by blank lines (\n\n)
  const parts = buffer.split('\n\n');

  for (let i = 0; i < parts.length - 1; i++) {
    const ev = parseSSEPart(parts[i]);
    if (ev) events.push(ev);
  }

  return { events, remainder: parts[parts.length - 1] ?? '' };
}

function parseSSEPart(raw: string): Event | null {
  // Extract the data: payload(s) from an SSE block
  const dataLines: string[] = [];
  for (const line of raw.split('\n')) {
    const trimmed = line.trim();
    if (trimmed.startsWith('data: ')) {
      dataLines.push(trimmed.slice(6));
    }
  }
  if (dataLines.length === 0) return null;

  // Join multi-line JSON
  const jsonStr = dataLines.join('');
  let data: Record<string, unknown>;
  try {
    data = JSON.parse(jsonStr);
  } catch {
    return null;
  }

  if ('token' in data) return { type: 'token', token: String(data.token ?? '') };
  if ('citation' in data) return { type: 'citation', citation: (data.citation as Record<string, unknown>) ?? {} };
  if ('done' in data && data.done === true) {
    return { type: 'done', usage: (data.usage as Record<string, number>) ?? {} };
  }
  if ('error' in data) return { type: 'error', message: String(data.error ?? 'Unknown error') };
  return null;
}

function processChunk(chunk: string, handlers: {
  onToken: (token: string) => void;
  onCitation: (citation: Record<string, unknown>) => void;
  onDone: (usage: Record<string, number>) => void;
  onError: (err: Error) => void;
}) {
  const ev = parseSSEPart(chunk);
  if (!ev) return;
  switch (ev.type) {
    case 'token': handlers.onToken(ev.token); break;
    case 'citation': handlers.onCitation(ev.citation); break;
    case 'done': handlers.onDone(ev.usage); break;
    case 'error': handlers.onError(new Error(ev.message)); break;
  }
}

const SUGGESTIONS_BASE = '/api';

/** Fetch suggestions from the knowledge graph based on user message */
export async function getSuggestions(message: string, limit = 3): Promise<Suggestion[]> {
  try {
    const params = new URLSearchParams({
      context: message.slice(0, 200),
      limit: String(limit),
    });
    const res = await fetch(`${SUGGESTIONS_BASE}/graph/suggest?${params}`);
    if (!res.ok) {
      return getStaticSuggestions();
    }
    const data = await res.json();
    if (!Array.isArray(data.suggestions) || data.suggestions.length === 0) {
      return getStaticSuggestions();
    }
    return data.suggestions as Suggestion[];
  } catch {
    return getStaticSuggestions();
  }
}

/** Static fallback suggestions when API is unavailable */
function getStaticSuggestions(): Suggestion[] {
  return [
    { text: 'Best items for Briar?', type: 'champion' },
    { text: 'Anima trait breakdown', type: 'trait' },
    { text: 'Top S-tier comps', type: 'general' },
  ];
}
