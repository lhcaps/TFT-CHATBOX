// ─── Types ────────────────────────────────────────────────────────────────────

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
