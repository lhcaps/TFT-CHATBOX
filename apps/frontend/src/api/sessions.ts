import type { Session, Mode } from './types';
import type { MessageOut } from './types';

const BASE = '/api';

export async function listSessions(): Promise<Session[]> {
  const res = await fetch(`${BASE}/sessions`);
  if (!res.ok) throw new Error(`listSessions failed: ${res.statusText}`);
  return res.json();
}

export async function createSession(title?: string, mode: Mode = 'normal'): Promise<Session> {
  const res = await fetch(`${BASE}/sessions`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title, mode }),
  });
  if (!res.ok) throw new Error(`createSession failed: ${res.statusText}`);
  return res.json();
}

export async function getSession(id: string): Promise<Session> {
  const res = await fetch(`${BASE}/sessions/${id}`);
  if (!res.ok) throw new Error(`getSession failed: ${res.statusText}`);
  return res.json();
}

export async function getSessionMessages(sessionId: string): Promise<MessageOut[]> {
  const res = await fetch(`${BASE}/sessions/${sessionId}/messages`);
  if (!res.ok) throw new Error(`getSessionMessages failed: ${res.statusText}`);
  return res.json();
}

export async function deleteSession(id: string): Promise<void> {
  const res = await fetch(`${BASE}/sessions/${id}`, { method: 'DELETE' });
  if (!res.ok) throw new Error(`deleteSession failed: ${res.statusText}`);
}
