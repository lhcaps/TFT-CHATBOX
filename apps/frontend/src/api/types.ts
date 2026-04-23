export type Role = 'system' | 'user' | 'assistant' | 'tool';
export type Mode = 'normal' | 'rag' | 'coach';

export interface Citation {
  id: string;
  source: string;
  heading: string;
  text: string;
  score: number;
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
  entityFilter?: string;  // RAG2-01: 'champion' | 'item' | 'trait' | 'augment' | 'system'
}

export interface SSEEvent {
  type: 'token' | 'done' | 'usage' | 'citation' | 'error' | 'entity_card';
  data: Record<string, unknown>;
}

// ─── Entity Card Types ─────────────────────────────────────────────────────────

/** Entity types that can appear as inline cards */
export type EntityType = 'champion' | 'item' | 'trait' | 'augment';

/** Champion entity marker */
export interface ChampionEntity {
  type: 'champion';
  name: string;
  cost: number;
  traits: Array<{ name: string; count: number }>;
  ability: string;
  role: 'carry' | 'tank' | 'support' | 'flex';
}

/** Item entity marker */
export interface ItemEntity {
  type: 'item';
  name: string;
  category: 'AD' | 'AP' | 'Tank' | 'Support';
  stats: string[];
  effect: string;
  recipe?: string[];
}

/** Trait entity marker */
export interface TraitEntity {
  type: 'trait';
  name: string;
  count: number;
  bonus: string;
}

/** Augment entity marker */
export interface AugmentEntity {
  type: 'augment';
  name: string;
  tier: 'Silver' | 'Gold' | 'Prismatic';
  effect: string;
  relatedChampions?: string[];
}

/** Union of all entity card types */
export type EntityCard = ChampionEntity | ItemEntity | TraitEntity | AugmentEntity;

/** Content block for MessageContent rendering */
export interface ContentBlock {
  kind: 'text' | 'comp' | 'entity';
  raw: string;
  entity?: EntityCard;
}

// ─── Coach Types ───────────────────────────────────────────────────────────────

/** Coach line of play */
export interface LineOfPlay {
  name: string;
  econ?: string;
  items?: string[];
  timing?: string;
  risk?: string;
}

/** Coach pivot fallback */
export interface PivotLine {
  name: string;
  timing: string;
  transferable?: string;
}

/** Suggestion chip data */
export interface Suggestion {
  text: string;
  type: 'champion' | 'item' | 'trait' | 'augment' | 'general';
}
