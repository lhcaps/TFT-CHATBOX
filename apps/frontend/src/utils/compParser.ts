// ─── Types ────────────────────────────────────────────────────────────────────

import type { EntityCard, ContentBlock } from '../api/types';

export interface CompTrait {
  name: string;
  count: number;
}

export interface ParsedComp {
  compName: string;
  tier: 'S' | 'A' | 'B';
  top4Rate: string;
  avgPlace: string;
  carry: string;
  items: string[];
  units: string[];
  traits: CompTrait[];
}

// ─── Parser ────────────────────────────────────────────────────────────────────

export function parseCompCard(markdown: string): ParsedComp | null {
  try {
    const lines = markdown.trim().split('\n');

    let compName = '';
    let tier = 'B' as 'S' | 'A' | 'B';
    let top4Rate = '0';
    let avgPlace = '5.0';
    let carry = '';
    const items: string[] = [];
    const units: string[] = [];
    const traits: CompTrait[] = [];

    for (const line of lines) {
      const trimmed = line.trim();

      if (trimmed.startsWith('# Comp:') || trimmed.startsWith('### Comp:')) {
        compName = trimmed.replace(/^#+\s*Comp:\s*/, '').trim();
        continue;
      }

      if (trimmed.startsWith('**Tier:**')) {
        const m = trimmed.match(/\*\*Tier:\*\*\s*([SABsab])\b/);
        if (m) {
          tier = m[1].toUpperCase() as 'S' | 'A' | 'B';
        }
        const top4m = trimmed.match(/Top4:\*\*\s*([0-9.]+)%/);
        if (top4m) top4Rate = top4m[1];
        const avgm = trimmed.match(/Avg Place:\*\*\s*([0-9.]+)/);
        if (avgm) avgPlace = avgm[1];
        continue;
      }

      if (trimmed.startsWith('**Carry:**')) {
        carry = trimmed.replace(/^\*\*Carry:\*\*\s*/, '').trim();
        continue;
      }

      if (trimmed.startsWith('**Items:**')) {
        const content = trimmed.replace(/^\*\*Items:\*\*\s*/, '');
        const itemMatches = content.matchAll(/\[([^\]]+)\]/g);
        for (const match of itemMatches) {
          items.push(match[1].trim());
        }
        continue;
      }

      if (trimmed.startsWith('**Units:**')) {
        const content = trimmed.replace(/^\*\*Units:\*\*\s*/, '');
        const unitList = content.split(',').map(u => u.trim()).filter(Boolean);
        units.push(...unitList);
        continue;
      }

      if (trimmed.startsWith('**Traits:**')) {
        const content = trimmed.replace(/^\*\*Traits:\*\*\s*/, '');
        const traitParts = content.split(',').map(t => t.trim()).filter(Boolean);
        for (const part of traitParts) {
          const mm = part.match(/^([^(]+)\s*\(([0-9]+)\)/);
          if (mm) {
            traits.push({ name: mm[1].trim(), count: parseInt(mm[2], 10) });
          } else {
            const bare = part.trim();
            if (bare) {
              const nm = bare.match(/^([A-Za-z ]+?)\s*([0-9]+)$/);
              if (nm) {
                traits.push({ name: nm[1].trim(), count: parseInt(nm[2], 10) });
              } else {
                traits.push({ name: bare, count: 1 });
              }
            }
          }
        }
        continue;
      }
    }

    if (!compName && !carry) return null;

    return { compName, tier, top4Rate, avgPlace, carry, items, units, traits };
  } catch {
    return null;
  }
}

// ─── Block Parser ───────────────────────────────────────────────────────────────

export interface CompBlock {
  type: 'comp' | 'text';
  raw: string;
}

export function parseCompBlocks(content: string): CompBlock[] {
  const blocks: CompBlock[] = [];
  const regex = /(?:^|\n)(#{1,3}\s+Comp:\s*.+?(?=\n#{1,3}\s+Comp:|\n*(?:-{3,}|\*{3,}|$)))/gm;
  let lastIndex = 0;
  let match;

  while ((match = regex.exec(content)) !== null) {
    if (match.index > lastIndex) {
      const textBefore = content.slice(lastIndex, match.index).trim();
      if (textBefore) blocks.push({ type: 'text', raw: textBefore });
    }
    blocks.push({ type: 'comp', raw: match[0].trim() });
    lastIndex = match.index + match[0].length;
  }

  if (lastIndex < content.length) {
    const remaining = content.slice(lastIndex).trim();
    if (remaining) blocks.push({ type: 'text', raw: remaining });
  }

  return blocks;
}

// ─── Entity Marker Parser ─────────────────────────────────────────────────────

/** Entity marker regex — matches complete or partial JSON starting with {"type": */
const ENTITY_MARKER_RE = /\{"type":\s*"(champion|item|trait|augment)"[^{}]*(?:\{[^{}]*\}[^{}]*)*\}/g;

/** Validates that a string is valid JSON and has a known entity type */
export function tryParseEntity(raw: string): EntityCard | null {
  try {
    const parsed = JSON.parse(raw) as EntityCard;
    if (['champion', 'item', 'trait', 'augment'].includes(parsed.type)) {
      return parsed;
    }
    return null;
  } catch {
    return null;
  }
}

/** Streaming buffer: accumulate tokens, extract complete entity markers */
export class EntityMarkerBuffer {
  private buffer: string = '';

  add(token: string): EntityCard[] {
    const entities: EntityCard[] = [];
    this.buffer += token;

    let match;
    ENTITY_MARKER_RE.lastIndex = 0;

    while ((match = ENTITY_MARKER_RE.exec(this.buffer)) !== null) {
      const candidate = match[0];
      const parsed = tryParseEntity(candidate);
      if (parsed) {
        entities.push(parsed);
        this.buffer = this.buffer.slice(0, match.index) + this.buffer.slice(match.index + candidate.length);
        ENTITY_MARKER_RE.lastIndex = 0;
      }
    }

    return entities;
  }

  getBuffer(): string {
    return this.buffer;
  }
}

/** Parse a full message content string into text/comp/entity blocks */
export function parseEntityBlocks(content: string): ContentBlock[] {
  const blocks: ContentBlock[] = [];

  const compRegex = /(^|\n)(#{1,3}\s+Comp:\s*.+?(?=\n#{1,3}\s+Comp:|\n*(?:-{3,}|\*{3,}|$)))/gm;
  let lastIndex = 0;
  let match;

  while ((match = compRegex.exec(content)) !== null) {
    if (match.index > lastIndex) {
      const textBefore = content.slice(lastIndex, match.index);
      parseEntityMarkersInText(textBefore, blocks);
    }
    blocks.push({ kind: 'comp', raw: match[2] });
    lastIndex = match.index + match[0].length;
  }

  if (lastIndex < content.length) {
    parseEntityMarkersInText(content.slice(lastIndex), blocks);
  }

  return blocks;
}

/** Helper: scan text for entity marker patterns and add as blocks */
function parseEntityMarkersInText(text: string, blocks: ContentBlock[]): void {
  const markerRe = /\{"type":\s*"(champion|item|trait|augment)"[^{}]*(?:\{[^{}]*\}[^{}]*)*\}/g;
  let lastEnd = 0;
  let m;

  while ((m = markerRe.exec(text)) !== null) {
    if (m.index > lastEnd) {
      const textPart = text.slice(lastEnd, m.index).trim();
      if (textPart) blocks.push({ kind: 'text', raw: textPart });
    }
    const parsed = tryParseEntity(m[0]);
    if (parsed) {
      blocks.push({ kind: 'entity', raw: m[0], entity: parsed });
    } else {
      blocks.push({ kind: 'text', raw: '`' + m[0] + '`' });
    }
    lastEnd = m.index + m[0].length;
  }

  if (lastEnd < text.length) {
    const remaining = text.slice(lastEnd).trim();
    if (remaining) blocks.push({ kind: 'text', raw: remaining });
  }
}

// ─── Coach Line-of-Play Parser ────────────────────────────────────────────────

import type { LineOfPlay, PivotLine } from '../api/types';

/** Parse coach line-of-play blocks from message content */
export function parseCoachBlocks(content: string): {
  text: string;
  lines: LineOfPlay[];
  pivots: PivotLine[];
} {
  const lines: LineOfPlay[] = [];
  const pivots: PivotLine[] = [];

  // Find all primary/option blocks
  const blockPattern = /(?:^|\n)(PRIMARY|OPTION\s*\d+)[:：]?\s*\n?(.+?)(?=\n(?:PRIMARY|OPTION\s*\d+|PIVOT\s*FALLBACK)|$)/gis;
  let match;
  const matches: Array<{ type: string; content: string }> = [];

  while ((match = blockPattern.exec(content)) !== null) {
    matches.push({
      type: match[1].toUpperCase().trim(),
      content: match[2].trim(),
    });
  }

  // Parse each block
  for (const block of matches) {
    const line: Partial<LineOfPlay> = { name: '' };
    const lines_content = block.content.split('\n');

    for (const line_content of lines_content) {
      const trimmed = line_content.trim();
      if (!trimmed || trimmed.startsWith('--')) continue;

      // Parse key-value pairs
      const econMatch = trimmed.match(/^Econ[s]?[：:]?\s*(.+)/i);
      if (econMatch) { line.econ = econMatch[1].trim(); continue; }

      const itemsMatch = trimmed.match(/^Items?[：:]?\s*(.+)/i);
      if (itemsMatch) {
        line.items = itemsMatch[1].split(/[,，]/).map(s => s.trim()).filter(Boolean);
        continue;
      }

      const timingMatch = trimmed.match(/^Timing[s]?[：:]?\s*(.+)/i);
      if (timingMatch) { line.timing = timingMatch[1].trim(); continue; }

      const riskMatch = trimmed.match(/^Risk[s]?[：:]?\s*(.+)/i);
      if (riskMatch) { line.risk = riskMatch[1].trim(); continue; }

      // First non-empty line without prefix is the name
      if (!line.name && trimmed && !trimmed.includes(':')) {
        line.name = trimmed;
      }
    }

    if (line.name) {
      lines.push(line as LineOfPlay);
    }
  }

  // Parse pivot fallback
  const pivotPattern = /(?:^|\n)PIVOT\s*FALLBACK[:：]?\s*\n?(.+?)(?=\n\n|$)/gis;
  while ((match = pivotPattern.exec(content)) !== null) {
    const pivotContent = match[1].trim();
    const pivotLines = pivotContent.split('\n');

    for (const pl of pivotLines) {
      const trimmed = pl.trim();
      if (!trimmed) continue;

      // Format: "CompName: timing details"
      const pivotMatch = trimmed.match(/^([^:：]+)[:：]\s*(.+)/);
      if (pivotMatch) {
        pivots.push({
          name: pivotMatch[1].trim(),
          timing: pivotMatch[2].trim(),
        });
      }
    }
  }

  // Remove parsed content from remaining text
  const text = content
    .replace(/(?:^|\n)(PRIMARY|OPTION\s*\d+)[:：]?\s*\n?.+?(?=\n(?:PRIMARY|OPTION\s*\d+|PIVOT\s*FALLBACK)|$)/gis, '')
    .replace(/(?:^|\n)PIVOT\s*FALLBACK[:：]?\s*\n?.+?$/gis, '')
    .trim();

  return { text, lines, pivots };
}

/** Check if content contains coach line-of-play markers */
export function hasCoachContent(content: string): boolean {
  return /(?:^|\n)(PRIMARY|OPTION\s*\d+|PIVOT\s*FALLBACK)/im.test(content);
}

