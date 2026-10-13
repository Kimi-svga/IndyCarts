/**
 * Типы результатов команд.
 */

/** Результат выполнения команды. */
export type CommandResult =
  | { type: 'text'; text: string; className?: string }
  | { type: 'kv'; data: Array<[string, string, string?]> }
  | { type: 'table'; headers: string[]; rows: string[][] }
  | { type: 'json'; data: unknown }
  | { type: 'box'; content: string; variant: 'info' | 'success' | 'error' | 'warn' }
  | { type: 'error'; message: string }
  | { type: 'success'; message: string }
  | { type: 'warn'; message: string }
  | { type: 'raw'; html: string }
  | { type: 'empty' };

/** Помощники для создания результатов. */
export const Result = {
  text: (text: string, className?: string): CommandResult => ({
    type: 'text',
    text,
    className,
  }),

  kv: (data: Array<[string, string, string?]>): CommandResult => ({
    type: 'kv',
    data,
  }),

  table: (headers: string[], rows: string[][]): CommandResult => ({
    type: 'table',
    headers,
    rows,
  }),

  json: (data: unknown): CommandResult => ({
    type: 'json',
    data,
  }),

  box: (
    content: string,
    variant: 'info' | 'success' | 'error' | 'warn' = 'info',
  ): CommandResult => ({
    type: 'box',
    content,
    variant,
  }),

  error: (message: string): CommandResult => ({
    type: 'error',
    message,
  }),

  success: (message: string): CommandResult => ({
    type: 'success',
    message,
  }),

  warn: (message: string): CommandResult => ({
    type: 'warn',
    message,
  }),

  raw: (html: string): CommandResult => ({
    type: 'raw',
    html,
  }),

  empty: (): CommandResult => ({ type: 'empty' }),
};
