/**
 * Парсер команд терминала.
 * Токенизация + кавычки + флаги + пайпы.
 */

export interface ParsedCommand {
  name: string;
  args: string[];
  flags: Record<string, string | true>;
}

/** Токенизация строки. */
export function tokenize(input: string): string[] {
  const tokens: string[] = [];
  let current = '';
  let inString = false;
  let stringChar = '';
  let escaped = false;

  for (const ch of input) {
    if (escaped) {
      current += ch;
      escaped = false;
      continue;
    }

    if (ch === '\\') {
      escaped = true;
      continue;
    }

    if (inString) {
      if (ch === stringChar) {
        inString = false;
        tokens.push(current);
        current = '';
      } else {
        current += ch;
      }
      continue;
    }

    if (ch === '"' || ch === "'") {
      inString = true;
      stringChar = ch;
      continue;
    }

    if (ch === ' ' || ch === '\t') {
      if (current) {
        tokens.push(current);
        current = '';
      }
      continue;
    }

    if (ch === '|') {
      if (current) {
        tokens.push(current);
        current = '';
      }
      tokens.push('|');
      continue;
    }

    current += ch;
  }

  if (current) tokens.push(current);
  return tokens;
}

/** Разбить на пайпы. */
export function splitPipeline(tokens: string[]): string[][] {
  const pipeline: string[][] = [];
  let current: string[] = [];

  for (const token of tokens) {
    if (token === '|') {
      if (current.length) pipeline.push(current);
      current = [];
    } else {
      current.push(token);
    }
  }

  if (current.length) pipeline.push(current);
  return pipeline;
}

/** Парсинг флагов. */
export function parseFlags(tokens: string[]): Record<string, string | true> {
  const flags: Record<string, string | true> = {};

  for (const token of tokens) {
    const match = token.match(/^--([\w-]+)(?:=(.*))?$/);
    if (match) {
      const key = match[1];
      const value = match[2];
      flags[key] = value !== undefined ? value : true;
    }
  }

  return flags;
}

/** Полный парсинг pipeline. */
export function parse(input: string): ParsedCommand[] {
  const tokens = tokenize(input);
  const segments = splitPipeline(tokens);

  return segments.map((segment) => {
    const name = segment[0] || '';
    const rest = segment.slice(1);
    const args = rest.filter((t) => !t.startsWith('--'));
    const flags = parseFlags(rest);

    return { name, args, flags };
  });
}
