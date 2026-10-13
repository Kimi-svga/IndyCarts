/**
 * Типы контекстов терминала (для cd).
 */

/** Тип контекста. */
export type ContextType =
  | 'root'
  | 'users'
  | 'user'
  | 'cards'
  | 'card'
  | 'market'
  | 'auction'
  | 'pvp'
  | 'clan'
  | 'logs'
  | 'system';

/** Контекст терминала. */
export interface TerminalContext {
  /** Тип. */
  type: ContextType;

  /** ID (для user, card). */
  id?: string | number;

  /** Имя (для clan). */
  name?: string;

  /** Путь для отображения в prompt. */
  path: string;
}

/** Начальный контекст. */
export const ROOT_CONTEXT: TerminalContext = {
  type: 'root',
  path: '~',
};

/** Построить prompt из контекста. */
export function contextToPrompt(ctx: TerminalContext): string {
  switch (ctx.type) {
    case 'root':
      return '~';
    case 'user':
      return `user/${ctx.id}`;
    case 'card':
      return `card/${ctx.id}`;
    case 'clan':
      return `clan/${ctx.name}`;
    default:
      return ctx.type;
  }
  } 
