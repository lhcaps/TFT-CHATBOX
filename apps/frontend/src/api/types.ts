export type Role = 'system' | 'user' | 'assistant' | 'tool';
export type Mode = 'normal' | 'rag' | 'coach';

export interface Citation {
  id: string;
  source: string;
  text: string;
  similarity: number;
}

export interface Message {
  role: Role;
  content: string;
  citations?: Citation[];
  isStreaming?: boolean;
}

/** Message from GET /sessions/{id}/messages */
export interface MessageOut {
  role: Role;
  content: string;
  citations?: Citation[];
}

export interface Session {
  id: string;
  title: string | null;
  mode: Mode;
  created_at: string;
}

export interface ChatOptions {
  sessionId?: string;
  message: string;
  mode: Mode;
  stream?: boolean;
  signal?: AbortSignal;
}

export interface SSEEvent {
  type: 'token' | 'done' | 'usage' | 'citation' | 'error';
  data: Record<string, unknown>;
}
